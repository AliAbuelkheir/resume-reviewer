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
    goal="Read and analyze a resume PDF to generate a concise JSON summary and extract keywords.",
    backstory=(
        "You are an expert HR analyst specializing in resume parsing. "
        "When given a path to a resume PDF in the input variable `resume_filename`, use the provided PDFSearchTool to read the resume content. "
        "DO NOT print or return any tool-invocation templates, debug instructions, or agent tool metadata. "
        "Instead, call the tool programmatically and return a single valid JSON object (no surrounding text) with exactly these keys: "
        "`summary` (a short paragraph), and `keywords` (an array of short keyword strings)."
    ),
    tools=[PDF_tool],
    llm=llm,
    verbose=True
)