#!/usr/bin/env bash
# Regenerate backend/requirements.txt with exact pins (run on Linux / VPS / Docker).
set -euo pipefail
cd "$(dirname "$0")/.."

python3.11 -m venv /tmp/rag-lock-venv
source /tmp/rag-lock-venv/bin/activate
pip install -U pip pip-tools

pip-compile requirements.in -o requirements.txt --resolver=backtracking --allow-unsafe

pip install -r requirements.txt
pip freeze | sort > requirements.freeze.txt
echo "Wrote requirements.txt and requirements.freeze.txt"
