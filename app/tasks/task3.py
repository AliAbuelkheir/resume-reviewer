from crewai import Task
from app.agents.agent3 import score_generator_agent
from app.tasks.task2 import job_analysis_task
from app.models import CVAnalysis

ATS_DESCRIPTION = (
    "Use the outputs from the resume analysis (parsed resume JSON) and job description analysis. "
    "Compute an ATS score (0-100) based on overlap of keywords, responsibilities, and requirements. "
    "Rules:\n"
    "- strengths & weaknesses are STRING lists (semicolon or newline separated).\n"
    "- Base scoring primarily on factual overlap but do not expect full accuracy between keywords; do not hallucinate.\n"
    "- Keep summary concise and grounded.\n"
)

EXPECTED_ATS_OUTPUT = "{\"ats_score\": 0-100, \"analysis\": {\"strengths\": \"...\", \"weaknesses\": \"...\", \"summary\": \"...\"} }"

def build_ats_score_task(resume_analysis_task):
    return Task(
        description=ATS_DESCRIPTION,
        expected_output=EXPECTED_ATS_OUTPUT,
        agent=score_generator_agent,
        context=[resume_analysis_task, job_analysis_task],
        output_json=CVAnalysis
    )

# Backwards compatibility variable
ats_score_task = None