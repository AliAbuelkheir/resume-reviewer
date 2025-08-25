from crewai import Task
from pydantic import BaseModel
from app.agents.agent3 import score_generator_agent
from app.tasks.task1 import resume_analysis_task
from app.tasks.task2 import job_analysis_task
from app.models import CVAnalysis

ats_score_task = Task(
    description=(
        "Use the outputs from the resume analysis and job description analysis. "
        "Compute an ATS score out of 100 based on keyword overlap, responsibilities, and requirements. "
        "Return a single valid JSON object with this shape (note strengths and weaknesses are STRINGs, each a comma or newline separated list):\n"
        "{\n"
        "  \"ats_score\": 75,\n"
        "  \"analysis\": {\n"
        "     \"strengths\": \"Strong Python experience; Good SQL knowledge\",\n"
        "     \"weaknesses\": \"Limited cloud expertise\",\n"
        "     \"summary\": \"Candidate is a good match for data roles requiring Python and SQL, but lacks cloud experience.\"\n"
        "  }\n"
        "}"
    ),
    expected_output="{\"ats_score\": 0-100, \"analysis\": {\"strengths\": \"...\", \"weaknesses\": \"...\", \"summary\": \"...\"} }",
    agent=score_generator_agent,
    context=[resume_analysis_task, job_analysis_task],
    output_json=CVAnalysis
)