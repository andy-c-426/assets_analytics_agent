#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

cleanup() {
  echo ""
  echo "Shutting down..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
  echo "Done."
}

trap cleanup EXIT INT TERM

echo "═══════════════════════════════════════════"
echo "  Asset Analytics Agent"
echo "═══════════════════════════════════════════"
echo ""

# Backend
echo "[1/2] Starting backend on http://localhost:8000 ..."
cd "$ROOT"
uvicorn backend.app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Frontend
echo "[2/2] Starting frontend on http://localhost:5173 ..."
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "═══════════════════════════════════════════"
echo "  Frontend : http://localhost:5173"
echo "  API Docs : http://localhost:8000/docs"
echo "  Health   : http://localhost:8000/api/health"
echo "═══════════════════════════════════════════"
echo ""
echo "Press Ctrl+C to stop both servers."
echo ""

wait
