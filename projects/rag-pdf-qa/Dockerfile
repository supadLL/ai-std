FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    QDRANT_LOCAL_PATH=/app/.qdrant \
    DOCUMENT_METADATA_PATH=/app/data/documents.json \
    USER_STORE_PATH=/app/data/users.json \
    INDEX_JOB_STORAGE_PATH=/app/data/index_jobs \
    SOURCE_STORAGE_PATH=/app/data/source_files \
    DATABASE_URL=sqlite:///data/app.db

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-chi-sim \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/data/eval /app/data/index_jobs /app/data/source_files /app/.qdrant

COPY app ./app
COPY web ./web
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations
COPY data/eval/rag_eval_cases.json ./data/eval/rag_eval_cases.json
COPY .env.example ./.env.example

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()"

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
