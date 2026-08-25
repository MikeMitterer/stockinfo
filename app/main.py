"""FastAPI-Einstiegspunkt — App-Setup, Lifespan und HTTP-Routen.

Router enthalten nur HTTP-Belange. Fachlogik gehört in die Service-Schicht.
"""

import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import structlog
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.config import Settings, get_settings
from app.docs import register_docs
from app.container import get_cached_quote_service
from app.db import init_db
from app.migration_guard import (
    HEALTHCHECK_PATH,
    REASON_MIGRATION_PENDING,
    is_allowed,
    static_allowlist,
)
from app.models import HealthResponse, OperationalResponse, ReadinessResponse
from app.routers import dashboard, fields, fx, migration, quotes
from app.routers.migration import get_gate
from app.scheduler import RefreshScheduler

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialisiert das Schema und — **wenn freigegeben** — den Scheduler.

    Steht ein Identitäts-Umzug aus, wird hier **nichts** migriert und der
    Scheduler **nicht** gestartet. Der Grund ist die Reihenfolge: Dieser Block
    läuft, bevor die App den ersten Request bedient, und ein UI, das erst
    danach erreichbar wird, könnte den Benutzer nicht mehr warnen. Der Dienst
    geht deshalb in den Pending-Zustand und wartet auf die Bestätigung.

    Den Scheduler laufen zu lassen wäre in dieser Lage besonders falsch: Er
    schreibt, ohne dass jemand einen Request gestellt hat — die vorgerechnete
    Auswirkung stimmte bei der Bestätigung dann nicht mehr.
    """
    settings: Settings = get_settings()
    if init_db(settings.database_path):
        get_gate().block()

    laufende: list[RefreshScheduler] = []

    def scheduler_starten() -> None:
        """Startet den Refresh — **einmal**, sobald der Betrieb freigegeben ist.

        Nach einer Bestätigung zur Laufzeit ist der Lifespan längst durch.
        Ohne diesen Weg liefe der Hintergrund-Refresh bis zum nächsten
        Neustart nicht: Der Dienst sähe gesund aus und holte keine Kurse.
        """
        if laufende:
            return
        scheduler = RefreshScheduler(
            get_cached_quote_service(), settings.refresh_interval_hours
        )
        scheduler.start()
        laufende.append(scheduler)
        logger.info("scheduler_started")

    if get_gate().pending:
        get_gate().on_release(scheduler_starten)
    else:
        scheduler_starten()

    logger.info(
        "app_started",
        database_path=settings.database_path,
        version=__version__,
        migration_pending=get_gate().pending,
    )
    try:
        yield
    finally:
        get_gate().on_release(None)
        for scheduler in laufende:
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
app.include_router(fields.router)
app.include_router(migration.router)


@app.middleware("http")
async def migration_guard(request: Request, call_next):
    """Weist im Pending-Zustand alles ab, was nicht auf der Allowlist steht.

    **Zentral und nicht in den Routern.** Einzelprüfungen dort wären eine
    parallele Fachregel, und beim nächsten neuen Endpunkt fehlte eine. Hier
    kommt jeder Request vorbei.

    Die Allowlist wird bei **jedem** Request neu aus dem Verzeichnis
    abgeleitet. Das kostet einen Verzeichnis-Scan, gilt aber nur im
    Pending-Zustand — einem Zustand, der Minuten dauert und in dem der Dienst
    ohnehin nichts anderes tut. Ihn dafür beim Start zwischenzuspeichern hieße,
    eine zweite Wahrheit anzulegen, die bei einem nachgelieferten Build
    driftet.

    Args:
        request: Der eingehende Request.
        call_next: Die nächste Schicht der Middleware-Kette.

    Returns:
        Die Antwort — oder `503` mit stabiler Kennung.
    """
    if not get_gate().pending:
        return await call_next(request)

    static_paths = static_allowlist(get_settings().static_dir)
    if is_allowed(request.method, request.url.path, static_paths):
        return await call_next(request)

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": REASON_MIGRATION_PENDING,
            "migration": "/migration",
        },
    )


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

    Bewusst billig und ohne Abhängigkeiten. Genau deshalb sagt die Antwort
    **nichts** über die Datenbank: Ein Prozess kann laufen und trotzdem nicht
    arbeiten können.

    **Was hier nicht mehr steht.** Der Docstring behauptete, die Antwort
    entscheide über einen Neustart. Nachgemessen stimmt das für dieses
    Deployment nicht — ein `unhealthy`-Container wird von der Docker Engine
    nicht neu gestartet, und `--restart unless-stopped` reagiert auf einen
    beendeten Prozess, nicht auf den Health-Status. Eine
    Orchestrator-Semantik, die es nicht gibt, gehört in keine Zusage.

    Die beiden anderen Fragen: `/operational` — kann der Prozess seine
    derzeitige Aufgabe erfüllen? `/ready` — ist der normale Fachbetrieb
    freigegeben?
    """
    return HealthResponse(version=__version__)


