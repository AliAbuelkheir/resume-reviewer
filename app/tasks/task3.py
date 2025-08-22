from crewai import Task
from pydantic import BaseModel
from app.agents.agent3 import score_generator_agent
from app.tasks.task1 import resume_analysis_task
from app.tasks.task2 import job_analysis_task

class CVAnalysis(BaseModel):
    ats_score: int
    analysis: str

ats_score_task = Task(
    description="""Use the outputs from the resume analysis and job description analysis. 
    Compute an ATS score out of 100 based on keyword overlap and relevance. 
    Provide a quick analysis of the applicant's fit. If resume analysis is unavailable a score of 0 is expected""",
    expected_output="""ATS Score: [Score]/100
Analysis: [1-2 paragraphs on strengths, gaps, and recommendations]""",
    agent=score_generator_agent,
    context=[resume_analysis_task, job_analysis_task],  # Depends on previous tasks
    output_json=CVAnalysis
)