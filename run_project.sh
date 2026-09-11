#!/bin/bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
if [ ! -d ".venv" ]; then echo "Missing .venv. Run ./clean_install.sh first."; exit 1; fi
source .venv/bin/activate
PORT=8501
while lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; do PORT=$((PORT+1)); done
export STREAMLIT_CONFIG_DIR="$ROOT/.streamlit"
python -m streamlit run app.py --server.port "$PORT"
