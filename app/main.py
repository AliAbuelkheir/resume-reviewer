from fastapi import HTTPException
import os
import tempfile
from fastapi import FastAPI, File, Form, Header, UploadFile
from crewai import Crew
from app.agents.agent1 import resume_analyzer_agent
from app.agents.agent2 import job_analyzer_agent
from app.agents.agent3 import score_generator_agent
from app.tasks.task1 import resume_analysis_task
from app.tasks.task2 import job_analysis_task
from app.tasks.task3 import ats_score_task
from pydantic import BaseModel

app = FastAPI()

# @app.post("/run-crew")
# async def run_crew(
#     job_description: str = Form(...), 
#     resume_file: UploadFile = File(...), 
#     resume_filename: str = Form(...),
#     x_api_key: str = Header(...)
#     ):

#     if x_api_key != os.getenv("API_KEY"):
#         raise HTTPException(status_code=401, detail="Invalid API Key")
#     # Create a temporary file for the uploaded PDF with the provided filename
#     try:
#         # Use tempfile.NamedTemporaryFile to save the PDF locally
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
#             contents = await resume_file.read()
#             tmp_file.write(contents)
#             temp_resume_path = tmp_file.name

#         # Rename the temporary file to match the provided resume_filename
#         os.replace(temp_resume_path, os.path.join(os.path.dirname(temp_resume_path), resume_filename))

#         # Update the resume_filename to the final path
#         resume_path = os.path.join(os.path.dirname(temp_resume_path), resume_filename)

#         # Set up and run the CrewAI crew
#         crew = Crew(
#             agents=[resume_analyzer_agent, job_analyzer_agent, score_generator_agent],
#             tasks=[resume_analysis_task, job_analysis_task, ats_score_task],
#             # memory=True,
#             verbose=True  # For debugging
#         )
#         result = crew.kickoff(inputs={
#             "resume_filename": resume_path,
#             "job_description": job_description
#         })
        
#         print(resume_path)
#         print(temp_resume_path)
#         return {"result": result.raw}
#     finally:
#         # Delete the temporary PDF file after execution
#         if os.path.exists(resume_path):
#             os.unlink(resume_path)

UPLOAD_DIR = "web/uploads"  # matches your mounts: block in .platform.app.yaml
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/run-crew")
async def run_crew(
    job_description: str = Form(...), 
    resume_file: UploadFile = File(...), 
    resume_filename: str = Form(...),
    x_api_key: str = Header(...)
):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    contents = await resume_file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max 5 MB allowed.")

    # Reset file pointer so we can save it
    resume_file.file.seek(0)

    # Full path where file will be saved
    resume_path = os.path.join(UPLOAD_DIR, resume_filename)

    try:
        # Save uploaded file to uploads folder
        with open(resume_path, "wb") as buffer:
            shutil.copyfileobj(resume_file.file, buffer)

        # Run CrewAI
        crew = Crew(
            agents=[resume_analyzer_agent, job_analyzer_agent, score_generator_agent],
            tasks=[resume_analysis_task, job_analysis_task, ats_score_task],
            verbose=True
        )
        result = crew.kickoff(inputs={
            "resume_filename": resume_path,
            "job_description": job_description
        })

        return {"result": result.raw}

    finally:
        # Clean up: delete uploaded file
        if os.path.exists(resume_path):
            os.remove(resume_path)