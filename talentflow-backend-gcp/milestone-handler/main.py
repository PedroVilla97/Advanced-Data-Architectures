import base64
import json
import os
from typing import Any, Dict

import functions_framework
import requests


REPUTATION_SERVICE_URL = os.getenv("REPUTATION_SERVICE_URL")


def decode_pubsub_event(cloud_event) -> Dict[str, Any]:
    """
    Decode a Pub/Sub CloudEvent into a Python dictionary.

    """

    message = cloud_event.data.get("message", {})
    encoded_data = message.get("data")

    if not encoded_data:
        raise ValueError("Pub/Sub message does not contain data")

    decoded_data = base64.b64decode(encoded_data).decode("utf-8")
    return json.loads(decoded_data)


def release_payment(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulated payment 

    """

    return {
        "status": "payment_released",
        "contract_id": event.get("contract_id"),
        "milestone_id": event.get("milestone_id"),
        "freelancer_id": event.get("freelancer_id"),
        "amount": event.get("amount"),
    }


def update_reputation(freelancer_id: str) -> Dict[str, Any]:
    """
    Calls the reputation-service to update the freelancer's score.
    """

    if not REPUTATION_SERVICE_URL:
        raise RuntimeError("REPUTATION_SERVICE_URL environment variable is missing")

    response = requests.post(
        f"{REPUTATION_SERVICE_URL}/scores/update",
        json={
            "freelancer_id": freelancer_id,
            "delta": 0.1,
        },
        timeout=10,
    )

    response.raise_for_status()
    return response.json()


@functions_framework.cloud_event
def milestone_handler(cloud_event):
    """
    FaaS entry point triggered by Pub/Sub.

    Expected event:
    {
      "event_type": "MilestoneCompleted",
      "contract_id": "c1",
      "milestone_id": "m1",
      "freelancer_id": "f1",
      "amount": 300
    }
    """

    event = decode_pubsub_event(cloud_event)

    if event.get("event_type") != "MilestoneCompleted":
        print(
            json.dumps(
                {
                    "status": "ignored",
                    "reason": "Unsupported event type",
                    "event": event,
                }
            )
        )
        return

    freelancer_id = event.get("freelancer_id")

    if not freelancer_id:
        raise ValueError("MilestoneCompleted event is missing freelancer_id")

    payment_result = release_payment(event)
    reputation_result = update_reputation(freelancer_id)

    print(
        json.dumps(
            {
                "status": "processed",
                "event": event,
                "payment_result": payment_result,
                "reputation_result": reputation_result,
            }
        )
    )
