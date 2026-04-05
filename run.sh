#!/bin/bash

# Run script for Vulcan OmniPro 220 Agent

echo "🚀 Starting Vulcan OmniPro 220 Technical Support Agent..."
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Running in fallback mode (no LLM)."
    echo "   Copy .env.example to .env and add your API key for LLM features."
    echo "   cp .env.example .env"
fi

echo "Starting backend server on http://localhost:8000..."
echo "Starting frontend on http://localhost:5173..."
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Run backend and frontend in parallel
(cd backend && python3 main.py) &
BACKEND_PID=$!

# Give backend a moment to start
sleep 5

(cd frontend && npm run dev) &
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
