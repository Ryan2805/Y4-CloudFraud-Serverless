import json
import os
import uuid
from datetime import datetime, timezone

import boto3

stepfunctions = boto3.client("stepfunctions", region_name=os.getenv("AWS_REGION", "eu-west-1"))


def build_response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }


def lambda_handler(event, context):
    try:
        body = event.get("body")

        if body is None:
            return build_response(400, {"error": "Missing request body"})

        if isinstance(body, str):
            body = json.loads(body)

        required_fields = [
            "customerId",
            "merchantId",
            "amount",
            "currency",
            "country",
            "deviceId",
            "ipAddress"
        ]

        missing_fields = [field for field in required_fields if field not in body]
        if missing_fields:
            return build_response(400, {
                "error": "Missing required fields",
                "missingFields": missing_fields
            })

        transaction_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        workflow_input = {
            "transactionId": transaction_id,
            "createdAt": created_at,
            "customerId": body["customerId"],
            "merchantId": body["merchantId"],
            "amount": body["amount"],
            "currency": body["currency"],
            "country": body["country"],
            "deviceId": body["deviceId"],
            "ipAddress": body["ipAddress"],
            "status": "RECEIVED"
        }

        state_machine_arn = os.getenv("STATE_MACHINE_ARN")

        if not state_machine_arn:
            return build_response(500, {
                "error": "STATE_MACHINE_ARN environment variable not set"
            })

        execution_name = f"txn-{transaction_id}"

        stepfunctions.start_execution(
            stateMachineArn=state_machine_arn,
            name=execution_name,
            input=json.dumps(workflow_input)
        )

        return build_response(202, {
            "message": "Transaction received and workflow started",
            "transactionId": transaction_id,
            "status": "RECEIVED"
        })

    except json.JSONDecodeError:
        return build_response(400, {"error": "Invalid JSON in request body"})

    except Exception as exc:
        return build_response(500, {
            "error": "Internal server error",
            "details": str(exc)
        })
