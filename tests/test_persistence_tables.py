"""Die SQLModel-Modelle bilden das Schema ab — Spalte für Spalte.

Angelegt wird das Schema vom DDL in `app/persistence/`, nicht von den
Modellen. Fehlt einem Modell eine Spalte, käme sie beim Lesen nicht mehr mit;
hat es eine zu viel, bräche das erste `SELECT`. Geprüft wird eine frische
Datenbank und eine aus dem Altformat umgezogene, weil beide Wege das Schema
verschieden erreichen.
"""

import sqlite3
from pathlib import Path

import pytest

from app.persistence.db import init_db, run_migration
from app.persistence.tables import (
    DailyCloseRecord,
    DailyMetaRecord,
    DetailOverrideRecord,
    DetailValueRecord,
    FxRateRecord,
    InstrumentOverrideRecord,
    InstrumentRecord,
    MetaRecord,
    MigrationRejectionRecord,
    QuoteRecord,
)
from tests.legacy_schema import LEGACY_FIRST_SEEN, create_legacy_tables

RECORDS = [
    InstrumentRecord,
    QuoteRecord,
    DailyCloseRecord,
    DetailValueRecord,
    DetailOverrideRecord,
    DailyMetaRecord,
    FxRateRecord,
    MetaRecord,
    InstrumentOverrideRecord,
    MigrationRejectionRecord,
]


def _fresh(tmp_path: Path) -> Path:
    path = tmp_path / "fresh.db"
    init_db(str(path))
    return path


def _migrated(tmp_path: Path) -> Path:
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as connection:
        create_legacy_tables(connection)
        # Ein Symbol ohne Börsenendung wird abgelehnt — erst damit entsteht
        # der Umzugsbericht `migration_rejections`.
        connection.executemany(
            "INSERT INTO instruments (symbol, isin, first_seen) VALUES (?, ?, ?)",
            [("EUNL.DE", "IE00B4L5Y983", LEGACY_FIRST_SEEN), ("XYZ", None, LEGACY_FIRST_SEEN)],
        )
    assert init_db(str(path)), "ohne Ablehnung kein Bericht — falsches Fixture"
    run_migration(str(path), rejected_at=LEGACY_FIRST_SEEN)
    init_db(str(path))
    with sqlite3.connect(path) as connection:
        migrated = connection.execute("SELECT ticker, mic FROM instruments").fetchall()
    assert migrated == [("EUNL", "XETR")], "der Umzug ist nicht gelaufen — falsches Fixture"
    return path


@pytest.mark.parametrize("database", [_fresh, _migrated], ids=["frisch", "umgezogen"])
@pytest.mark.parametrize("record", RECORDS, ids=lambda record: record.__tablename__)
def test_das_modell_traegt_genau_die_spalten_der_tabelle(
    tmp_path: Path, database, record
) -> None:
    if record is MigrationRejectionRecord and database is _fresh:
        pytest.skip("Der Umzugsbericht entsteht erst mit dem ersten Umzug")
    path = database(tmp_path)
    with sqlite3.connect(path) as connection:
        stored = {row[1] for row in connection.execute(f"PRAGMA table_info({record.__tablename__})")}

    assert set(record.model_fields) == stored
