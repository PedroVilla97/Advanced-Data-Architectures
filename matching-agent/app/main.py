from fastapi import FastAPI
from pydantic import BaseModel
from app.orchestrator import run_matching_flow

app = FastAPI(title="TalentFlow Matching Agent")

class JobPostRequest(BaseModel):
    description: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/match")
async def match_freelancers(payload: JobPostRequest):
    result = await run_matching_flow(payload.description)
    return result