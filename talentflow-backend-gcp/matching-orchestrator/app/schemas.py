from typing import List, Optional
from pydantic import BaseModel, Field


class JobSubmissionRequest(BaseModel):
    description: str = Field(..., min_length=10)
    top_k: int = Field(default=3, ge=1, le=10)


class ParsedJob(BaseModel):
    skills: List[str]
    budget: Optional[float] = None
    category: str = "general"


class MatchItem(BaseModel):
    freelancer_id: str
    name: str
    skills: List[str]
    hourly_rate: float
    reputation_score: float
    match_score: float
    matched_skills: List[str]


class JobSubmissionResponse(BaseModel):
    job_id: str
    parsed_job: ParsedJob
    shortlist: List[MatchItem]
