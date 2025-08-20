from crewai import Agent
from crewai import LLM
import os

llm = LLM(
    model="gemini/gemini-2.0-flash-lite",
    api_key=os.getenv("GEMINI_API_KEY")
)

job_analyzer_agent = Agent(
    role="Job Description Analyzer",
    goal="Analyze a job description string to extract keywords, responsibilities, and requirements.",
    backstory="""You are a skilled job market analyst. 
    Your task is to parse the provided job description text, 
    identify key keywords (e.g., required skills, tools), 
    list responsibilities, and outline requirements (e.g., experience level, qualifications).""",
    llm=llm,
    verbose=True
)