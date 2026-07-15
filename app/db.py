"""SQLite-Anbindung und Schema-Initialisierung.

Kapselt Verbindungsaufbau und Schema. Raw-SQL für Fachlogik gehört in die
Repository-Schicht (repository.py), nicht hierher.
"""

import sqlite3
from pathlib import Path

import structlog

logger = structlog.get_logger()

# Schema — instruments (langsam veränderliche Metadaten) + quotes (Zeitreihe).
_SCHEMA = """
CREATE TABLE IF NOT EXISTS instruments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    isin            TEXT UNIQUE,
    symbol          TEXT NOT NULL,
    exchange        TEXT,
    name            TEXT,
    type            TEXT,
    currency        TEXT,
    provider        TEXT,
    ter             REAL,
    replication     TEXT,
    fund_size       REAL,
    volatility      REAL,
    accumulating    INTEGER,
    first_seen      TEXT NOT NULL,
    meta_fetched_at TEXT
);

CREATE TABLE IF NOT EXISTS quotes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id INTEGER NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    price         REAL NOT NULL,
    quote_time    TEXT NOT NULL,
    volume        INTEGER,
    currency      TEXT,
    fetched_at    TEXT NOT NULL,
    UNIQUE (instrument_id, quote_time)
);

CREATE INDEX IF NOT EXISTS idx_quotes_instrument_time
    ON quotes (instrument_id, quote_time DESC);

CREATE TABLE IF NOT EXISTS daily_closes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id INTEGER NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    date          TEXT NOT NULL,
    close         REAL NOT NULL,
    currency      TEXT,
    UNIQUE (instrument_id, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_instrument_date
    ON daily_closes (instrument_id, date);

CREATE TABLE IF NOT EXISTS daily_meta (
    instrument_id INTEGER PRIMARY KEY REFERENCES instruments(id) ON DELETE CASCADE,
    fetched_from  TEXT,
    fetched_to    TEXT
);
"""


def get_connection(database_path: str) -> sqlite3.Connection:
    """Öffnet eine SQLite-Verbindung und legt das Zielverzeichnis bei Bedarf an.

    Args:
        database_path: Pfad zur SQLite-Datei (z.B. 'data/stockinfo.db').

    Returns:
        Verbindung mit Row-Factory (Zugriff per Spaltenname), aktivierten
        Foreign-Keys und WAL-Modus (Request-Threadpool und Scheduler schreiben
        parallel).
    """
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=10.0, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def init_db(database_path: str) -> None:
    """Erstellt das Datenbankschema, falls es noch nicht existiert.

    Args:
        database_path: Pfad zur SQLite-Datei.
    """
    connection = get_connection(database_path)
    try:
        connection.executescript(_SCHEMA)
        _migrate(connection)
        connection.commit()
    finally:
        connection.close()


def _migrate(connection: sqlite3.Connection) -> None:
    """Ergänzt fehlende Spalten/Indizes in bestehenden Datenbanken (idempotent)."""
    existing = {row["name"] for row in connection.execute("PRAGMA table_info(instruments)")}
    for column, ddl in (("volatility", "REAL"), ("accumulating", "INTEGER")):
        if column not in existing:
            connection.execute(f"ALTER TABLE instruments ADD COLUMN {column} {ddl}")

    # Vor dem UNIQUE-Index Alt-Duplikate zusammenführen — sonst schlägt die
    # Index-Erstellung auf bestehenden Datenbanken fehl.
    _dedupe_symbols(connection)
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_instruments_symbol "
        "ON instruments (symbol)"
    )


def _dedupe_symbols(connection: sqlite3.Connection) -> None:
    """Führt Instrumente mit gleichem Symbol zusammen (Zeile mit ISIN gewinnt).

    Duplikate konnten vor dem UNIQUE-Index durch parallele Erst-Requests
    entstehen. Kurs-Historie und Tages-Schlusskurse werden auf das verbleibende
    Instrument umgehängt; Kollisionen (gleicher Zeitpunkt/Tag) verfallen mit
    dem gelöschten Duplikat.
    """
    duplicated = connection.execute(
        "SELECT symbol FROM instruments GROUP BY symbol HAVING COUNT(*) > 1"
    ).fetchall()
    for row in duplicated:
        symbol = row["symbol"]
        keeper = connection.execute(
            "SELECT id FROM instruments WHERE symbol = ? "
            "ORDER BY (isin IS NULL), id LIMIT 1",
            (symbol,),
        ).fetchone()
        duplicates = connection.execute(
            "SELECT id FROM instruments WHERE symbol = ? AND id != ?",
            (symbol, keeper["id"]),
        ).fetchall()
        for duplicate in duplicates:
            for table in ("quotes", "daily_closes"):
                connection.execute(
                    f"UPDATE OR IGNORE {table} SET instrument_id = ? "
                    "WHERE instrument_id = ?",
                    (keeper["id"], duplicate["id"]),
                )
            connection.execute(
                "DELETE FROM instruments WHERE id = ?", (duplicate["id"],)
            )
        logger.warning(
            "duplicate_symbol_merged", symbol=symbol, kept_id=keeper["id"]
        )
