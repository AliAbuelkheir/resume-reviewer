from crewai import Agent
from crewai_tools import PDFSearchTool
from crewai import LLM
import os

llm = LLM(
    model="gemini/gemini-2.0-flash-lite",
    api_key=os.getenv("GEMINI_API_KEY")
)

tool = PDFSearchTool(
    config=dict(
        llm=dict(
            provider="google",
            config=dict(
                model="gemini/gemini-2.0-flash-lite"
            ),
        ),
        embedder=dict(
            provider="google",
            config=dict(
                model="models/embedding-001",
                task_type="retrieval_document"
            ),
        ),
    )
)

resume_analyzer_agent = Agent(
    role="Resume Analyzer",
    goal="Read and analyze a resume PDF to generate a summary and extract keywords.",
    backstory="""You are an expert HR analyst specializing in resume parsing. 
    Your task is to use the read_pdf tool to extract text from the provided resume file, 
    then create a concise summary of the candidate's experience, education, and skills. 
    Extract key keywords (e.g., skills, technologies, job titles) for ATS comparison.""",
    tools=[tool],
    llm=llm,
    verbose=True
)