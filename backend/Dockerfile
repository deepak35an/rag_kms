FROM python:3.11-slim

WORKDIR /app

# System deps for PDF extraction and OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Python deps — exact versions from requirements.txt (includes torch CPU index)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && python -m uvicorn --version \
    && python -c "import fastapi, uvicorn, langchain_community, sentence_transformers, torch, qdrant_client; print('deps OK')"

COPY . .

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 \
    KMP_DUPLICATE_LIB_OK=TRUE \
    ANONYMIZED_TELEMETRY=False

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
