import os
import boto3
from botocore.exceptions import ClientError


dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TRANSACTIONS_TABLE"])


def lambda_handler(event, context):
    transaction_id = event.get("transactionId")
    customer_id = event.get("customerId")
    created_at = event.get("createdAt")

    if not transaction_id:
        raise ValueError("transactionId is required")

    if not customer_id:
        raise ValueError("customerId is required")

    if not created_at:
        raise ValueError("createdAt is required")

    item = {
        "transactionId": transaction_id,
        "customerId": customer_id,
        "merchantId": event.get("merchantId"),
        "amount": event.get("amount"),
        "currency": event.get("currency"),
        "country": event.get("country"),
        "deviceId": event.get("deviceId"),
        "ipAddress": event.get("ipAddress"),
        "createdAt": created_at,
        "decision": event.get("decision", "UNKNOWN"),
        "fraudScore": event.get("fraudScore", 0),
        "riskLevel": event.get("riskLevel", "UNKNOWN"),
        "riskReasons": event.get("riskReasons", []),
        "status": "STORED"
    }

    try:
        table.put_item(Item=item)
    except ClientError as exc:
        raise Exception(f"Failed to store transaction: {str(exc)}")

    return {
        **event,
        "storageStatus": "SUCCESS",
        "status": "STORED"
    }
}