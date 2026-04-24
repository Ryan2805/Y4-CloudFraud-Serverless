import os
import boto3
from botocore.exceptions import ClientError


dynamodb = boto3.resource("dynamodb")
reviews_table = dynamodb.Table(os.environ["REVIEWS_TABLE"])


def lambda_handler(event, context):
    review_id = event.get("reviewId")

    if not review_id:
        raise ValueError("reviewId is required")

    try:
        response = reviews_table.get_item(
            Key={"reviewId": review_id}
        )
    except ClientError as exc:
        raise Exception(f"Failed to read review result: {str(exc)}")

    item = response.get("Item")

    if not item:
        raise ValueError(f"Review not found for reviewId: {review_id}")

    review_status = item.get("reviewStatus", "UNKNOWN")
    review_decision = item.get("reviewDecision", "PENDING")

    return {
        **event,
        "reviewStatus": review_status,
        "reviewDecision": review_decision,
        "status": "REVIEW_RESULT_CHECKED"
    }