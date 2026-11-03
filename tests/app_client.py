"""Die App für API-Tests — gecachte Fabriken und Start an einer Stelle.

Die Liste der gecachten Fabriken stand in `conftest.py` und in drei
Testdateien, und die Kopien waren nicht gleich: `test_error_paths` setzte den
Analyse-Dienst nicht zurück. Ein Dienst, der beim Zurücksetzen fehlt, überlebt
den Profilwechsel mit den Quellen des vorigen Tests — und das fällt nur auf,
solange sein Test nicht der erste seiner Art im Lauf ist.

Importiert wird erst beim Aufruf, wie in `conftest.py`: Die App-Module sollen
nicht schon beim Sammeln der Tests geladen werden.
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def service_factories() -> tuple[Callable, ...]:
    """Jeder gecachte Dienst, der Quellen festhält — vollständig, nicht auf Zuruf.

    Returns:
        Die Fabriken mit `cache_clear`.
    """
    from app import container

    return (
        container.get_cached_quote_service,
        container.get_daily_history_service,
        container.get_quote_analyzer,
        container.get_backup_service,
        container.get_fx_service,
    )


def clear_service_caches() -> None:
    """Setzt die Dienste zurück, Einstellungen und Quellenkonfiguration nicht.

    Für Tests, die die Kette gerade neu gebaut haben: Die Dienste halten ihre
    Quellen fest und trügen sonst die alten Anbieter weiter. Der Analyzer
    gehört seit T-46 dazu; er bekommt die Ketten in den Konstruktor.

    **Die Konfiguration steht bewusst nicht dabei.** Sie wird beim
    Profilwechsel einmal neu gelesen, und die Ketten hängen daran über die
    **Identität** des Objekts. Sie danach noch einmal zu verwerfen hieße,
    `/sources` eine dritte Konfiguration unterzuschieben — die Rollen meldeten
    dann „noch nicht gebaut".
    """
    for factory in service_factories():
        factory.cache_clear()


def clear_cached_factories() -> None:
    """Setzt Einstellungen, Quellenkonfiguration und alle Dienste zurück."""
    from app import container
    from app.config import get_settings

    get_settings.cache_clear()
    container.get_sources_config.cache_clear()
    clear_service_caches()


@contextmanager
def app_on_volume(volume: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Die App auf einem Volume — Lifespan inklusive.

    Als Kontextmanager, damit der Lifespan wirklich läuft: Dort werden die
    Plugins geladen. Ohne ihn prüfte der Test eine App, die den Ladevorgang nie
    ausgeführt hat.

    Args:
        volume: Ordner, der die Rolle von `/data` übernimmt.
        monkeypatch: Setzt `DATABASE_PATH` für die Dauer des Tests.

    Yields:
        Der geöffnete Client.
    """
    from app.main import app

    monkeypatch.setenv("DATABASE_PATH", str(volume / "stockinfo.db"))
    clear_cached_factories()
    with TestClient(app) as opened:
        yield opened
    clear_cached_factories()
