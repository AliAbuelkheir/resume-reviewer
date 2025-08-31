from crewai import Agent, LLM
from app.PDF_RAG import create_pdf_rag_tool
import os
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource


def _build_llm():
    return LLM(
        model="gemini/gemini-2.0-flash-lite",
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0,
        top_p=1,
    )


def build_resume_analyzer_agent(path : str):
    """Factory returning a fresh stateless resume analyzer agent with its own PDF RAG tool."""
    llm = _build_llm()
    pdf_source = PDFKnowledgeSource(
        file_paths=[path]
    )
    return Agent(
        role="Resume Analyzer",
        goal="Parse a SINGLE provided resume PDF into accurate structured JSON strictly from its content.",
        backstory=(
            "You operate in stateless mode: ONLY the current PDF at {resume_path} exists. "
            "No prior resumes, no cached memory, no external documents beyond general language knowledge. "
            "Never fabricate employers, dates, degrees, or skills. If it's not clearly in the PDF, exclude it. "
            "Return ONLY valid JSON. No explanations. No extra keys. "
            "All keywords must appear in the PDF (case-insensitive or trivial morphological variant)."
        ),
        #tools=[create_pdf_rag_tool()],  # new tool per invocation
        llm=llm,
        memory=False,
        verbose=True,
        knowledge_sources=[pdf_source]
    )

# Backwards compatibility global (kept None intentionally to discourage reuse)
resume_analyzer_agent = None