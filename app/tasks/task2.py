from crewai import Task
from app.agents.agent2 import job_analyzer_agent
from app.models import JobAnalysis

job_analysis_task = Task(
    description=(
        "Analyze the provided job description: {job_description}. "
        "Return a single valid JSON object with this exact structure:\n"
        "{\n"
        "  \"keywords\": [\"<all relevant skills, tools, technologies, domains, certifications, and methodologies explicitly mentioned in the job description>\"],\n"
        "  \"responsibilities\": [\"<each responsibility/task the candidate will perform>\", ...],\n"
        "  \"requirements\": [\"<each qualification, experience level, degree, certification, or mandatory condition>\", ...]\n"
        "}\n\n"
        "Notes:\n"
        "- Extract ALL relevant keywords, not just technical ones (include tools, methodologies, industries, certifications, soft skills, etc.).\n"
        "- Responsibilities should describe what the candidate will do if hired.\n"
        "- Requirements should describe what the candidate must already have (skills, education, years of experience).\n"
        "- Do not add information that is not explicitly in the job description."
    ),
    expected_output=(
        "{\"keywords\": [\"Java\", \"Spring Boot\", \"AWS\", \"Agile\"], "
        "\"responsibilities\": [\"Design scalable APIs\", \"Collaborate with product team\"], "
        "\"requirements\": [\"5+ years experience\", \"Bachelor’s in Computer Science\"] }"
    ),
    agent=job_analyzer_agent,
    output_json=JobAnalysis
)
