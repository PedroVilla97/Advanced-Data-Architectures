from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import FreelancerProfile, ScoreUpdateRequest
from app.store import PROFILES

app = FastAPI(title="TalentFlow Reputation Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "reputation-service"}


@app.get("/profiles")
def list_profiles() -> list[dict]:
    return list(PROFILES.values())


@app.get("/profiles/{freelancer_id}")
def get_profile(freelancer_id: str) -> dict:
    profile = PROFILES.get(freelancer_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@app.post("/profiles")
def create_profile(profile: FreelancerProfile) -> dict:
    if profile.freelancer_id in PROFILES:
        raise HTTPException(status_code=409, detail="Profile already exists")
    PROFILES[profile.freelancer_id] = profile.model_dump()
    return PROFILES[profile.freelancer_id]


@app.post("/scores/update")
def update_score(payload: ScoreUpdateRequest) -> dict:
    profile = PROFILES.get(payload.freelancer_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    updated = max(0.0, min(5.0, profile["reputation_score"] + payload.delta))
    profile["reputation_score"] = round(updated, 2)
    return profile
