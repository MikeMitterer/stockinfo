"""SQLite-Repository — kapselt allen Datenbankzugriff.

Kein Raw-SQL außerhalb dieser Schicht. Jede Methode nutzt eine eigene, kurz
gehaltene Verbindung — so ist der Zugriff thread-safe (Request-Threadpool und
Hintergrund-Scheduler teilen sich keine Connection).
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app.db import get_connection
from app.models import QuoteResponse

# Instrument-Metadatenfelder (ohne id/isin/symbol/first_seen).
_META_FIELDS = (
    "exchange",
    "name",
    "type",
    "currency",
    "provider",
    "ter",
    "replication",
    "fund_size",
)


class QuoteRepository:
    """Liest und schreibt Instrumente und Kurs-Zeitreihen in SQLite."""

    def __init__(self, database_path: str) -> None:
        """
        Args:
            database_path: Pfad zur SQLite-Datei.
        """
        self._database_path = database_path

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Öffnet eine Verbindung, committet bei Erfolg und schließt immer."""
        connection = get_connection(self._database_path)
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def get_instrument_by_isin(self, isin: str) -> dict | None:
        """Gibt das Instrument zur ISIN zurück (oder ``None``)."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM instruments WHERE isin = ?", (isin,)
            ).fetchone()
            return dict(row) if row else None

    def get_instrument_by_symbol(self, symbol: str) -> dict | None:
        """Gibt das erste Instrument zum Symbol zurück (oder ``None``)."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM instruments WHERE symbol = ? ORDER BY id LIMIT 1",
                (symbol,),
            ).fetchone()
            return dict(row) if row else None

    def get_latest_quote(self, instrument_id: int) -> dict | None:
        """Gibt den jüngsten Kurspunkt eines Instruments zurück (oder ``None``)."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM quotes WHERE instrument_id = ? "
                "ORDER BY quote_time DESC LIMIT 1",
                (instrument_id,),
            ).fetchone()
            return dict(row) if row else None

    def get_history(
        self,
        instrument_id: int,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Gibt die Kurs-Zeitreihe eines Instruments zurück (neueste zuerst).

        Args:
            instrument_id: ID des Instruments.
            date_from: Optionale untere Grenze (ISO) auf ``quote_time``.
            date_to: Optionale obere Grenze (ISO) auf ``quote_time``.
            limit: Maximale Anzahl Punkte.

        Returns:
            Liste von Kurspunkt-Dicts.
        """
        clauses = ["instrument_id = ?"]
        params: list[object] = [instrument_id]
        if date_from:
            clauses.append("quote_time >= ?")
            params.append(date_from)
        if date_to:
            clauses.append("quote_time <= ?")
            params.append(date_to)
        params.append(limit)
        query = (
            f"SELECT * FROM quotes WHERE {' AND '.join(clauses)} "
            "ORDER BY quote_time DESC LIMIT ?"
        )
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def list_instruments(self) -> list[dict]:
        """Gibt alle bekannten Instrumente zurück (für den Hintergrund-Refresh)."""
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM instruments").fetchall()
            return [dict(row) for row in rows]

    def list_instruments_with_latest(self) -> list[dict]:
        """Gibt alle Instrumente inkl. jüngstem Kurs und History-Anzahl zurück."""
        query = """
            SELECT i.*,
                   q.price      AS latest_price,
                   q.quote_time AS latest_quote_time,
                   q.currency   AS latest_currency,
                   q.fetched_at AS latest_fetched_at,
                   (SELECT COUNT(*) FROM quotes WHERE instrument_id = i.id)
                       AS history_count
            FROM instruments i
            LEFT JOIN quotes q ON q.id = (
                SELECT id FROM quotes WHERE instrument_id = i.id
                ORDER BY quote_time DESC LIMIT 1
            )
            ORDER BY i.symbol
        """
        with self._connect() as connection:
            rows = connection.execute(query).fetchall()
            return [dict(row) for row in rows]

    def count_instruments(self) -> int:
        """Gibt die Anzahl bekannter Instrumente zurück (günstiger als eine Liste)."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS n FROM instruments"
            ).fetchone()
            return int(row["n"])

    def delete_instrument(self, isin: str) -> bool:
        """Löscht ein Instrument (und seine Quotes via Cascade) anhand der ISIN.

        Returns:
            True, wenn ein Instrument gelöscht wurde, sonst False.
        """
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM instruments WHERE isin = ?", (isin,)
            )
            return cursor.rowcount > 0

    def save_quote(self, response: QuoteResponse) -> int:
        """Speichert Instrument-Metadaten und hängt den Kurspunkt an.

        Args:
            response: Frisch beschaffte Kurs-Antwort.

        Returns:
            Die ID des (angelegten oder aktualisierten) Instruments.
        """
        with self._connect() as connection:
            instrument_id = self._upsert_instrument(connection, response)
            self._insert_quote(connection, instrument_id, response)
            return instrument_id

    def _upsert_instrument(
        self, connection: sqlite3.Connection, response: QuoteResponse
    ) -> int:
        """Legt das Instrument an oder aktualisiert seine Metadaten."""
        existing_id = self._find_instrument_id(
            connection, response.isin, response.symbol
        )
        meta = {field: getattr(response, field) for field in _META_FIELDS}

        if existing_id is None:
            columns = "isin, symbol, first_seen, meta_fetched_at, " + ", ".join(
                _META_FIELDS
            )
            placeholders = ", ".join(["?"] * (4 + len(_META_FIELDS)))
            values = [
                response.isin,
                response.symbol,
                response.fetched_at,
                response.fetched_at,
                *meta.values(),
            ]
            cursor = connection.execute(
                f"INSERT INTO instruments ({columns}) VALUES ({placeholders})", values
            )
            return int(cursor.lastrowid)

        assignments = ", ".join(f"{field} = ?" for field in _META_FIELDS)
        connection.execute(
            f"UPDATE instruments SET {assignments}, meta_fetched_at = ? WHERE id = ?",
            [*meta.values(), response.fetched_at, existing_id],
        )
        return existing_id

    @staticmethod
    def _find_instrument_id(
        connection: sqlite3.Connection, isin: str | None, symbol: str
    ) -> int | None:
        """Sucht ein Instrument per ISIN, sonst per Symbol."""
        if isin:
            row = connection.execute(
                "SELECT id FROM instruments WHERE isin = ?", (isin,)
            ).fetchone()
            if row:
                return int(row["id"])
        row = connection.execute(
            "SELECT id FROM instruments WHERE symbol = ? ORDER BY id LIMIT 1", (symbol,)
        ).fetchone()
        return int(row["id"]) if row else None

    @staticmethod
    def _insert_quote(
        connection: sqlite3.Connection, instrument_id: int, response: QuoteResponse
    ) -> None:
        """Hängt einen Kurspunkt an; Duplikate (gleicher quote_time) werden ignoriert."""
        connection.execute(
            "INSERT OR IGNORE INTO quotes "
            "(instrument_id, price, quote_time, volume, currency, fetched_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                instrument_id,
                response.price,
                response.quote_time,
                response.volume,
                response.currency,
                response.fetched_at,
            ),
        )
