# ── Backend FastAPI ────────────────────────────────
FROM python:3.11-slim AS backend

WORKDIR /app

# System dependencies (for asyncpg and weasyprint)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV PORT=8080

EXPOSE 8080

CMD ["uvicorn", "api_services.main:app", "--host", "0.0.0.0", "--port", "8080"]
