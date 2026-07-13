"""FastAPI-Einstiegspunkt — App-Setup, Lifespan und HTTP-Routen.

Router enthalten nur HTTP-Belange. Fachlogik gehört in die Service-Schicht.
"""

import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.config import Settings, get_settings
from app.container import get_cached_quote_service
from app.db import init_db
from app.models import HealthResponse
from app.routers import dashboard, quotes
from app.scheduler import RefreshScheduler

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialisiert DB-Schema und Refresh-Scheduler; stoppt ihn beim Herunterfahren."""
    settings: Settings = get_settings()
    init_db(settings.database_path)

    scheduler = RefreshScheduler(
        get_cached_quote_service(), settings.refresh_interval_hours
    )
    scheduler.start()
    logger.info(
        "app_started", database_path=settings.database_path, version=__version__
    )
    try:
        yield
    finally:
        scheduler.shutdown()
        logger.info("app_stopped")


app = FastAPI(title="StockInfo", version=__version__, lifespan=lifespan)
app.include_router(quotes.router)
app.include_router(dashboard.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liefert den Health-Status des Services (für Docker-Healthcheck & Monitoring)."""
    return HealthResponse(version=__version__)


def mount_dashboard(app: FastAPI, static_dir: str) -> bool:
    """Mountet das gebaute Dashboard als statische Dateien an ``/``.

    Wird als Letztes registriert, damit die API-Routen Vorrang behalten. Fehlt
    das Verzeichnis (z.B. im lokalen Dev ohne Build), wird nichts gemountet.

    Args:
        app: Die FastAPI-Instanz.
        static_dir: Pfad zum Verzeichnis mit dem gebauten Bundle (index.html …).

    Returns:
        ``True`` wenn gemountet, sonst ``False``.
    """
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="dashboard")
        return True
    return False


mount_dashboard(app, get_settings().static_dir)
