def lambda_handler(event, context):
    risk_level = event.get("riskLevel")
    fraud_score = event.get("fraudScore")

    if risk_level is None:
        raise ValueError("riskLevel is required")

    if fraud_score is None:
        raise ValueError("fraudScore is required")

    if risk_level == "LOW":
        decision = "APPROVED"
    elif risk_level == "MEDIUM":
        decision = "FLAGGED"
    elif risk_level == "HIGH":
        decision = "REJECTED"
    else:
        raise ValueError(f"Unknown riskLevel: {risk_level}")

    return {
        **event,
        "decision": decision,
        "status": "DECISION_MADE"
    }