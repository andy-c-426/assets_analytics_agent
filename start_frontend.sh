#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

PORT="5173"
LOG_FILE=""
LOG_PID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)
      PORT="$2"
      shift ;;
    --log) LOG_FILE="$ROOT/logs/frontend.log" ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
  shift
done

cd "$ROOT/frontend"

if [ -n "$LOG_FILE" ]; then
  mkdir -p "$ROOT/logs"
  echo "[frontend] Starting on http://localhost:$PORT (logging to $LOG_FILE) ..."
  npm run dev -- --port "$PORT" >> "$LOG_FILE" 2>&1 &
  LOG_PID=$!
  echo "[frontend] PID: $LOG_PID | http://localhost:$PORT"
else
  echo "[frontend] Starting on http://localhost:$PORT ..."
  cleanup() {
    echo ""
    echo "[frontend] Shutting down..."
    kill $FRONTEND_PID 2>/dev/null
    wait $FRONTEND_PID 2>/dev/null
    echo "[frontend] Done."
  }
  trap cleanup EXIT INT TERM
  npm run dev -- --port "$PORT" &
  FRONTEND_PID=$!
  echo "[frontend] PID: $FRONTEND_PID | http://localhost:$PORT"
  echo "Press Ctrl+C to stop."
  wait
fi
