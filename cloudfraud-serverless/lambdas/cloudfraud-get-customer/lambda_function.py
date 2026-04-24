import json
import os
import boto3
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["CUSTOMERS_TABLE"])

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    print("EVENT:", json.dumps(event))

    customer_id = event["pathParameters"]["customerId"]

    response = table.get_item(
        Key={
            "customerId": customer_id
        }
    )

    item = response.get("Item")

    if not item:
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Customer not found"})
        }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(item, default=decimal_default)
    }