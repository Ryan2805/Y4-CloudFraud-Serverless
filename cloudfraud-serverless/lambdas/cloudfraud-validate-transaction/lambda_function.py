import json


def lambda_handler(event, context):
    required_fields = [
        "transactionId",
        "createdAt",
        "customerId",
        "merchantId",
        "amount",
        "currency",
        "country",
        "deviceId",
        "ipAddress"
    ]

    missing_fields = [field for field in required_fields if field not in event]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    amount = event.get("amount")
    currency = event.get("currency")
    country = event.get("country")
    ip_address = event.get("ipAddress")

    if not isinstance(amount, (int, float)):
        raise ValueError("Amount must be a number")

    if amount <= 0:
        raise ValueError("Amount must be greater than 0")

    if amount > 10000:
        raise ValueError("Amount exceeds maximum allowed validation threshold")

    if not isinstance(currency, str) or len(currency) != 3:
        raise ValueError("Currency must be a 3-letter code")

    if not isinstance(country, str) or len(country) != 2:
        raise ValueError("Country must be a 2-letter code")

    if not isinstance(ip_address, str) or not ip_address.strip():
        raise ValueError("IP address must be provided")

    event["validationStatus"] = "VALID"
    event["validatedAt"] = context.aws_request_id if context else "local-test"

    return {
        "transactionId": event["transactionId"],
        "createdAt": event["createdAt"],
        "customerId": event["customerId"],
        "merchantId": event["merchantId"],
        "amount": event["amount"],
        "currency": event["currency"],
        "country": event["country"],
        "deviceId": event["deviceId"],
        "ipAddress": event["ipAddress"],
        "status": "VALIDATED",
        "validationStatus": event["validationStatus"],
        "validatedAt": event["validatedAt"]
    }
