#!/bin/bash
# ArcheCode Startup Script
# Starts both backend and frontend services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "============================================"
echo "  ArcheCode - AI Code Archaeology Platform"
echo "============================================"
echo ""

# Check for .env file
if [ ! -f "$PROJECT_DIR/.env" ]; then
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        echo "[INFO] No .env file found. Copying from .env.example..."
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        echo "[INFO] Please edit .env and add your OPENAI_API_KEY"
    fi
fi

# Source .env if it exists
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

# Start backend
echo "[1/2] Starting backend..."
cd "$PROJECT_DIR/backend"

if [ ! -d "venv" ]; then
    echo "  Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

echo "  Backend starting on http://localhost:8000"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend
echo "[2/2] Starting frontend..."
cd "$PROJECT_DIR/frontend"

if [ ! -d "node_modules" ]; then
    echo "  Installing npm dependencies..."
    npm install
fi

echo "  Frontend starting on http://localhost:3000"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "============================================"
echo "  ArcheCode is running!"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "============================================"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
