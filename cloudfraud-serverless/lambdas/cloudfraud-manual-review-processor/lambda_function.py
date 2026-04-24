import os
import json
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


dynamodb = boto3.resource("dynamodb")
reviews_table = dynamodb.Table(os.environ["REVIEWS_TABLE"])


def lambda_handler(event, context):
    processed_records = []

    for record in event.get("Records", []):
        body = json.loads(record["body"])

        review_id = body.get("reviewId")
        fraud_score = body.get("fraudScore", 50)

        if not review_id:
            raise ValueError("reviewId is required")

        if fraud_score >= 60:
            final_review_decision = "REJECTED"
        else:
            final_review_decision = "APPROVED"

        try:
            reviews_table.update_item(
                Key={"reviewId": review_id},
                UpdateExpression="""
                    SET reviewStatus = :status,
                        reviewDecision = :decision,
                        reviewedAt = :reviewedAt
                """,
                ExpressionAttributeValues={
                    ":status": "COMPLETED",
                    ":decision": final_review_decision,
                    ":reviewedAt": datetime.now(timezone.utc).isoformat()
                }
            )
        except ClientError as exc:
            raise Exception(f"Failed to update review record: {str(exc)}")

        processed_records.append({
            "reviewId": review_id,
            "reviewDecision": final_review_decision
        })

    return {
        "processedRecords": processed_records
    }