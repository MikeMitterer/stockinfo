"""FastAPI-Einstiegspunkt — App-Setup, Lifespan und HTTP-Routen.

Router enthalten nur HTTP-Belange. Fachlogik gehört in die Service-Schicht.
"""

import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import structlog
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.config import Settings, get_settings
from app.docs import register_docs
from app.container import get_cached_quote_service
from app.db import init_db
from app.models import HealthResponse, ReadinessResponse
from app.routers import dashboard, fx, quotes
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


# Default-Docs deaktiviert: /redoc entfällt, /docs kommt als Dark-Variante
# aus app.docs (siehe register_docs weiter unten).
app = FastAPI(
    title="StockInfo",
    version=__version__,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)
register_docs(app)
app.include_router(quotes.router)
app.include_router(dashboard.router)
app.include_router(fx.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness: Antwortet der Prozess überhaupt noch?

    Bewusst billig und ohne Abhängigkeiten — die Antwort entscheidet über einen
    Neustart, und ein Neustart hilft gegen eine kaputte Datenbank nicht.
    Ob der Dienst *arbeiten* kann, beantwortet `/ready`.
    """
    return HealthResponse(version=__version__)


@app.get("/ready", response_model=ReadinessResponse)
async def ready(response: Response) -> ReadinessResponse:
    """Readiness: Kann der Dienst gerade arbeiten?

    `/health` antwortete immer mit ``ok``, auch wenn die SQLite-Datei
    verschwunden oder nicht mehr lesbar war — der Container galt dann bis zum
    ersten echten Request als gesund. Diese Route sieht deshalb wirklich nach:
    ein winziger Zugriff auf die Datenbank, mehr nicht.

    Args:
        response: Wird auf 503 gesetzt, wenn die Datenbank nicht erreichbar ist.

    Returns:
        Zustand samt Version. Der Statuscode ist die eigentliche Aussage —
        503 heißt „gerade nicht bedienbar", nicht „tot".
    """
    try:
        get_cached_quote_service().count_instruments()
    except Exception as exc:
        logger.warning("readiness_check_failed", error=str(exc))
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(status="degraded", version=__version__, database="error")
    return ReadinessResponse(status="ok", version=__version__, database="ok")


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
