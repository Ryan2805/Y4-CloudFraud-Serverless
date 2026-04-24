def lambda_handler(event, context):
    review_status = event.get("reviewStatus")
    review_decision = event.get("reviewDecision")

    if review_status != "COMPLETED":
        return {
            **event,
            "decision": "FLAGGED",
            "finalDecisionSource": "REVIEW_PENDING",
            "status": "REVIEW_STILL_PENDING"
        }

    if review_decision == "APPROVED":
        final_decision = "APPROVED"
    elif review_decision == "REJECTED":
        final_decision = "REJECTED"
    else:
        final_decision = "FLAGGED"

    return {
        **event,
        "decision": final_decision,
        "finalDecisionSource": "MANUAL_REVIEW",
        "status": "REVIEW_DECISION_APPLIED"
    }