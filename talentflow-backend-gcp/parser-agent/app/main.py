import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import JobTextRequest, ParseResponse

app = FastAPI(title="TalentFlow Parser Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

KNOWN_SKILLS = [
    "python",
    "fastapi",
    "react",
    "typescript",
    "docker",
    "firebase",
    "sql",
    "gcp",
    "bigquery",
    "firestore",
    "next.js",
    "node.js",
]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "parser-agent"}


@app.post("/parse", response_model=ParseResponse)
def parse_job(payload: JobTextRequest) -> ParseResponse:
    text = payload.description.lower()
    skills = extract_skills_from_text(text)
    budget = extract_budget_from_text(text)
    category = infer_category_from_text(text)
    return ParseResponse(skills=skills, budget=budget, category=category)


@app.post("/extract-skills")
def extract_skills(payload: JobTextRequest) -> dict:
    return {"skills": extract_skills_from_text(payload.description.lower())}


@app.post("/extract-budget")
def extract_budget(payload: JobTextRequest) -> dict:
    return {"budget": extract_budget_from_text(payload.description.lower())}


def extract_skills_from_text(text: str) -> list[str]:
    return [skill for skill in KNOWN_SKILLS if skill in text]


def extract_budget_from_text(text: str):
    matches = re.findall(r"\d+(?:\.\d+)?", text)
    return float(matches[0]) if matches else None


def infer_category_from_text(text: str) -> str:
    if any(word in text for word in ["react", "frontend", "typescript", "next.js"]):
        return "frontend"
    if any(word in text for word in ["python", "sql", "data", "bigquery"]):
        return "data"
    if any(word in text for word in ["gcp", "docker", "cloud", "firestore"]):
        return "cloud"
    return "general"
