#!/bin/bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
rm -rf .venv __pycache__ .pytest_cache tests/__pycache__
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python validate_project.py
python -m pytest tests -q
echo "READY: ./run_project.sh"
