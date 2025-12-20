@echo off
echo ========================================
echo 🏦 Starting DummyBank Services (Windows)
echo ========================================
echo.

cd /d "%~dp0"

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not found in PATH!
    echo Please install Python 3.8+ and add it to PATH.
    pause
    exit /b
)

REM Create venv if missing
if not exist venv (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate venv
echo 🔧 Activating virtual environment...
call venv\Scripts\activate

REM Install dependencies
echo 📥 Installing backend dependencies...
pip install -q -r backend\requirements.txt

echo 📥 Installing frontend dependencies...
pip install -q -r frontend\requirements.txt

echo.
echo ✅ Dependencies installed!
echo.

REM Start Backend
echo 🚀 Starting FastAPI Backend (Port 8000)...
start "DummyBank Backend" cmd /k "call ..\venv\Scripts\activate && cd backend && python main.py"

echo ⏳ Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

REM Start Frontend
echo 🚀 Starting Streamlit Frontend (Port 8501)...
start "DummyBank Frontend" cmd /k "call ..\venv\Scripts\activate && cd frontend && streamlit run streamlit_app.py --server.port 8501"

echo.
echo ========================================
echo 🎉 Services Launched!
echo.
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:8501
echo.
echo 🛑 Close the opened command windows to stop the servers.
echo ========================================
pause
