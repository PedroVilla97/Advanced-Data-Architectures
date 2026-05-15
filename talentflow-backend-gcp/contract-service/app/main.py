import json
import os
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.cloud import pubsub_v1


app = FastAPI(title="Contract Service")


# -----------------------------
# Google Cloud Pub/Sub settings
# -----------------------------
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
MILESTONE_TOPIC = os.getenv("MILESTONE_TOPIC", "milestone-completed")


# -----------------------------
# Data models
# -----------------------------
class Milestone(BaseModel):
    milestone_id: str
    title: str
    amount: float
    status: str = "pending"


class ContractCreateRequest(BaseModel):
    contract_id: str
    job_id: str
    freelancer_id: str
    freelancer_name: str
    terms: str
    milestones: List[Milestone]


class MilestoneCompleteRequest(BaseModel):
    contract_id: str
    milestone_id: str


# -----------------------------
# In-memory contract store
# Later this can be replaced by Cloud SQL
# -----------------------------
CONTRACTS = {}


# -----------------------------
# Pub/Sub helper
# -----------------------------
def publish_milestone_completed(event: dict) -> str:
    """
    Publishes a MilestoneCompleted event to Google Cloud Pub/Sub.

    This supports the choreography/event-driven part of the architecture:
    contract-service -> Pub/Sub -> milestone-handler function.
    """

    if not PROJECT_ID:
        raise RuntimeError(
            "GOOGLE_CLOUD_PROJECT environment variable is missing. "
            "Set it when deploying contract-service."
        )

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, MILESTONE_TOPIC)

    data = json.dumps(event).encode("utf-8")

    future = publisher.publish(
        topic_path,
        data,
        event_type="MilestoneCompleted",
    )

    message_id = future.result()
    return message_id


# -----------------------------
# Health endpoint
# -----------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "contract-service",
        "pubsub_topic": MILESTONE_TOPIC,
        "project_id_configured": PROJECT_ID is not None,
    }


# -----------------------------
# Contract endpoints
# -----------------------------
@app.get("/contracts")
def list_contracts():
    return list(CONTRACTS.values())


@app.get("/contracts/{contract_id}")
def get_contract(contract_id: str):
    if contract_id not in CONTRACTS:
        raise HTTPException(status_code=404, detail="Contract not found")

    return CONTRACTS[contract_id]


@app.post("/contracts")
def create_contract(payload: ContractCreateRequest):
    if payload.contract_id in CONTRACTS:
        raise HTTPException(status_code=409, detail="Contract already exists")

    contract = payload.model_dump()
    contract["status"] = "active"

    CONTRACTS[payload.contract_id] = contract

    return contract


# -----------------------------
# Milestone endpoint with Pub/Sub event publishing
# -----------------------------
@app.post("/milestones/complete")
def complete_milestone(payload: MilestoneCompleteRequest):
    if payload.contract_id not in CONTRACTS:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract = CONTRACTS[payload.contract_id]

    completed_milestone = None

    for milestone in contract["milestones"]:
        if milestone["milestone_id"] == payload.milestone_id:
            if milestone["status"] == "completed":
                raise HTTPException(
                    status_code=409,
                    detail="Milestone already completed",
                )

            milestone["status"] = "completed"
            completed_milestone = milestone
            break

    if completed_milestone is None:
        raise HTTPException(status_code=404, detail="Milestone not found")

    all_completed = all(
        milestone["status"] == "completed"
        for milestone in contract["milestones"]
    )

    if all_completed:
        contract["status"] = "completed"

    CONTRACTS[payload.contract_id] = contract

    event = {
        "event_type": "MilestoneCompleted",
        "contract_id": payload.contract_id,
        "milestone_id": payload.milestone_id,
        "freelancer_id": contract["freelancer_id"],
        "freelancer_name": contract["freelancer_name"],
        "amount": completed_milestone["amount"],
    }

    try:
        message_id = publish_milestone_completed(event)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Milestone was completed but Pub/Sub event failed: {str(exc)}",
        )

    return {
        "message": "Milestone completed and event published",
        "contract": contract,
        "pubsub_message_id": message_id,
        "event": event,
    }