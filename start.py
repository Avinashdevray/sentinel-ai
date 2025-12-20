#!/usr/bin/env python3
"""
Startup script for FinAgent Sentinel
Runs both the backend API server and the dummy bank app
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def main():
    print("🚀 Starting FinAgent Sentinel...")
    print("=" * 60)
    
    # Get project root
    project_root = Path(__file__).parent
    
    # Start the dummy bank app (simple HTTP server)
    print("\n📱 Starting Dummy Bank App on http://localhost:8001...")
    bank_dir = project_root / "bank_app"
    bank_process = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8001"],
        cwd=bank_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(1)
    print("✅ Bank App running at http://localhost:8001")
    
    # Start the backend API
    print("\n🧠 Starting Backend API on http://localhost:8000...")
    backend_dir = project_root / "backend"
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    
    time.sleep(2)
    print("✅ Backend API running at http://localhost:8000")
    
    print("\n" + "=" * 60)
    print("✅ All services started successfully!")
    print("\nNext steps:")
    print("1. Open a new terminal")
    print("2. Navigate to the frontend directory:")
    print("   cd frontend")
    print("3. Install dependencies (first time only):")
    print("   npm install")
    print("4. Start the frontend:")
    print("   npm run dev")
    print("\n5. Open http://localhost:3000 in your browser")
    print("\nPress Ctrl+C to stop all services")
    print("=" * 60)
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        bank_process.terminate()
        backend_process.terminate()
        print("✅ All services stopped")
        sys.exit(0)

if __name__ == "__main__":
    main()
