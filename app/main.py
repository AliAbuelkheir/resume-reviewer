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
from dotenv import load_dotenv
from app.agents.agent2 import job_analyzer_agent
from app.agents.agent3 import score_generator_agent
from app.tasks.task1 import build_resume_analysis_task
from app.tasks.task2 import job_analysis_task
from app.tasks.task3 import build_ats_score_task
from pydantic import BaseModel

"""Main FastAPI application for the Resume Reviewer System."""

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env (idempotent call)
load_dotenv()

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
KNOWLEDGE_DIR = os.path.normpath(os.path.join("knowledge"))
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

def _wait_for_file(path: str, attempts: int = 5, delay: float = 0.05) -> bool:
    """Poll for file existence & non-zero size to guard against race conditions on some filesystems."""
    import time
    last_size = -1
    for _ in range(attempts):
        if os.path.exists(path):
            size = os.path.getsize(path)
            if size > 0 and size == last_size:  # stable size over two consecutive checks
                return True
            last_size = size
        time.sleep(delay)
    return os.path.exists(path) and os.path.getsize(path) > 0

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
    resume_path = None
    knowledge_path_full = None  # will hold path to copied knowledge file
    knowledge_copied = False    # flag to indicate we created a copy to delete later
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

        # Save file (synchronously, block until done)
        logger.info("💾 Saving file (blocking)...")
        _save_and_sync(resume_file, resume_path)

        if not _wait_for_file(resume_path):
            logger.error("❌ File save verification failed (not found or unstable size)")
            raise HTTPException(status_code=500, detail="File save failed (verification)")
        saved_size = os.path.getsize(resume_path)
        logger.info(f"✅ File saved & verified ({saved_size} bytes)")

        # Prepare knowledge-local copy (workaround for PDFKnowledgeSource prefix behavior)
        knowledge_filename = os.path.basename(resume_path)
        knowledge_path_full = os.path.join(KNOWLEDGE_DIR, knowledge_filename)
        try:
            shutil.copy2(resume_path, knowledge_path_full)
            if not _wait_for_file(knowledge_path_full):
                raise RuntimeError("knowledge copy not stable")
            logger.info(f"📚 Copied resume into knowledge store: {knowledge_path_full}")
            knowledge_copied = True
        except Exception as copy_err:
            logger.warning(f"⚠️ Could not copy file into knowledge directory ({copy_err}), falling back to original path for knowledge source")
            knowledge_filename = os.path.basename(resume_path)

        # We pass only the filename so the knowledge system (which prefixes knowledge/) doesn't duplicate the directory
        knowledge_identifier = knowledge_filename

        # Run CrewAI with fresh agent & task (stateless per request)
        logger.info("🤖 Building fresh resume analyzer agent & task...")
        dynamic_resume_task = build_resume_analysis_task(knowledge_identifier)
        dynamic_resume_agent = getattr(dynamic_resume_task, 'agent', None)
        dynamic_ats_task = build_ats_score_task(dynamic_resume_task)

        agents_list = [dynamic_resume_agent, job_analyzer_agent, score_generator_agent]
        tasks_list = [dynamic_resume_task, job_analysis_task, dynamic_ats_task]

        # Diagnostics: ensure nothing is None
        if any(a is None for a in agents_list):
            nulls = [i for i,a in enumerate(agents_list) if a is None]
            logger.error(f"❌ Agent build failure at indices {nulls}")
            raise HTTPException(status_code=500, detail=f"Internal error: agent build failed (indices {nulls})")
        if any(t is None for t in tasks_list):
            nulls = [i for i,t in enumerate(tasks_list) if t is None]
            logger.error(f"❌ Task build failure at indices {nulls}")
            raise HTTPException(status_code=500, detail=f"Internal error: task build failed (indices {nulls})")

        # Extra: log types for debugging
        logger.info("🧪 Agents types: " + ", ".join(type(a).__name__ for a in agents_list))
        logger.info("🧪 Tasks types: " + ", ".join(type(t).__name__ for t in tasks_list))

        # Build embedder configuration (required for knowledge vectorization)
        google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not google_api_key:
            logger.error("❌ Missing GOOGLE_API_KEY or GEMINI_API_KEY for embedding model")
            raise HTTPException(status_code=500, detail="Server missing Google embedding API key")

        embedder_config = {
            "provider": "google",
            "config": {
                "api_key": google_api_key,
                "model": "text-embedding-004",
            },
        }
        logger.info("🧬 Embedder configured: provider=google model=text-embedding-004")

        crew = Crew(
            agents=agents_list,
            tasks=tasks_list,
            verbose=True,
            embedder=embedder_config,
        )
        result = crew.kickoff(inputs={
            "resume_path": resume_path,
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
            if resume_path and os.path.exists(resume_path):
                os.remove(resume_path)
                logger.info(f"🗑️ Cleaned up file: {resume_path}")
            if knowledge_copied and knowledge_path_full and os.path.exists(knowledge_path_full):
                try:
                    os.remove(knowledge_path_full)
                    logger.info(f"🗑️ Cleaned up knowledge copy: {knowledge_path_full}")
                except Exception as ke:
                    logger.warning(f"⚠️ Failed to remove knowledge copy {knowledge_path_full}: {ke}")
        except Exception as e:
            logger.warning(f"⚠️ Cleanup failed: {e}")

@app.get("/")
async def root():
    logger.info("📍 Root endpoint accessed")
    return {"message": "Welcome to the Resume Reviewer System API"}