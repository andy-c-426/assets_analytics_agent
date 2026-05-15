#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

RELOAD=""
LOG_FILE=""
LOG_PID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reload) RELOAD="--reload" ;;
    --log) LOG_FILE="$ROOT/logs/backend.log" ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
  shift
done

cd "$ROOT"

if [ -n "$LOG_FILE" ]; then
  mkdir -p "$ROOT/logs"
  echo "[backend] Starting on http://localhost:8000 (logging to $LOG_FILE) ..."
  uvicorn backend.app.main:app $RELOAD --port 8000 >> "$LOG_FILE" 2>&1 &
  LOG_PID=$!
  echo "[backend] PID: $LOG_PID | http://localhost:8000"
else
  echo "[backend] Starting on http://localhost:8000 ..."
  cleanup() {
    echo ""
    echo "[backend] Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    echo "[backend] Done."
  }
  trap cleanup EXIT INT TERM
  uvicorn backend.app.main:app $RELOAD --port 8000 &
  BACKEND_PID=$!
  echo "[backend] PID: $BACKEND_PID | http://localhost:8000"
  echo "Press Ctrl+C to stop."
  wait
fi
