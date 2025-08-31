from crewai import Task
from app.agents.agent1 import build_resume_analyzer_agent
from app.PDF_RAG import create_pdf_rag_tool
from app.models import ResumeAnalysis
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource

TASK_DESCRIPTION = (
    "Read ONLY the resume located at {resume_path}. "
    "You MUST treat this execution as fully isolated: no prior resumes, no cached memory, and no external documents exist. "
    "Analyze the entire document (experience, education, skills, certifications, projects). "
    "Strict Rules:\n"
    "- Only include information explicitly present in the PDF.\n"
    "- Do NOT infer or hallucinate missing dates, employers, degrees, or skills.\n"
    "- Every keyword MUST appear verbatim (case-insensitive) or as a simple stem (e.g., 'analyzing' vs 'analyze').\n"
    "- If uncertain whether a concept is present, exclude it.\n"
    "- No external knowledge injection.\n"
    "Flexibility:\n"
    "- Include ALL relevant keywords: technical, tools, methodologies, domains, soft skills, certifications.\n"
    "- The keyword list length is flexible—prefer completeness over brevity.\n"
    "Quality:\n"
    "- JSON only. No comments, no markdown, no surrounding text.\n"
    "- Preserve meaning; keep summary factual and grounded in text."
)

EXPECTED_OUTPUT = "{\"summary\": \"...\", \"keywords\": [\"Skill1\", \"Skill2\", \"Certification\", \"Tool\"] }"

def build_resume_analysis_task(path : str):
    agent = build_resume_analyzer_agent(path)
    return Task(
        description=TASK_DESCRIPTION,
        expected_output=EXPECTED_OUTPUT,
        agent=agent,
        output_json=ResumeAnalysis
    )

# Backwards compatibility variable (will be rebuilt per request in main)
resume_analysis_task = None