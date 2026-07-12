FROM python:3.12-slim

# git wird für die justetf-scraping-Abhängigkeit (git+https) gebraucht,
# curl für den Healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Cache liegt im Volume /data (überlebt Container-Neustarts)
ENV HOST=0.0.0.0 \
    PORT=8000 \
    DATABASE_PATH=/data/stockinfo.db
VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT}/health" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host \"$HOST\" --port \"$PORT\""]
