import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Matching Orchestrator")

PARSER_AGENT_URL = os.getenv("PARSER_AGENT_URL", "http://parser-agent:8080")
REPUTATION_SERVICE_URL = os.getenv("REPUTATION_SERVICE_URL", "http://reputation-service:8080")


class MatchRequest(BaseModel):
    description: str
    top_k: int = 3


@app.get("/health")
def health():
    return {"status": "ok", "service": "matching-orchestrator"}


def compute_score(job, freelancer):
    job_skills = set(skill.lower() for skill in job.get("skills", []))
    freelancer_skills = set(skill.lower() for skill in freelancer.get("skills", []))

    overlap = job_skills.intersection(freelancer_skills)
    skill_score = len(overlap) * 25

    budget_score = 0
    if job.get("budget") is None or freelancer["hourly_rate"] <= job["budget"]:
        budget_score = 20

    reputation_score = freelancer["reputation_score"] * 10

    total = skill_score + budget_score + reputation_score

    return {
        "freelancer": freelancer,
        "match_score": round(total, 2),
        "matched_skills": list(overlap)
    }


@app.post("/match")
async def match(payload: MatchRequest):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            parse_response = await client.post(
                f"{PARSER_AGENT_URL}/parse",
                json={"description": payload.description}
            )
            parse_response.raise_for_status()
            parsed_job = parse_response.json()

            profiles_response = await client.get(f"{REPUTATION_SERVICE_URL}/profiles")
            profiles_response.raise_for_status()
            profiles = profiles_response.json()

        ranked = [compute_score(parsed_job, profile) for profile in profiles]
        ranked.sort(key=lambda x: x["match_score"], reverse=True)

        return {
            "parsed_job": parsed_job,
            "shortlist": ranked[:payload.top_k]
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))