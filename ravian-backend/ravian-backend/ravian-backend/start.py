#!/usr/bin/env python3
"""
Startup script for Ravian Backend API
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("Starting Ravian Backend API...", flush=True)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("main.py not found. Please run from project root directory.", flush=True)
        sys.exit(1)
    
    # Install dependencies if needed
    if not Path("venv").exists():
        print("Installing dependencies...", flush=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Run the application (no capture so all logs go to this terminal)
    print("Starting FastAPI server at http://0.0.0.0:8000 (logs below)...", flush=True)
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "main:app", 
        "--reload", 
        "--host", "0.0.0.0", 
        "--port", "8000"
    ])

if __name__ == "__main__":
    main()
