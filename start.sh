#!/bin/bash
set -e

echo "======================================"
echo " Groww AI Fact Engine — Local Startup"
echo "======================================"

# Check required env vars before doing anything
if [ -z "$GOOGLE_API_KEY" ] || [ -z "$GROQ_API_KEY" ]; then
  echo "ERROR: GOOGLE_API_KEY and GROQ_API_KEY must be set in .env"
  exit 1
fi

source venv/bin/activate
export PYTHONPATH=.

# Phase 1: Ingest data
echo ""
echo "[1/4] Running ingestion pipeline..."
python -m phase1_ingestion.run_ingestion
echo "[1/4] Ingestion complete."

# Phase 2: Embed into ChromaDB
echo ""
echo "[2/4] Embedding documents into ChromaDB..."
python -m phase2_rag.ingest
echo "[2/4] Embedding complete."

# Phase 3: Start FastAPI backend in background
echo ""
echo "[3/4] Starting FastAPI backend on port 8080..."
PYTHONPATH=. python -m phase3_api.main &
BACKEND_PID=$!
sleep 3

# Phase 4: Start Next.js frontend in background
echo ""
echo "[4/4] Starting Next.js frontend on port 3000..."
cd frontend && npm run dev &
FRONTEND_PID=$!

echo ""
echo "======================================"
echo " All services running."
echo " Backend:  http://localhost:8080"
echo " Frontend: http://localhost:3000"
echo " Press Ctrl+C to stop all services."
echo "======================================"

cleanup() {
    echo "Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM
wait
