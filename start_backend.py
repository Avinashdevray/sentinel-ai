#!/usr/bin/env python3
"""
Start script for FinAgent Sentinel with API key
"""
import os
import sys
import subprocess
import time

# Set the API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyCKQQqU7gmhCHKExbmuDODkLXuDABDvPgE"

print("🚀 Starting FinAgent Sentinel with Gemini 2.5 Flash...")
print("=" * 60)

# Start the backend
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
os.chdir(backend_dir)

print("\n🧠 Starting Backend API on http://localhost:8000...")
subprocess.run([
    "bash", "-c",
    "source venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
])
