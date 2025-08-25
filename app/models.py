from pydantic import BaseModel
from typing import List

class ResumeAnalysis(BaseModel):
    summary: str
    keywords: List[str]

class JobAnalysis(BaseModel):
    keywords: List[str]
    responsibilities: List[str]
    requirements: List[str]

class CVAnalysisDetails(BaseModel):
    strengths: str  # newline or comma separated list of strengths
    weaknesses: str  # newline or comma separated list of weaknesses
    summary: str

class CVAnalysis(BaseModel):
    ats_score: int
    analysis: CVAnalysisDetails
