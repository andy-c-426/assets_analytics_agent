#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

RELOAD=""
LOG_FILE=""
LOG_PID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reload) RELOAD="--reload" ;;
    --log) LOG_FILE="$ROOT/logs/agent.log" ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
  shift
done

cd "$ROOT/agent-service"

if [ -n "$LOG_FILE" ]; then
  mkdir -p "$ROOT/logs"
  echo "[agent] Starting on http://0.0.0.0:8001 (logging to $LOG_FILE) ..."
  uvicorn agent_service.app.main:app --host 0.0.0.0 $RELOAD --port 8001 >> "$LOG_FILE" 2>&1 &
  LOG_PID=$!
  echo "[agent] PID: $LOG_PID | http://localhost:8001"
else
  echo "[agent] Starting on http://0.0.0.0:8001 ..."
  cleanup() {
    echo ""
    echo "[agent] Shutting down..."
    kill $AGENT_PID 2>/dev/null
    wait $AGENT_PID 2>/dev/null
    echo "[agent] Done."
  }
  trap cleanup EXIT INT TERM
  uvicorn agent_service.app.main:app --host 0.0.0.0 $RELOAD --port 8001 &
  AGENT_PID=$!
  echo "[agent] PID: $AGENT_PID | http://localhost:8001"
  echo "Press Ctrl+C to stop."
  wait
fi
