#!/bin/bash

echo "🚀 Starting Groww Fact Engine..."

# 1. Start the FastAPI backend on port 8080 in the background
echo "📦 Starting FastAPI backend (Port 8080)..."
source venv/bin/activate
PYTHONPATH=. python phase3_api/main.py &
BACKEND_PID=$!

echo "Backend PID: $BACKEND_PID"

# 2. Wait a few seconds for Backend to boot up
sleep 3

# 3. Start the Next.js frontend on port 3000
echo "🖥️ Starting Next.js frontend (Port 3000)..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo "Frontend PID: $FRONTEND_PID"

# Function to handle termination
cleanup() {
    echo "🛑 Stopping services..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit
}

trap cleanup SIGINT SIGTERM

# Wait indefinitely so the script doesn't exit immediately
wait
