import shutil
import asyncio
from typing import Optional
from fastapi import HTTPException
import os
import tempfile
from fastapi import FastAPI, File, Form, Header, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from crewai import Crew
from app.agents.agent1 import resume_analyzer_agent
from app.agents.agent2 import job_analyzer_agent
from app.agents.agent3 import score_generator_agent
from app.tasks.task1 import resume_analysis_task
from app.tasks.task2 import job_analysis_task
from app.tasks.task3 import ats_score_task
from pydantic import BaseModel

app = FastAPI(
    title="Resume Reviewer System API",
    description=(
        "API to analyze resumes against a job description and return an ATS-style score. "
        "Upload a PDF resume via the `/run-crew` endpoint."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Minimal, configurable CORS so the Swagger UI can be used from a browser during development.
raw = os.getenv("ALLOWED_ORIGINS")
if raw:
    origins = [o.strip() for o in raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Save uploaded file to uploads folder in a thread so we don't block the event loop.
        # Ensure the file is flushed and synced to disk before proceeding to Crew.
def _save_and_sync(upload_file, dest_path):
    # upload_file.file is a file-like object opened by Starlette's UploadFile
    # copy into dest_path, flush and fsync to ensure write completes.
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        buffer.flush()
        try:
            os.fsync(buffer.fileno())
        except OSError:
            # fsync may not be supported in some environments; ignore if it fails
            pass

UPLOAD_DIR = os.path.normpath(os.path.join("web", "uploads"))  # matches your mounts: block in .platform.app.yaml
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/run-crew")
async def run_crew(
    job_description: str = Form(...), 
    resume_file: UploadFile = File(...), 
    resume_filename: str = Form(...),
    x_api_key: Optional[str] = Header(None)
):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    contents = await resume_file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max 2 MB allowed.")

    # Reset file pointer so we can save it
    resume_file.file.seek(0)

    # Validate that the uploaded file is a PDF
    allowed_types = {"application/pdf", "application/x-pdf"}
    if resume_file.content_type and resume_file.content_type.lower() not in allowed_types:
        raise HTTPException(status_code=415, detail="Only PDF uploads are accepted.")

    # Sanitize filename (prevent directory traversal) and ensure it ends with .pdf
    resume_filename = os.path.basename(resume_filename)
    base, ext = os.path.splitext(resume_filename)
    if ext.lower() != ".pdf":
        resume_filename = f"{base}.pdf"

    # Full path where file will be saved (as PDF) - normalized and absolute to avoid mixed separators
    resume_path = os.path.abspath(os.path.normpath(os.path.join(UPLOAD_DIR, resume_filename)))

    try:
        
        await asyncio.to_thread(_save_and_sync, resume_file, resume_path)

        # Run CrewAI
        crew = Crew(
            agents=[resume_analyzer_agent, job_analyzer_agent, score_generator_agent],
            tasks=[resume_analysis_task, job_analysis_task, ats_score_task],
            verbose=True
        )
        crew.reset_memories(command_type='all')  
        result = crew.kickoff(inputs={
            "resume_filename": resume_path,
            "job_description": job_description
        })

        return result.json_dict

    finally:
        # Clean up: delete uploaded file
        if os.path.exists(resume_path):
            os.remove(resume_path)


@app.get("/")
async def root():
    # Run CrewAI
    crew = Crew(
        agents=[resume_analyzer_agent, job_analyzer_agent, score_generator_agent],
        tasks=[resume_analysis_task, job_analysis_task, ats_score_task],
        verbose=True
    )
    crew.list_models()
    return {"message": "Welcome to the Resume Reviewer System API"}