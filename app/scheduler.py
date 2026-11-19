"""Hintergrund-Scheduler für den periodischen Cache-Refresh.

Kapselt APScheduler und ruft in festem Intervall ``refresh_all`` auf. Der Job
läuft in einem eigenen Thread mit eigenen DB-Verbindungen (das Repository
öffnet je Aufruf eine Verbindung).
"""

from datetime import UTC, datetime

import structlog
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.util import undefined

from app.services.quote_cache import CachedQuoteService, RefreshInProgressError

logger = structlog.get_logger()

_JOB_ID = "refresh_all"


class RefreshScheduler:
    """Startet und stoppt den periodischen Refresh-Job."""

    def __init__(
        self, service: CachedQuoteService, interval_minutes: int, run_on_start: bool
    ) -> None:
        """
        Args:
            service: Dienst mit ``refresh_all()``.
            interval_minutes: Intervall zwischen zwei Läufen in Minuten.
            run_on_start: Erster Lauf direkt beim Start statt nach einem Intervall.
        """
        self._service = service
        self._interval_minutes = interval_minutes
        self._run_on_start = run_on_start
        self._scheduler = BackgroundScheduler()

    def start(self) -> None:
        """Registriert den Job und startet den Scheduler."""
        # Ohne next_run_time läuft APScheduler erst nach dem ersten Intervall; None
        # hieße dagegen „pausiert“, darum undefined statt None.
        self._scheduler.add_job(
            self._run_refresh,
            trigger="interval",
            minutes=self._interval_minutes,
            next_run_time=datetime.now(UTC) if self._run_on_start else undefined,
            id=_JOB_ID,
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info(
            "scheduler_started",
            interval_minutes=self._interval_minutes,
            run_on_start=self._run_on_start,
        )

    def _run_refresh(self) -> None:
        """Führt ``refresh_all`` aus; überspringt den Lauf, wenn bereits einer läuft."""
        try:
            self._service.refresh_all()
        except RefreshInProgressError:
            logger.warning("refresh_skipped_already_running")

    def shutdown(self) -> None:
        """Stoppt den Scheduler (ohne auf laufende Jobs zu warten)."""
        self._scheduler.shutdown(wait=False)
        logger.info("scheduler_stopped")
