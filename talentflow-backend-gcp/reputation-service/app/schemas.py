from typing import List
from pydantic import BaseModel, Field


class FreelancerProfile(BaseModel):
    freelancer_id: str
    name: str
    skills: List[str]
    hourly_rate: float = Field(..., ge=0)
    reputation_score: float = Field(..., ge=0, le=5)


class ScoreUpdateRequest(BaseModel):
    freelancer_id: str
    delta: float
