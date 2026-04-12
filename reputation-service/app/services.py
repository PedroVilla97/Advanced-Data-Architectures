from fastapi import HTTPException
from app.models import FreelancerProfile, FreelancerProfileCreate, ScoreUpdateRequest
from app.store import PROFILES


def list_profiles() -> list[FreelancerProfile]:
    return list(PROFILES.values())


def get_profile(freelancer_id: str) -> FreelancerProfile:
    profile = PROFILES.get(freelancer_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Freelancer not found")
    return profile


def create_profile(payload: FreelancerProfileCreate) -> FreelancerProfile:
    if payload.freelancer_id in PROFILES:
        raise HTTPException(status_code=409, detail="Freelancer already exists")
    profile = FreelancerProfile(**payload.model_dump())
    PROFILES[payload.freelancer_id] = profile
    return profile


def update_score(payload: ScoreUpdateRequest) -> FreelancerProfile:
    profile = get_profile(payload.freelancer_id)
    new_score = max(0.0, min(5.0, profile.reputation_score + payload.delta))
    profile.reputation_score = round(new_score, 2)
    if payload.delta > 0:
        profile.completed_projects += 1
    PROFILES[payload.freelancer_id] = profile
    return profile