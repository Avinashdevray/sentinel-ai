#!/bin/bash

# DummyBank Stop Script
# This script stops all DummyBank services

echo "🛑 Stopping DummyBank Services..."
echo ""

# Function to kill process if running
kill_process() {
    if [ -f "$1" ]; then
        PID=$(cat "$1")
        if ps -p $PID > /dev/null 2>&1; then
            echo "   Stopping process $PID..."
            kill $PID 2>/dev/null
            sleep 1
            # Force kill if still running
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID 2>/dev/null
            fi
            echo "   ✅ Process $PID stopped"
        else
            echo "   ℹ️  Process $PID not running"
        fi
        rm "$1"
    fi
}

# Stop backend
echo "Stopping backend..."
kill_process ".backend.pid"

# Stop frontend
echo "Stopping frontend..."
kill_process ".frontend.pid"

# Kill any remaining processes on ports
echo ""
echo "Checking for remaining processes..."

if lsof -ti:8000 >/dev/null 2>&1; then
    echo "   Killing process on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
fi

if lsof -ti:8501 >/dev/null 2>&1; then
    echo "   Killing process on port 8501..."
    lsof -ti:8501 | xargs kill -9 2>/dev/null
fi

echo ""
echo "✅ All DummyBank services stopped!"
echo ""