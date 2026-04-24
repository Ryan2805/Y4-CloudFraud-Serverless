import os
import json
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")

reviews_table = dynamodb.Table(os.environ["REVIEWS_TABLE"])
queue_url = os.environ["REVIEW_QUEUE_URL"]


def lambda_handler(event, context):
    transaction_id = event.get("transactionId")
    customer_id = event.get("customerId")

    if not transaction_id:
        raise ValueError("transactionId is required")

    if not customer_id:
        raise ValueError("customerId is required")

    review_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    review_item = {
        "reviewId": review_id,
        "transactionId": transaction_id,
        "customerId": customer_id,
        "fraudScore": event.get("fraudScore"),
        "riskLevel": event.get("riskLevel"),
        "riskReasons": event.get("riskReasons", []),
        "reviewStatus": "PENDING",
        "createdAt": created_at
    }

    try:
        reviews_table.put_item(Item=review_item)

        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps({
                "reviewId": review_id,
                "transactionId": transaction_id,
                "customerId": customer_id,
                "fraudScore": event.get("fraudScore"),
                "riskLevel": event.get("riskLevel")
            })
        )

    except ClientError as exc:
        raise Exception(f"Failed to create review task: {str(exc)}")

    return {
        **event,
        "reviewId": review_id,
        "reviewStatus": "PENDING",
        "status": "REVIEW_TASK_CREATED"
    }