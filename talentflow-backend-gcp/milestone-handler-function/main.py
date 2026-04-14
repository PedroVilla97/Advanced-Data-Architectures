import os
import requests
import functions_framework

REPUTATION_SERVICE_URL = os.getenv("REPUTATION_SERVICE_URL", "http://localhost:8002")


@functions_framework.http
def handle_milestone_completion(request):
    data = request.get_json(silent=True) or {}

    required_fields = {"contract_id", "milestone_id", "freelancer_id", "amount"}
    missing = sorted(required_fields - set(data.keys()))
    if missing:
        return {"error": f"Missing fields: {', '.join(missing)}"}, 400

    payment_result = release_payment(data)
    reputation_result = notify_reputation(data["freelancer_id"])

    return {
        "status": "processed",
        "payment": payment_result,
        "reputation": reputation_result,
    }, 200


def release_payment(event: dict) -> dict:
    return {
        "status": "released",
        "contract_id": event["contract_id"],
        "milestone_id": event["milestone_id"],
        "amount": event["amount"],
    }


def notify_reputation(freelancer_id: str) -> dict:
    response = requests.post(
        f"{REPUTATION_SERVICE_URL}/scores/update",
        json={"freelancer_id": freelancer_id, "delta": 0.1},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
