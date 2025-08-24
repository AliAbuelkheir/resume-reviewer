# Resume Reviewer System

A lightweight FastAPI app that analyzes PDF resumes against a job description and returns an ATS-style score using CrewAI agents.

Features
- Single endpoint `/run-crew` accepts a PDF resume and job description and returns a structured result.
- Upload size limit (2 MB by default).
- Enforces PDF uploads and saves files under `web/uploads` temporarily.
- OpenAPI docs available at `/docs` and OpenAPI JSON at `/openapi.json`.
- CORS middleware configured to allow localhost origins by default.

## Quick start (local)
1. Create and activate a Python 3.11+ virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Set environment variables (API keys should NOT be checked into git):

```powershell
set API_KEY=your_api_key_here 
set GEMINI_API_KEY=your_api_key_here
set ALLOWED_ORIGINS=http://localhost:3000
```

3. Run locally with Uvicorn:

```powershell
uvicorn app.main:app --port 8000 --reload
```

4. Open the interactive docs at:

```
http://localhost:8080/docs
```

## Usage
POST `/run-crew` as multipart/form-data with:
  - `job_description` (string, required)
  - `resume_file` (file, required) — must be a PDF (max 2 MB)
Headers:
  - `x-api-key` — must match the `API_KEY` environment variable

Notes:
  - You no longer supply a filename. The server generates a unique, sanitized name using a UUID to avoid collisions (e.g. `resume_3f9c2e4a9b0d4f0d8e6b4e2c1c9d1f3a.pdf`).
  - The uploaded file is stored temporarily under `web/uploads` and deleted after processing completes.
  - Only `application/pdf` (and `application/x-pdf`) content types are accepted.

## Response

The endpoint orchestrates 3 CrewAI tasks and returns structured JSON. Example shape:

```json
{
  "resume_analysis": {
    "summary": "Short paragraph summarizing experience.",
    "keywords": ["Python", "SQL", "ETL"]
  },
  "job_analysis": {
    "keywords": ["Python", "Machine Learning", "Agile"],
    "responsibilities": ["Develop ML models", "Collaborate with data team"],
    "requirements": ["3+ years experience", "Bachelor’s degree in CS"]
  },
  "ats_score": 78,
  "analysis": {
    "strengths": ["Strong Python experience", "Good SQL knowledge"],
    "weaknesses": ["Limited cloud expertise"],
    "summary": "Candidate matches core technical skills but lacks depth in cloud platforms."
  }
}
```

Field meanings:
  - `resume_analysis`: Parsed summary and extracted skills from the resume PDF.
  - `job_analysis`: Parsed key skill, responsibility, and requirement lists from the job description.
  - `ats_score`: Integer 0–100 indicating match quality.
  - `analysis`: Diagnostic breakdown of strengths, weaknesses, and an overall summary.

## Security and production notes
- This project is intended for demo/non-production use. For production hardening:
  - Use HTTPS and strong API authentication.
  - Add rate-limiting middleware (e.g., `slowapi`).
  - Limit concurrent uploads and scanning jobs.
  - Use deterministic LLM settings (temperature=0) and schema-enforced outputs for reproducible scores.

## Troubleshooting
- If Swagger UI is empty or `/docs` 404s, ensure Uvicorn is started from the project root: `uvicorn app.main:app --port 8000` (then visit `http://localhost:8000/docs`).
- If `/run-crew` returns 401, verify the `x-api-key` header matches the `API_KEY` env var.
- If you get 415, confirm the uploaded file is a PDF and the Content-Type is set correctly by the client.
- If you get 413, the file exceeded the 2 MB limit.

