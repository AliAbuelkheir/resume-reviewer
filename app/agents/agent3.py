from crewai import Agent
from crewai import LLM
import os

llm = LLM(
    model="gemini/gemini-2.0-flash-lite",
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)

score_generator_agent = Agent(
    role="ATS Score Generator",
    goal="Compare resume analysis with job description analysis to compute ATS score and structured feedback.",
    backstory=(
        "You are an ATS optimization expert. "
        "You always return valid JSON. "
        "You compare resume keywords with job description keywords/requirements. "
        "You must produce a score out of 100 and a breakdown of strengths, weaknesses, and summary."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False
)