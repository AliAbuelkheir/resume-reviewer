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
    goal="Compare resume analysis with job description to generate an ATS score and applicant analysis.",
    backstory="""You are an ATS optimization expert. 
    Using the resume summary/keywords and job description details, 
    calculate a compatibility score out of 100 based on keyword matches, skill alignment, and relevance. 
    Provide a brief analysis of the applicant's strengths, weaknesses, and fit.""",
    llm=llm,
    verbose=True,
    allow_delegation=False
)