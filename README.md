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
- POST `/run-crew` as multipart/form-data with fields:
  - `job_description` (string)
  - `resume_file` (file) — must be a PDF
  - `resume_filename` (string) — final saved name; will be forced to end with `.pdf`
  - `x-api-key` header — must match `API_KEY` env var

## Response

The `/run-crew` endpoint returns a small JSON object with two primary fields:

- `ats_score` (integer): an ATS-style score in the range 0–100 summarizing how well the resume matches the job description.
- `analysis` (string): a short, human-readable analysis explaining the reasons for the score (strengths, gaps, matched keywords, etc.).

Example successful response (200 OK):

```json
{
  "ats_score": 78,
  "analysis": "Strong experience in the required domain and most requested skills present; missing certification X and few leadership examples."
}
```

## Security and production notes
- This project is intended for demo/non-production use. For production hardening:
  - Use HTTPS and strong API authentication.
  - Add rate-limiting middleware (e.g., `slowapi`).
  - Limit concurrent uploads and scanning jobs.
  - Use deterministic LLM settings (temperature=0) and schema-enforced outputs for reproducible scores.

## Troubleshooting
- If Swagger UI is empty or `/docs` 404s, ensure `app` is imported correctly and Uvicorn is started from the project root with `uvicorn app.main:app`.
- If `/run-crew` returns 401, check the `API_KEY` environment variable.

