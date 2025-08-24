@echo off
echo Starting Resume Reviewer System...

:: Suppress all warnings
call venv\Scripts\activate.bat && python -W ignore::DeprecationWarning -m uvicorn app.main:app --port 8000 --reload
