import os
import json
import time
from decimal import Decimal

import boto3
import redis
from boto3.dynamodb.conditions import Key
from botocore.config import Config
from botocore.exceptions import ClientError


aws_region = os.environ.get("AWS_REGION", "eu-west-1")

dynamodb_config = Config(
    region_name=aws_region,
    connect_timeout=2,
    read_timeout=2,
    retries={"max_attempts": 1}
)

dynamodb = boto3.resource(
    "dynamodb",
    region_name=aws_region,
    config=dynamodb_config
)

table = dynamodb.Table(os.environ["TRANSACTIONS_TABLE"])
gsi_name = os.environ["TRANSACTIONS_GSI"]

redis_host = os.environ["REDIS_HOST"]
redis_port = int(os.environ.get("REDIS_PORT", "6379"))
cache_ttl = int(os.environ.get("CACHE_TTL_SECONDS", "120"))
redis_ssl = os.environ.get("REDIS_SSL", "true").lower() == "true"

redis_client = redis.Redis(
    host=redis_host,
    port=redis_port,
    ssl=redis_ssl,
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
    retry_on_timeout=False
)


def convert_decimal(value):
    if isinstance(value, list):
        return [convert_decimal(item) for item in value]

    if isinstance(value, dict):
        return {key: convert_decimal(val) for key, val in value.items()}

    if isinstance(value, Decimal):
        if value % 1 == 0:
            return int(value)
        return float(value)

    return value


def lambda_handler(event, context):
    start_time = time.time()
    customer_id = event.get("customerId")

    if not customer_id:
        raise ValueError("customerId is required")

    cache_key = f"customer:recent-transactions:{customer_id}"

    try:
        print("Testing Valkey connection before read...")
        redis_client.ping()
        print("Valkey reachable before read")

        print("Checking recent transactions cache...")
        cached_transactions = redis_client.get(cache_key)
        print("Recent transactions cache check complete")

        if cached_transactions:
            recent_transactions = json.loads(cached_transactions)
            latency_ms = round((time.time() - start_time) * 1000, 2)

            print("Recent transactions cache HIT")

            return {
                **event,
                "recentTransactions": recent_transactions,
                "recentTransactionCount": len(recent_transactions),
                "recentTransactionsCacheStatus": "HIT",
                "recentTransactionsLookupLatencyMs": latency_ms,
                "status": "RECENT_TRANSACTIONS_FETCHED"
            }

        print("Recent transactions cache MISS")

    except Exception as exc:
        print(f"Recent transactions cache read failed, falling back to DynamoDB: {str(exc)}")

    try:
        print("Querying recent transactions from DynamoDB...")
        response = table.query(
            IndexName=gsi_name,
            KeyConditionExpression=Key("customerId").eq(customer_id),
            ScanIndexForward=False,
            Limit=5
        )
        print("DynamoDB recent transactions query complete")
    except ClientError as exc:
        raise Exception(f"Failed to query recent transactions: {str(exc)}")
    except Exception as exc:
        raise Exception(f"DynamoDB connection/query failed: {str(exc)}")

    items = convert_decimal(response.get("Items", []))

    recent_transactions = []
    for item in items:
        recent_transactions.append({
            "transactionId": item.get("transactionId"),
            "customerId": item.get("customerId"),
            "merchantId": item.get("merchantId"),
            "amount": item.get("amount"),
            "currency": item.get("currency"),
            "country": item.get("country"),
            "deviceId": item.get("deviceId"),
            "createdAt": item.get("createdAt"),
            "decision": item.get("decision")
        })

    try:
        print("Testing Valkey connection before write...")
        redis_client.ping()
        print("Valkey reachable before write")

        print("Writing recent transactions to cache...")
        redis_client.setex(
            cache_key,
            cache_ttl,
            json.dumps(recent_transactions)
        )
        print("Recent transactions cache write complete")
    except Exception as exc:
        print(f"Recent transactions cache write failed, continuing without cache: {str(exc)}")

    latency_ms = round((time.time() - start_time) * 1000, 2)

    return {
        **event,
        "recentTransactions": recent_transactions,
        "recentTransactionCount": len(recent_transactions),
        "recentTransactionsCacheStatus": "MISS",
        "recentTransactionsLookupLatencyMs": latency_ms,
        "status": "RECENT_TRANSACTIONS_FETCHED"
    }