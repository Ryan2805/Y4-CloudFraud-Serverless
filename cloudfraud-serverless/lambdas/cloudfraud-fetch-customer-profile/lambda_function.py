import os
import json
import time
from decimal import Decimal

import boto3
import redis
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

table = dynamodb.Table(os.environ["CUSTOMERS_TABLE"])

redis_host = os.environ["REDIS_HOST"]
redis_port = int(os.environ.get("REDIS_PORT", "6379"))
cache_ttl = int(os.environ.get("CACHE_TTL_SECONDS", "300"))
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
        return int(value) if value % 1 == 0 else float(value)
    return value


def lambda_handler(event, context):
    start_time = time.time()
    customer_id = event.get("customerId")

    if not customer_id:
        raise ValueError("customerId is required")

    cache_key = f"customer:profile:{customer_id}"

    try:
        print("Attempting Valkey ping...")
        redis_client.ping()
        print("Valkey reachable")

        print("Checking cache...")
        cached_profile = redis_client.get(cache_key)
        print("Cache check complete")

        if cached_profile:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            print("Cache HIT")
            return {
                **event,
                "customerProfile": json.loads(cached_profile),
                "customerCacheStatus": "HIT",
                "customerLookupLatencyMs": latency_ms,
                "status": "CUSTOMER_PROFILE_FETCHED"
            }

        print("Cache MISS")

    except Exception as exc:
        print(f"Cache read failed, falling back to DynamoDB: {str(exc)}")

    try:
        print("Reading from DynamoDB...")
        response = table.get_item(Key={"customerId": customer_id})
        print("DynamoDB read complete")
    except ClientError as exc:
        raise Exception(f"Failed to read customer profile: {str(exc)}")
    except Exception as exc:
        raise Exception(f"DynamoDB connection/read failed: {str(exc)}")

    item = response.get("Item")

    if not item:
        raise ValueError(f"Customer profile not found for customerId: {customer_id}")

    item = convert_decimal(item)

    profile = {
        "customerId": item["customerId"],
        "baselineRisk": item.get("baselineRisk", 50),
        "accountStatus": item.get("accountStatus", "UNKNOWN"),
        "homeCountry": item.get("homeCountry", "UNKNOWN"),
        "averageTransactionAmount": item.get("averageTransactionAmount", 0),
        "flaggedCount": item.get("flaggedCount", 0)
    }

    try:
        print("Writing to cache...")
        redis_client.setex(cache_key, cache_ttl, json.dumps(profile))
        print("Cache write complete")
    except Exception as exc:
        print(f"Cache write failed, continuing without cache: {str(exc)}")

    latency_ms = round((time.time() - start_time) * 1000, 2)

    return {
        **event,
        "customerProfile": profile,
        "customerCacheStatus": "MISS",
        "customerLookupLatencyMs": latency_ms,
        "status": "CUSTOMER_PROFILE_FETCHED"
    }