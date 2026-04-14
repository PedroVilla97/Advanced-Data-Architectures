import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import MILESTONE_HANDLER_URL, ALLOW_ORIGINS
from app.schemas import ContractCreateRequest, MilestoneCompleteRequest, MilestoneCompletionEvent
from app.store import CONTRACTS

app = FastAPI(title="TalentFlow Contract Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS if ALLOW_ORIGINS != ["*"] else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "contract-service"}


@app.get("/contracts")
def list_contracts() -> list[dict]:
    return list(CONTRACTS.values())


@app.get("/contracts/{contract_id}")
def get_contract(contract_id: str) -> dict:
    contract = CONTRACTS.get(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@app.post("/contracts")
def create_contract(payload: ContractCreateRequest) -> dict:
    if payload.contract_id in CONTRACTS:
        raise HTTPException(status_code=409, detail="Contract already exists")
    contract = payload.model_dump()
    contract["status"] = "active"
    CONTRACTS[payload.contract_id] = contract
    return contract


@app.post("/milestones/complete")
async def complete_milestone(payload: MilestoneCompleteRequest) -> dict:
    contract = CONTRACTS.get(payload.contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    selected = None
    for milestone in contract["milestones"]:
        if milestone["milestone_id"] == payload.milestone_id:
            selected = milestone
            break

    if not selected:
        raise HTTPException(status_code=404, detail="Milestone not found")

    if selected["status"] == "completed":
        raise HTTPException(status_code=409, detail="Milestone already completed")

    selected["status"] = "completed"

    event = MilestoneCompletionEvent(
        contract_id=payload.contract_id,
        milestone_id=payload.milestone_id,
        freelancer_id=contract["freelancer_id"],
        amount=selected["amount"],
    ).model_dump()

    function_result = None
    if MILESTONE_HANDLER_URL:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(MILESTONE_HANDLER_URL, json=event)
                response.raise_for_status()
                function_result = response.json()
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Milestone handler failed: {exc}")

    return {
        "message": "Milestone completed",
        "event": event,
        "function_result": function_result,
    }
