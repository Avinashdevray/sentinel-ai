#!/bin/bash

# DummyBank Startup Script
# This script starts all DummyBank services

echo "🏦 Starting DummyBank Services..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Check if ports are available
if check_port 8000; then
    echo "⚠️  Port 8000 is already in use. Please stop the service using it."
    echo "   Run: lsof -ti:8000 | xargs kill -9"
    exit 1
fi

if check_port 8501; then
    echo "⚠️  Port 8501 is already in use. Please stop the service using it."
    echo "   Run: lsof -ti:8501 | xargs kill -9"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install backend dependencies
echo "📥 Installing backend dependencies..."
cd backend
pip install -q -r requirements.txt
cd ..

# Install frontend dependencies
echo "📥 Installing frontend dependencies..."
cd frontend
pip install -q -r requirements.txt
cd ..

echo ""
echo "✅ Dependencies installed successfully!"
echo ""

# Start backend in background
echo "🚀 Starting FastAPI backend on http://localhost:8000"
cd backend
python main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 3

# Check if backend started successfully
if check_port 8000; then
    echo "✅ Backend started successfully!"
else
    echo "❌ Failed to start backend. Check logs/backend.log for details."
    exit 1
fi

echo ""
echo "🚀 Starting Streamlit frontend on http://localhost:8501"
cd frontend
streamlit run streamlit_app.py > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
sleep 3

# Check if frontend started successfully
if check_port 8501; then
    echo "✅ Frontend started successfully!"
else
    echo "❌ Failed to start frontend. Check logs/frontend.log for details."
    kill $BACKEND_PID
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 DummyBank is now running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Services:"
echo "   • FastAPI Backend:  http://localhost:8000"
echo "   • API Documentation: http://localhost:8000/docs"
echo "   • Streamlit App:    http://localhost:8501"
echo ""
echo "🔑 Demo Credentials:"
echo "   Username: demo"
echo "   Password: demo123"
echo ""
echo "📝 Logs:"
echo "   • Backend:  logs/backend.log"
echo "   • Frontend: logs/frontend.log"
echo ""
echo "🛑 To stop all services, run:"
echo "   ./stop.sh"
echo "   or press Ctrl+C and run: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Save PIDs to file for stop script
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# Keep script running
wait