# server/Dockerfile — Langkah 15 (PDF Hal. 29 & 30):
# Container ringan SignBridge FastAPI + Static Web PWA + ONNX Runtime CPU + PostgreSQL Client
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY server/requirements.txt /app/server/requirements.txt
RUN pip install --no-cache-dir -r /app/server/requirements.txt

COPY signbridge /app/signbridge
COPY data /app/data
COPY web /app/web
COPY server /app/server
COPY migrations /app/migrations

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:7860/health || exit 1

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
