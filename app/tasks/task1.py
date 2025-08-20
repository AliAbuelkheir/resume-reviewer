from crewai import Task
from app.agents.agent1 import resume_analyzer_agent

resume_analysis_task = Task(
    description="""Use the read_pdf tool to read the resume from {resume_filename}. 
    Generate a general summary of the resume and extract keywords (skills, experiences, etc.).""",
    expected_output="""Resume Summary: [A concise paragraph summarizing the resume]
Keywords: [Comma-separated list of keywords, e.g., Python, Machine Learning, 5 years experience]""",
    agent=resume_analyzer_agent
)