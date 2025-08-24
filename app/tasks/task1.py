from crewai import Task
from app.agents.agent1 import resume_analyzer_agent
from app.PDF_RAG import PDF_tool

resume_analysis_task = Task(
    description=(
        "Programmatically use the read_pdf tool to read the resume located at {resume_filename}. "
        "Return exactly one JSON object (no additional text) with the following shape: {\"summary\": <string>, \"keywords\": [<string>, ...] }. "
        "The `summary` should be a concise paragraph. `keywords` should be a short list of skill/technology strings."
    ),
    expected_output=(
        "{\"summary\": \"A short paragraph summarizing experience, education, and notable projects.\", "
        "\"keywords\": [\"Python\", \"SQL\", \"ETL\"] }"
    ),
    agent=resume_analyzer_agent,
    tools=[PDF_tool]
)