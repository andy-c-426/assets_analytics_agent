#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

cleanup() {
  echo ""
  echo "Shutting down..."
  kill $BACKEND_PID $AGENT_PID $FRONTEND_PID 2>/dev/null
  wait $BACKEND_PID $AGENT_PID $FRONTEND_PID 2>/dev/null
  echo "Done."
}

trap cleanup EXIT INT TERM

echo "═══════════════════════════════════════════"
echo "  Asset Analytics Agent"
echo "═══════════════════════════════════════════"
echo ""

# Backend
echo "[1/3] Starting backend on http://localhost:8000 ..."
cd "$ROOT"
uvicorn backend.app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Agent Service
echo "[2/3] Starting agent service on http://localhost:8001 ..."
cd "$ROOT/agent-service"
uvicorn agent_service.app.main:app --host 0.0.0.0 --reload --port 8001 &
AGENT_PID=$!

# Frontend
echo "[3/3] Starting frontend on http://localhost:5173 ..."
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "═══════════════════════════════════════════"
echo "  Frontend    : http://localhost:5173"
echo "  Backend API : http://localhost:8000/docs"
echo "  Agent API   : http://localhost:8001/docs"
echo "  Health      : http://localhost:8000/api/health"
echo "═══════════════════════════════════════════"
echo ""
echo "Use individual scripts to start each service separately:"
echo "  ./start_backend.sh  --reload  [--log]"
echo "  ./start_agent.sh    --reload  [--log]"
echo "  ./start_frontend.sh           [--log]"
echo ""
echo "Press Ctrl+C to stop all servers."
echo ""

wait
