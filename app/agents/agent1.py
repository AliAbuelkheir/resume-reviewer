from crewai import Agent
from crewai import LLM
from app.PDF_RAG import PDF_tool
import os


llm = LLM(
    model="gemini/gemini-2.0-flash-lite",
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0,
    top_p=1,
)

resume_analyzer_agent = Agent(
    role="Resume Analyzer",
    goal="Parse a resume PDF into structured JSON data for downstream analysis.",
    backstory=(
        "You are an expert HR analyst specializing in resume parsing. "
        "You always return clean JSON, never free text. "
        "Use the PDFSearchTool to read the resume content at {resume_path}. "
        "Your job is to summarize the resume and extract keywords of important"
        " skills/experiences in the resume."
    ),
    tools=[PDF_tool],
    llm=llm,
    verbose=True
)