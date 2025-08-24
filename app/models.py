from pydantic import BaseModel
from typing import List

class ResumeAnalysis(BaseModel):
    summary: str
    keywords: List[str]

class JobAnalysis(BaseModel):
    keywords: List[str]
    responsibilities: List[str]
    requirements: List[str]

class CVAnalysis(BaseModel):
    ats_score: int
    analysis: dict  # keys: strengths, weaknesses, summary
