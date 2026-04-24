from datetime import datetime, timezone


def lambda_handler(event, context):
    customer_id = event.get("customerId")
    transaction_id = event.get("transactionId")
    decision = event.get("decision")
    risk_level = event.get("riskLevel")

    if not customer_id:
        raise ValueError("customerId is required")

    if not transaction_id:
        raise ValueError("transactionId is required")

    if not decision:
        raise ValueError("decision is required")

    message = f"Transaction {transaction_id} for customer {customer_id} was {decision} with risk level {risk_level}."

    notification = {
        "notificationType": "TRANSACTION_DECISION",
        "sentAt": datetime.now(timezone.utc).isoformat(),
        "message": message
    }

    return {
        **event,
        "notification": notification,
        "notificationStatus": "SENT",
        "status": "NOTIFIED"
    }
