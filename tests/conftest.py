"""Isolierte Standarddatenbank und Schutz der Arbeitsdaten beim Testen."""

import os
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit

import pytest

from app.config import get_settings

PROTECTED_DIRECTORIES = (Path(__file__).resolve().parents[1] / "data",)
PROTECTED_DATABASES = (Path(get_settings().database_path).resolve(),)


def _guard_database_access(event: str, arguments: tuple) -> None:
    """Der native Audit-Aufruf liegt vor dem Öffnen, auch bei Connect-Aliasen."""
    if event != "sqlite3.connect":
        return
    database = os.fsdecode(arguments[0])
    if database in ("", ":memory:"):
        return
    if database.startswith("file:"):
        database = unquote(urlsplit(database).path)
    path = Path(database).resolve()
    if any(path == protected.resolve() for protected in PROTECTED_DATABASES) or any(
        path.is_relative_to(directory.resolve()) for directory in PROTECTED_DIRECTORIES
    ):
        raise RuntimeError(f"Test database access blocked: {path}")


# Bereits vor der Test-Collection aktiv; auch importierter Code wird erfasst.
sys.addaudithook(_guard_database_access)


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    from app import container
    from app.sources_registry import close_all

    cached_factories = (
        get_settings,
        container.get_sources_config,
        container.get_cached_quote_service,
        container.get_daily_history_service,
        container.get_quote_analyzer,
        container.get_backup_service,
        container.get_fx_service,
    )

    def clear_caches():
        close_all()
        for factory in cached_factories:
            factory.cache_clear()

    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "stockinfo.db"))
    clear_caches()
    try:
        yield
    finally:
        clear_caches()
