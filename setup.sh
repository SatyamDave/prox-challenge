#!/bin/bash

# Setup script for Vulcan OmniPro 220 Agent

echo "🔧 Setting up Vulcan OmniPro 220 Technical Support Agent..."
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

echo "✅ Python and Node.js found"
echo ""

# Setup backend
echo "📦 Installing backend dependencies..."
cd backend
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install backend dependencies"
    exit 1
fi
cd ..
echo "✅ Backend dependencies installed"
echo ""

# Setup frontend
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
if [ $? -ne 0 ]; then
    echo "❌ Failed to install frontend dependencies"
    exit 1
fi
cd ..
echo "✅ Frontend dependencies installed"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your ANTHROPIC_API_KEY"
fi

if [ ! -f "frontend/.env" ]; then
    echo "⚠️  No frontend/.env file found. Creating from template..."
    cp frontend/.env.example frontend/.env
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your ANTHROPIC_API_KEY"
echo "  2. Run ./run.sh to start the agent"
echo ""
