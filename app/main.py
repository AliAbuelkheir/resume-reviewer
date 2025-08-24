import shutil
import asyncio
import logging
import uuid
from typing import Optional
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Add exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error("🚫 Pydantic Validation Error:")
    logger.error(f"📍 URL: {request.url}")
    logger.error(f"📋 Method: {request.method}")
    logger.error(f"📄 Headers: {dict(request.headers)}")
    
    # Log detailed validation errors
    for error in exc.errors():
        logger.error(f"❌ Field: {error['loc']} | Type: {error['type']} | Message: {error['msg']}")
        if 'input' in error:
            logger.error(f"💡 Input received: {error['input']}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "errors": exc.errors(),
            "message": "Check logs for detailed validation errors"
        }
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

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging"""
    logger.info(f"📥 Incoming request: {request.method} {request.url}")
    logger.info(f"📋 Headers: {dict(request.headers)}")
    
    # Log form data for POST requests (be careful with file content)
    if request.method == "POST":
        try:
            content_type = request.headers.get("content-type", "")
            logger.info(f"📄 Content-Type: {content_type}")
            if "multipart/form-data" in content_type:
                logger.info("📎 Multipart form data detected")
        except Exception as e:
            logger.error(f"❌ Error reading request details: {e}")
    
    response = await call_next(request)
    logger.info(f"📤 Response status: {response.status_code}")
    return response

@app.post("/run-crew")
async def run_crew(
    job_description: str = Form(...), 
    resume_file: UploadFile = File(...), 
    x_api_key: Optional[str] = Header(None)
):
    logger.info("🚀 Starting /run-crew endpoint")
    
    try:
        # Log received parameters
        logger.info(f"📝 Job description length: {len(job_description) if job_description else 0} chars")
        logger.info(f" API key provided: {'Yes' if x_api_key else 'No'}")
        
        # Log file details
        if resume_file:
            logger.info(f"📎 File details:")
            logger.info(f"  - Filename: {resume_file.filename}")
            logger.info(f"  - Content-Type: {resume_file.content_type}")
            logger.info(f"  - Size: {resume_file.size if hasattr(resume_file, 'size') else 'Unknown'}")
        else:
            logger.error("❌ No resume file received")
            raise HTTPException(status_code=422, detail="No resume file provided")
        
        # Validate API key
        logger.info("🔐 Validating API key...")
        expected_key = os.getenv("API_KEY")
        if not expected_key:
            logger.error("❌ No API_KEY environment variable set")
            raise HTTPException(status_code=500, detail="Server configuration error")
        
        if x_api_key != expected_key:
            logger.warning("🚫 Invalid API key provided")
            raise HTTPException(status_code=401, detail="Invalid API Key")
        logger.info("✅ API key validated")
        
        # Read and validate file size
        logger.info("📏 Checking file size...")
        contents = await resume_file.read()
        file_size = len(contents)
        logger.info(f"📦 File size: {file_size} bytes ({file_size / 1024:.2f} KB)")
        
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"❌ File too large: {file_size} > {MAX_FILE_SIZE}")
            raise HTTPException(status_code=413, detail="File too large. Max 2 MB allowed.")
        
        if file_size == 0:
            logger.error("❌ Empty file received")
            raise HTTPException(status_code=422, detail="Empty file received")
        
        # Reset file pointer
        resume_file.file.seek(0)
        
        # Validate content type
        logger.info("🔍 Validating content type...")
        allowed_types = {"application/pdf", "application/x-pdf"}
        content_type = resume_file.content_type
        logger.info(f"📄 Received content type: {content_type}")
        
        if not content_type or content_type.lower() not in allowed_types:
            logger.warning(f"❌ Invalid content type: {content_type}")
            raise HTTPException(status_code=415, detail="Only PDF uploads are accepted.")
        logger.info("✅ Content type validated")
        
        # Generate unique, sanitized filename (no longer supplied by client)
        logger.info("🧹 Generating unique filename...")
        original_filename = resume_file.filename or "resume.pdf"
        original_filename = os.path.basename(original_filename)
        base, ext = os.path.splitext(original_filename)
        if ext.lower() != ".pdf":
            ext = ".pdf"
        unique_id = uuid.uuid4().hex
        resume_filename = f"{base[:50]}_{unique_id}{ext}"  # truncate base to avoid overly long names
        logger.info(f"📝 Original: {original_filename} -> Unique: {resume_filename}")
        
        # Create full path
        resume_path = os.path.abspath(os.path.normpath(os.path.join(UPLOAD_DIR, resume_filename)))
        logger.info(f"💾 Save path: {resume_path}")
        
        # Save file
        logger.info("💾 Saving file...")
        await asyncio.to_thread(_save_and_sync, resume_file, resume_path)
        
        if os.path.exists(resume_path):
            saved_size = os.path.getsize(resume_path)
            logger.info(f"✅ File saved successfully ({saved_size} bytes)")
        else:
            logger.error("❌ File save failed - file not found after save")
            raise HTTPException(status_code=500, detail="File save failed")
        
        # Run CrewAI
        logger.info("🤖 Starting CrewAI processing...")
        crew = Crew(
            agents=[resume_analyzer_agent, job_analyzer_agent, score_generator_agent],
            tasks=[resume_analysis_task, job_analysis_task, ats_score_task],
            verbose=True
        )
        crew.reset_memories(command_type='all')
        result = crew.kickoff(inputs={
            "resume_path": resume_path,  # kept for task placeholder compatibility
            "job_description": job_description
        })
        
        logger.info("✅ CrewAI processing completed")
        logger.info(f"📊 Result type: {type(result)}")
        
        return result.json_dict
        
    except HTTPException:
        # Re-raise HTTP exceptions (they're already logged above)
        raise
    except Exception as e:
        logger.error(f"💥 Unexpected error in /run-crew: {str(e)}")
        logger.exception("Full exception details:")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    finally:
        # Clean up
        try:
            if 'resume_path' in locals() and os.path.exists(resume_path):
                os.remove(resume_path)
                logger.info(f"🗑️ Cleaned up file: {resume_path}")
        except Exception as e:
            logger.warning(f"⚠️ Cleanup failed: {e}")

@app.get("/")
async def root():
    logger.info("📍 Root endpoint accessed")
    crew = Crew(
        agents=[resume_analyzer_agent, job_analyzer_agent, score_generator_agent],
        tasks=[resume_analysis_task, job_analysis_task, ats_score_task],
        verbose=True
    )
    crew.list_models()
    return {"message": "Welcome to the Resume Reviewer System API"}