import os
import sys
import subprocess
from pathlib import Path

def run_dev():
    """Run development server with auto-reload"""
    # Get the project root directory
    project_root = Path(__file__).parent
    venv_python = project_root / "venv" / "Scripts" / "python.exe"
    
    if not venv_python.exists():
        print("❌ Virtual environment not found. Please run: python -m venv venv")
        sys.exit(1)
    
    # Set environment variables
    env = os.environ.copy()
    env['PYTHONWARNINGS'] = 'ignore::DeprecationWarning'
    
    # Run uvicorn with the venv python
    cmd = [str(venv_python), "-m", "uvicorn", "app.main:app", "--port", "8000", "--reload"]
    
    print("🚀 Starting Resume Reviewer System...")
    try:
        subprocess.run(cmd, env=env, cwd=project_root)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == "__main__":
    run_dev()