@app.get("/ready", response_model=ReadinessResponse)
async def ready(response: Response) -> ReadinessResponse:
    """Readiness: Kann der Dienst gerade arbeiten?

    `/health` antwortete immer mit ``ok``, auch wenn die SQLite-Datei
    verschwunden oder nicht mehr lesbar war — der Container galt dann bis zum
    ersten echten Request als gesund. Diese Route sieht deshalb wirklich nach:
    ein winziger Zugriff auf die Datenbank, mehr nicht.

    **Zwei Gründe für ein `503`**, seit T-21 Teil 3: die unerreichbare
    Datenbank und der ausstehende Umzug. Beide sind über `status`
    unterscheidbar, und `status` ist ein `Literal` — sonst wäre der neue Wert
    nicht im Vertrag sichtbar.

    Der Pending-Zustand mit `200` zu beantworten wäre eine Lüge an jeden
    Consumer, der Readiness bestimmungsgemäß am Statuscode bewertet: Der Guard
    weist in dieser Lage sämtliche Fachrequests ab. Ob der **Prozess** seine
    derzeitige Aufgabe erfüllt, beantwortet `/operational`.

    Args:
        response: Wird auf 503 gesetzt, wenn der Fachbetrieb nicht freigegeben
            ist.

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

    if get_gate().pending:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(
            status="migration_pending", version=__version__, database="ok"
        )
    return ReadinessResponse(status="ok", version=__version__, database="ok")


@app.get(HEALTHCHECK_PATH, response_model=OperationalResponse)
async def operational(response: Response) -> OperationalResponse:
    """Kann der Prozess seine **derzeitige** Aufgabe erfüllen?

    Die dritte Frage neben `/health` und `/ready`, und die, an der seit T-21
    Teil 3 der Docker-`HEALTHCHECK` hängt. Während eines ausstehenden Umzugs
    ist der Dienst nicht kaputt — er tut genau das, was er tun soll, nämlich
    auf die Bestätigung warten. Ein Healthcheck, der dann `unhealthy` meldete,
    behauptete einen Fehler, wo eine Rückfrage läuft.

    Der Pfad steht als Konstante in `app.migration_guard` und wird von hier,
    vom Guard und von einem Test gegen den Dockerfile gelesen — drei
    Verbraucher, eine Quelle.

    Args:
        response: Wird auf 503 gesetzt, wenn die Datenbank nicht erreichbar ist.

    Returns:
        Der Betriebsmodus samt Version.
    """
    try:
        get_cached_quote_service().count_instruments()
    except Exception as exc:
        logger.warning("operational_check_failed", error=str(exc))
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return OperationalResponse(mode="degraded", version=__version__)

    mode = "migration_pending" if get_gate().pending else "serving"
    return OperationalResponse(mode=mode, version=__version__)


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
