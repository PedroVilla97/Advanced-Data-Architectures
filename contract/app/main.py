from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="TalentFlow Contract Service")

class ContractRequest(BaseModel):
    job_id: str
    freelancer_id: str
    hourly_rate: float
    terms: str

class MilestoneCompleteRequest(BaseModel):
    contract_id: str
    milestone_id: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/contracts")
def create_contract(payload: ContractRequest):
    return {
        "message": "contract created",
        "contract": payload.model_dump()
    }

@app.post("/milestones/complete")
def complete_milestone(payload: MilestoneCompleteRequest):
    return {
        "message": "milestone marked complete, payment release triggered",
        "event": payload.model_dump()
    }