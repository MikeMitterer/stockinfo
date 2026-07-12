"""FastAPI-Einstiegspunkt — App-Setup, Lifespan und HTTP-Routen.

Router enthalten nur HTTP-Belange. Fachlogik gehört in die Service-Schicht.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import structlog
from fastapi import FastAPI

from app import __version__
from app.config import Settings, get_settings
from app.db import init_db
from app.models import HealthResponse
from app.routers import quotes

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialisiert Ressourcen beim Start (DB-Schema) und räumt beim Stopp auf."""
    settings: Settings = get_settings()
    init_db(settings.database_path)
    logger.info(
        "app_started", database_path=settings.database_path, version=__version__
    )
    yield
    logger.info("app_stopped")


app = FastAPI(title="StockInfo", version=__version__, lifespan=lifespan)
app.include_router(quotes.router)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liefert den Health-Status des Services (für Docker-Healthcheck & Monitoring)."""
    return HealthResponse(version=__version__)
