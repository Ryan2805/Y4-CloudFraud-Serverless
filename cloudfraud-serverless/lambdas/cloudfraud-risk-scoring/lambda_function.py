def lambda_handler(event, context):
    customer_profile = event.get("customerProfile")
    recent_transactions = event.get("recentTransactions", [])

    if not customer_profile:
        raise ValueError("customerProfile is required")

    amount = event.get("amount")
    country = event.get("country")

    if amount is None:
        raise ValueError("amount is required")

    fraud_score = int(customer_profile.get("baselineRisk", 0))
    risk_reasons = []

    account_status = customer_profile.get("accountStatus")
    home_country = customer_profile.get("homeCountry")
    average_amount = customer_profile.get("averageTransactionAmount", 0)
    flagged_count = customer_profile.get("flaggedCount", 0)

    if account_status == "SUSPENDED":
        fraud_score += 40
        risk_reasons.append("Customer account is suspended")

    if home_country != "UNKNOWN" and country != home_country:
        fraud_score += 20
        risk_reasons.append("Transaction country differs from customer home country")

    if average_amount > 0 and amount > average_amount * 5:
        fraud_score += 35
        risk_reasons.append("Transaction amount is more than 5x customer average")
    elif average_amount > 0 and amount > average_amount * 2:
        fraud_score += 20
        risk_reasons.append("Transaction amount is more than 2x customer average")

    if flagged_count >= 2:
        fraud_score += 15
        risk_reasons.append("Customer has previous flagged transactions")

    if len(recent_transactions) >= 5:
        fraud_score += 15
        risk_reasons.append("High recent transaction volume detected")

    if fraud_score > 100:
        fraud_score = 100

    if fraud_score >= 70:
        risk_level = "HIGH"
    elif fraud_score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        **event,
        "fraudScore": fraud_score,
        "riskLevel": risk_level,
        "riskReasons": risk_reasons,
        "status": "RISK_SCORED"
    }