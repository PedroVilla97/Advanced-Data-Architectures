import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from google.cloud import firestore


app = FastAPI(title="Reputation Service")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
COLLECTION_NAME = os.getenv("FREELANCER_COLLECTION", "freelancer_profiles")

db = firestore.Client(project=PROJECT_ID)
profiles_ref = db.collection(COLLECTION_NAME)


class FreelancerProfile(BaseModel):
    freelancer_id: str
    name: str
    title: Optional[str] = "Freelancer"
    skills: List[str]
    hourly_rate: float = Field(..., ge=0)
    reputation_score: float = Field(..., ge=0, le=5)
    completed_projects: int = 0
    availability: str = "available"


class ScoreUpdateRequest(BaseModel):
    freelancer_id: str
    delta: float


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "reputation-service",
        "store": "firestore",
        "collection": COLLECTION_NAME,
    }


@app.get("/profiles")
def list_profiles():
    docs = profiles_ref.stream()
    return [doc.to_dict() for doc in docs]


@app.get("/profiles/{freelancer_id}")
def get_profile(freelancer_id: str):
    doc = profiles_ref.document(freelancer_id).get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Profile not found")

    return doc.to_dict()


@app.post("/profiles")
def create_profile(profile: FreelancerProfile):
    doc_ref = profiles_ref.document(profile.freelancer_id)
    existing = doc_ref.get()

    if existing.exists:
        raise HTTPException(status_code=409, detail="Profile already exists")

    data = profile.model_dump()
    doc_ref.set(data)

    return data


@app.post("/scores/update")
def update_score(payload: ScoreUpdateRequest):
    doc_ref = profiles_ref.document(payload.freelancer_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile = doc.to_dict()
    current_score = float(profile.get("reputation_score", 3.0))
    current_completed = int(profile.get("completed_projects", 0))

    new_score = max(0.0, min(5.0, current_score + payload.delta))
    profile["reputation_score"] = round(new_score, 2)

    if payload.delta > 0:
        profile["completed_projects"] = current_completed + 1

    doc_ref.set(profile)

    return profile