# syntax=docker/dockerfile:1
# ─── Stage 1: Dashboard bauen ─────────────────────────────────────────────────
FROM node:22-slim AS dashboard

WORKDIR /dashboard

COPY dashboard/package.json dashboard/package-lock.json ./
# Cache-Mount für den npm-Download-Cache — bleibt über Builds erhalten, auch wenn
# der npm-ci-Layer neu gebaut werden muss (z.B. bei geändertem Lockfile).
RUN --mount=type=cache,target=/root/.npm npm ci

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
# Cache-Mount für den pip-Download-Cache (kein --no-cache-dir — der Mount ersetzt
# ihn: Wheels bleiben über Builds erhalten statt sie ins Image zu schreiben).
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

# pyproject.toml ist die Versions-Quelle — app/__init__.py liest sie zur Laufzeit.
COPY pyproject.toml .
COPY app ./app

# Gebautes Dashboard aus Stage 1 — FastAPI serviert es an / (siehe STATIC_DIR).
COPY --from=dashboard /dashboard/dist ./web

# UTF-8 erzwingen (statt C/ASCII) — explizit für Nicht-Python-Prozesse (Shell,
# git, curl) und locale-unabhängige Zahlenformate. Python 3.12 ist im Container
# ohnehin UTF-8 (PEP 540). Region-Locales wie de_AT.UTF-8 sind im slim-Image NICHT
# generiert und würden auf C zurückfallen — daher C.UTF-8 (immer vorhanden).
# Cache liegt im Volume /data (überlebt Container-Neustarts)
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    DATABASE_PATH=/data/stockinfo.db \
    STATIC_DIR=/app/web
VOLUME ["/data"]
EXPOSE 8000

# Non-root: Die App läuft als 'stockinfo' (UID 99 = Unraid 'nobody', GID 100 =
# 'users'). Der Entrypoint startet als root, übergibt /data an den App-User
# (bestehende root-Volumes bleiben nutzbar) und droppt dann die Privilegien.
RUN useradd --system --uid 99 --gid users --no-create-home stockinfo \
    && mkdir -p /data && chown stockinfo:users /data
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT}/health" || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["sh", "-c", "uvicorn app.main:app --host \"$HOST\" --port \"$PORT\""]
