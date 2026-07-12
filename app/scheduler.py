"""Hintergrund-Scheduler für den periodischen Cache-Refresh.

Kapselt APScheduler und ruft in festem Intervall ``refresh_all`` auf. Der Job
läuft in einem eigenen Thread mit eigenen DB-Verbindungen (das Repository
öffnet je Aufruf eine Verbindung).
"""

import structlog
from apscheduler.schedulers.background import BackgroundScheduler

from app.services.quote_cache import CachedQuoteService

logger = structlog.get_logger()

_JOB_ID = "refresh_all"


class RefreshScheduler:
    """Startet und stoppt den periodischen Refresh-Job."""

    def __init__(self, service: CachedQuoteService, interval_hours: int) -> None:
        """
        Args:
            service: Dienst mit ``refresh_all()``.
            interval_hours: Intervall zwischen zwei Läufen in Stunden.
        """
        self._service = service
        self._interval_hours = interval_hours
        self._scheduler = BackgroundScheduler()

    def start(self) -> None:
        """Registriert den Job und startet den Scheduler."""
        self._scheduler.add_job(
            self._service.refresh_all,
            trigger="interval",
            hours=self._interval_hours,
            id=_JOB_ID,
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info("scheduler_started", interval_hours=self._interval_hours)

    def shutdown(self) -> None:
        """Stoppt den Scheduler (ohne auf laufende Jobs zu warten)."""
        self._scheduler.shutdown(wait=False)
        logger.info("scheduler_stopped")
