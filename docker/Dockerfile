# ─── Stage 1: Dashboard bauen ─────────────────────────────────────────────────
FROM node:22-slim AS dashboard

WORKDIR /dashboard

COPY dashboard/package.json dashboard/package-lock.json ./
RUN npm ci

COPY dashboard/ ./

# Leere API-Basis-URL → das Bundle ruft die API relativ auf (same-origin).
ENV VITE_API_BASE_URL=""
RUN npm run build

# ─── Stage 2: Backend + statisches Dashboard ──────────────────────────────────
FROM python:3.12-slim

# git für die justetf-scraping-Abhängigkeit (git+https), curl für den Healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Gebautes Dashboard aus Stage 1 — FastAPI serviert es an / (siehe STATIC_DIR).
COPY --from=dashboard /dashboard/dist ./web

# Cache liegt im Volume /data (überlebt Container-Neustarts)
ENV HOST=0.0.0.0 \
    PORT=8000 \
    DATABASE_PATH=/data/stockinfo.db \
    STATIC_DIR=/app/web
VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT}/health" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host \"$HOST\" --port \"$PORT\""]
