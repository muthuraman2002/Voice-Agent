#!/bin/bash

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Add project root to PYTHONPATH
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

echo "Starting backend with PYTHONPATH=${PYTHONPATH}"
echo "Project root: ${PROJECT_ROOT}"

# Activate virtual environment and start uvicorn
source venv/bin/activate
# Don't use --reload for now to avoid subprocess issues
uvicorn app.main:app --host 0.0.0.0 --port 8000
