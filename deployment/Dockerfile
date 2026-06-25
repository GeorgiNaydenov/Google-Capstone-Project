# Build the clinician-facing application as one Cloud Run artifact.
FROM node:22-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --uid 10001 clinical
COPY --chown=clinical:clinical . ./
COPY --from=frontend-build --chown=clinical:clinical /frontend/dist ./frontend/dist

USER clinical

ENV PORT=8080
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/healthz || exit 1

CMD ["sh", "-c", "uvicorn clinical_app.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
