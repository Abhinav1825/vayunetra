#!/usr/bin/env bash
# VayuNetra — run the WHOLE app locally in ONE terminal (FastAPI + Vite web).
# Usage:  make dev   (or  ./scripts/dev.sh )   ·   Ctrl+C stops both.
# Serves REAL Supabase data by default; use  DEMO_MODE=true make dev  for offline fixtures.
set -euo pipefail
cd "$(dirname "$0")/.."   # repo root

export DEMO_MODE="${DEMO_MODE:-false}"

# --- one-time setup (skipped if already present) ---
if [ ! -x .venv/bin/uvicorn ]; then
  echo "▶ first run: creating Python venv + installing deps..."
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi
if [ ! -d web/node_modules ]; then
  echo "▶ first run: installing web deps..."
  ( cd web && npm install )
fi

# --- start the API in the background ---
echo "▶ API  → http://localhost:8000   (DEMO_MODE=$DEMO_MODE)"
.venv/bin/uvicorn api.main:app --reload --port 8000 &
API_PID=$!

# stop the API whenever this script exits (Ctrl+C, error, or web server quitting)
cleanup() { echo; echo "stopping…"; kill "$API_PID" 2>/dev/null || true; pkill -P "$API_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

# --- start the web dev server in the foreground ---
echo "▶ Web  → http://localhost:5173"
echo "  (open the web URL; Ctrl+C here stops everything)"
cd web && npm run dev
