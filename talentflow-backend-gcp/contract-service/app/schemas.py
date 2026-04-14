from typing import List, Optional
from pydantic import BaseModel, Field


class Milestone(BaseModel):
    milestone_id: str
    title: str
    amount: float = Field(..., ge=0)
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


class MilestoneCompletionEvent(BaseModel):
    contract_id: str
    milestone_id: str
    freelancer_id: str
    amount: float
