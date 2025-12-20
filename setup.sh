#!/bin/bash

echo "🚀 FinAgent Sentinel - Setup Script"
echo "===================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi
echo "✅ Python 3 found: $(python3 --version)"

# Check Node
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi
echo "✅ Node.js found: $(node --version)"

# Setup Backend
echo ""
echo "📦 Setting up Backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

echo "✅ Backend setup complete!"

# Setup Frontend
cd ../frontend
echo ""
echo "📦 Setting up Frontend..."
npm install

echo "✅ Frontend setup complete!"

# Back to root
cd ..

echo ""
echo "===================================="
echo "✅ Setup Complete!"
echo ""
echo "⚠️  IMPORTANT: Configure your API key"
echo "   Edit backend/.env and add your GOOGLE_API_KEY"
echo ""
echo "To start the application:"
echo "   1. Terminal 1: python start.py"
echo "   2. Terminal 2: cd frontend && npm run dev"
echo "   3. Open http://localhost:3000"
echo ""
echo "===================================="
