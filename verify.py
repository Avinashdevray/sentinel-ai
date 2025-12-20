#!/usr/bin/env python3
"""
Verification script for FinAgent Sentinel
Checks that all components are properly set up
"""

import os
import sys
from pathlib import Path

def check_file(path, description):
    """Check if a file exists"""
    if path.exists():
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - NOT FOUND")
        return False

def check_env_var(var_name):
    """Check if environment variable is set"""
    value = os.getenv(var_name)
    if value and value != f"your_{var_name.lower()}_here":
        print(f"✅ {var_name} is configured")
        return True
    else:
        print(f"⚠️  {var_name} is NOT configured (edit backend/.env)")
        return False

def main():
    print("🔍 FinAgent Sentinel - Setup Verification")
    print("=" * 60)
    
    project_root = Path(__file__).parent
    all_good = True
    
    # Check project structure
    print("\n📁 Checking Project Structure...")
    files_to_check = [
        (project_root / "README.md", "README.md"),
        (project_root / "setup.sh", "Setup script"),
        (project_root / "start.py", "Start script"),
        
        # Backend
        (project_root / "backend" / "requirements.txt", "Backend requirements"),
        (project_root / "backend" / ".env", "Environment file"),
        (project_root / "backend" / "app" / "main.py", "Backend main.py"),
        (project_root / "backend" / "app" / "brain.py", "Brain module"),
        (project_root / "backend" / "app" / "agent.py", "Agent module"),
        (project_root / "backend" / "app" / "models.py", "Models module"),
        (project_root / "backend" / "app" / "utils.py", "Utils module"),
        
        # Frontend
        (project_root / "frontend" / "package.json", "Frontend package.json"),
        (project_root / "frontend" / "index.html", "Frontend HTML"),
        (project_root / "frontend" / "src" / "App.jsx", "App component"),
        (project_root / "frontend" / "src" / "components" / "LiveLog.jsx", "LiveLog component"),
        (project_root / "frontend" / "src" / "components" / "SafetyModal.jsx", "SafetyModal component"),
        (project_root / "frontend" / "src" / "hooks" / "useSocket.js", "WebSocket hook"),
        
        # Bank App
        (project_root / "bank_app" / "index.html", "Bank login page"),
        (project_root / "bank_app" / "dashboard.html", "Bank dashboard"),
        (project_root / "bank_app" / "gold.html", "Bank gold page"),
    ]
    
    for file_path, description in files_to_check:
        if not check_file(file_path, description):
            all_good = False
    
    # Check Python dependencies
    print("\n📦 Checking Python Environment...")
    try:
        import fastapi
        print("✅ FastAPI installed")
    except ImportError:
        print("❌ FastAPI not installed (run: pip install -r backend/requirements.txt)")
        all_good = False
    
    try:
        import langchain
        print("✅ LangChain installed")
    except ImportError:
        print("❌ LangChain not installed")
        all_good = False
    
    try:
        import langgraph
        print("✅ LangGraph installed")
    except ImportError:
        print("❌ LangGraph not installed")
        all_good = False
    
    try:
        from playwright.sync_api import sync_playwright
        print("✅ Playwright installed")
    except ImportError:
        print("❌ Playwright not installed")
        all_good = False
    
    # Check environment variables
    print("\n🔑 Checking Environment Configuration...")
    
    # Load .env file
    env_file = project_root / "backend" / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    if not check_env_var("GOOGLE_API_KEY"):
        all_good = False
    
    # Check Node.js dependencies
    print("\n📦 Checking Node.js Environment...")
    node_modules = project_root / "frontend" / "node_modules"
    if node_modules.exists():
        print("✅ Node modules installed")
    else:
        print("⚠️  Node modules not installed (run: cd frontend && npm install)")
        all_good = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_good:
        print("✅ All checks passed! You're ready to go!")
        print("\nNext steps:")
        print("1. Terminal 1: python start.py")
        print("2. Terminal 2: cd frontend && npm run dev")
        print("3. Open http://localhost:3000")
    else:
        print("⚠️  Some checks failed. Please review the issues above.")
        print("\nTo fix:")
        print("1. Run: ./setup.sh")
        print("2. Edit backend/.env and add your GOOGLE_API_KEY")
        print("3. Run this script again: python verify.py")
    print("=" * 60)
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())
