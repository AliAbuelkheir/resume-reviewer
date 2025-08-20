from crewai import Task
from app.agents.agent2 import job_analyzer_agent

job_analysis_task = Task(
    description="""Analyze the job description: {job_description}. 
    Extract keywords, responsibilities, and requirements.""",
    expected_output="""Keywords: [Comma-separated list]
Responsibilities: [Bullet point list]
Requirements: [Bullet point list]""",
    agent=job_analyzer_agent
)