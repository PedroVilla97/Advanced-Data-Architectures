from typing import List, Optional
from pydantic import BaseModel, Field


class JobTextRequest(BaseModel):
    description: str = Field(..., min_length=10)


class ParseResponse(BaseModel):
    skills: List[str]
    budget: Optional[float] = None
    category: str = "general"
