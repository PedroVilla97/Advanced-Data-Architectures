import os
import uuid
from typing import Dict, Any, List

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import PARSER_AGENT_URL, REPUTATION_SERVICE_URL, ALLOW_ORIGINS
from app.schemas import JobSubmissionRequest, JobSubmissionResponse, MatchItem, ParsedJob

app = FastAPI(title="TalentFlow Matching Orchestrator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS if ALLOW_ORIGINS != ["*"] else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

SHORTLISTS: Dict[str, Dict[str, Any]] = {}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "matching-orchestrator"}


@app.post("/jobs", response_model=JobSubmissionResponse)
async def submit_job(payload: JobSubmissionRequest) -> JobSubmissionResponse:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            parser_response = await client.post(
                f"{PARSER_AGENT_URL}/parse",
                json={"description": payload.description},
            )
            parser_response.raise_for_status()
            parsed_job = parser_response.json()

            profiles_response = await client.get(f"{REPUTATION_SERVICE_URL}/profiles")
            profiles_response.raise_for_status()
            profiles = profiles_response.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Dependency error: {exc}")

    shortlist = rank_candidates(parsed_job, profiles, payload.top_k)
    job_id = str(uuid.uuid4())

    SHORTLISTS[job_id] = {
        "job_id": job_id,
        "parsed_job": parsed_job,
        "shortlist": shortlist,
    }

    return JobSubmissionResponse(
        job_id=job_id,
        parsed_job=ParsedJob(**parsed_job),
        shortlist=[MatchItem(**item) for item in shortlist],
    )


@app.get("/shortlists/{job_id}")
def get_shortlist(job_id: str) -> dict:
    result = SHORTLISTS.get(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Shortlist not found")
    return result


def rank_candidates(parsed_job: dict, profiles: List[dict], top_k: int) -> List[dict]:
    ranked = [score_candidate(parsed_job, profile) for profile in profiles]
    ranked.sort(key=lambda item: item["match_score"], reverse=True)
    return ranked[:top_k]


def score_candidate(parsed_job: dict, profile: dict) -> dict:
    job_skills = set(skill.lower() for skill in parsed_job.get("skills", []))
    freelancer_skills = set(skill.lower() for skill in profile.get("skills", []))

    overlap = sorted(job_skills.intersection(freelancer_skills))
    skill_score = len(overlap) * 25.0

    budget = parsed_job.get("budget")
    budget_score = 0.0
    if budget is None or profile["hourly_rate"] <= budget:
        budget_score = 20.0

    reputation_score = float(profile["reputation_score"]) * 10.0
    total = round(skill_score + budget_score + reputation_score, 2)

    return {
        "freelancer_id": profile["freelancer_id"],
        "name": profile["name"],
        "skills": profile["skills"],
        "hourly_rate": profile["hourly_rate"],
        "reputation_score": profile["reputation_score"],
        "match_score": total,
        "matched_skills": overlap,
    }
