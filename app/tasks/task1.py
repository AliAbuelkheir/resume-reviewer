from crewai import Task
from app.agents.agent1 import resume_analyzer_agent
from app.PDF_RAG import PDF_tool
from app.models import ResumeAnalysis

resume_analysis_task = Task(
    description=(
        "Use the PDFSearchTool to read the resume at {resume_path}. "
        "Analyze the entire document including work experience, education, skills, certifications, and projects. "
        "Return a single valid JSON object with this exact structure:\n"
        "{\n"
        "  \"summary\": \"A concise paragraph summarizing the candidate’s background, education, skills, and key achievements.\",\n"
        "  \"keywords\": [\"<list of all relevant skills, tools, technologies, domains, and certifications found in the resume>\"]\n"
        "}\n\n"
        "Notes:\n"
        "- Extract ALL relevant keywords (not just technical ones). Include soft skills, tools, methodologies, industries, and certifications when available.\n"
        "- The number of keywords is flexible: include as many as are relevant.\n"
        "- Do not hallucinate skills that are not in the resume."
    ),
    expected_output="{\"summary\": \"...\", \"keywords\": [\"Skill1\", \"Skill2\", \"Certification\", \"Tool\"] }",
    agent=resume_analyzer_agent,
    tools=[PDF_tool],
    output_json=ResumeAnalysis
)