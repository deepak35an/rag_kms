#!/bin/bash

# Activate virtual environment
. /Users/priyanshu/Desktop/LFT/rag_kms/.venv/bin/activate

# Upgrade Pillow for Python 3.13 compatibility
pip install --upgrade Pillow

# Install requirements
pip install -r requirements.txt

# Start the backend server
echo "✅ Starting RAG backend on http://localhost:8000"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
