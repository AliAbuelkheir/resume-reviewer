from crewai import Agent
from crewai import LLM
import os

llm = LLM(
    model="gemini/gemini-2.0-flash-lite",
    api_key=os.getenv("GEMINI_API_KEY")
)

job_analyzer_agent = Agent(
    role="Job Description Analyzer",
    goal="Parse job descriptions into structured JSON for matching.",
    backstory=(
        "You are a skilled job market analyst. "
        "You always return valid JSON. "
        "Your job is to extract keywords, responsibilities, and requirements."
    ),
    llm=llm,
    verbose=True
)