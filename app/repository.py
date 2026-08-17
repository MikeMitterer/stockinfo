"""SQLite-Repository — kapselt allen Datenbankzugriff.

Kein Raw-SQL außerhalb dieser Schicht. Jede Methode nutzt eine eigene, kurz
gehaltene Verbindung — so ist der Zugriff thread-safe (Request-Threadpool und
Hintergrund-Scheduler teilen sich keine Connection).
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app.db import get_connection
from app.models import OVERRIDE_FIELDS, QuoteResponse

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
    "fund_domicile",
    "fund_currency",
    "volatility",
    "accumulating",
    # Wandert mit den Metadaten mit, nicht mit dem Kurspunkt: Er sagt, woher
    # der jüngste Metadaten-Stand kommt, und wird bei jedem Upsert überschrieben.
    "source",
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

    def get_daily_closes(
        self, instrument_id: int, date_from: str | None = None
    ) -> list[dict]:
        """Gibt die gecachten Tages-Schlusskurse zurück (älteste zuerst).

        Args:
            instrument_id: ID des Instruments.
            date_from: Optionale untere Grenze (ISO-Datum) auf ``date``.

        Returns:
            Liste von Tages-Schlusskurs-Dicts.
        """
        clauses = ["instrument_id = ?"]
        params: list[object] = [instrument_id]
        if date_from:
            clauses.append("date >= ?")
            params.append(date_from)
        query = (
            f"SELECT * FROM daily_closes WHERE {' AND '.join(clauses)} ORDER BY date"
        )
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def upsert_daily_closes(self, instrument_id: int, rows: list[dict]) -> None:
        """Speichert/aktualisiert Tages-Schlusskurse (Update bei gleichem Datum).

        Args:
            instrument_id: ID des Instruments.
            rows: Liste von ``{"date", "close", "currency"}``.
        """
        if not rows:
            return
        with self._connect() as connection:
            connection.executemany(
                "INSERT INTO daily_closes (instrument_id, date, close, currency) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT (instrument_id, date) "
                "DO UPDATE SET close = excluded.close, currency = excluded.currency",
                [
                    (instrument_id, row["date"], row["close"], row.get("currency"))
                    for row in rows
                ],
            )

    def daily_closes_range(self, instrument_id: int) -> tuple[str, str] | None:
        """Gibt (min, max) der gecachten Datumsgrenzen zurück (oder ``None``)."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT MIN(date) AS lo, MAX(date) AS hi FROM daily_closes "
                "WHERE instrument_id = ?",
                (instrument_id,),
            ).fetchone()
            if row is None or row["lo"] is None:
                return None
            return (row["lo"], row["hi"])

    def get_daily_meta(self, instrument_id: int) -> dict | None:
        """Gibt die Fetch-Wasserzeichen (fetched_from/to) zurück (oder ``None``).

        ``None`` in einer Spalte bedeutet 'unbegrenzt' (gesamte Historie).
        """
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM daily_meta WHERE instrument_id = ?", (instrument_id,)
            ).fetchone()
            return dict(row) if row else None

    def set_daily_meta(
        self, instrument_id: int, fetched_from: str | None, fetched_to: str | None
    ) -> None:
        """Setzt die Fetch-Wasserzeichen für ein Instrument."""
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO daily_meta (instrument_id, fetched_from, fetched_to) "
                "VALUES (?, ?, ?) "
                "ON CONFLICT (instrument_id) DO UPDATE SET "
                "fetched_from = excluded.fetched_from, fetched_to = excluded.fetched_to",
                (instrument_id, fetched_from, fetched_to),
            )

    def list_instruments(self) -> list[dict]:
        """Gibt alle bekannten Instrumente zurück (für den Hintergrund-Refresh)."""
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM instruments").fetchall()
            return [dict(row) for row in rows]

    def list_instruments_with_latest(self) -> list[dict]:
        """Gibt alle Instrumente inkl. jüngstem Kurs, History-Anzahl und Overrides zurück.

        Die manuellen Werte kommen **roh** mit (``manual_*``) — die Vorrang-Regel
        gehört in die Fachschicht, nicht in SQL. Sonst stünde die Regel an einer
        Stelle, die niemand liest, wenn er sie sucht.
        """
        manuell = ",\n                   ".join(
            f"o.{feld} AS manual_{feld}" for feld in OVERRIDE_FIELDS
        )
        query = f"""
            SELECT i.*,
                   q.price      AS latest_price,
                   q.quote_time AS latest_quote_time,
                   q.currency   AS latest_currency,
                   q.fetched_at AS latest_fetched_at,
                   {manuell},
                   (SELECT COUNT(*) FROM quotes WHERE instrument_id = i.id)
                       AS history_count
            FROM instruments i
            LEFT JOIN quotes q ON q.id = (
                SELECT id FROM quotes WHERE instrument_id = i.id
                ORDER BY quote_time DESC LIMIT 1
            )
            LEFT JOIN instrument_overrides o ON o.instrument_id = i.id
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

    def set_isin(self, symbol: str, isin: str) -> None:
        """Trägt die ISIN eines Instruments nachträglich ein (per Symbol).

        Aktualisiert gezielt nur das erste Instrument zum Symbol — nie mehrere
        Zeilen (würde den UNIQUE-Constraint auf ``isin`` verletzen).
        """
        with self._connect() as connection:
            connection.execute(
                "UPDATE instruments SET isin = ? WHERE id = ("
                "SELECT id FROM instruments WHERE symbol = ? ORDER BY id LIMIT 1)",
                (isin, symbol),
            )

    def get_overrides(self, instrument_id: int) -> dict | None:
        """Gibt die von Hand gepflegten Kennzahlen eines Instruments zurück.

        Returns:
            Zeile als dict oder None, wenn nie etwas eingetragen wurde.
        """
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM instrument_overrides WHERE instrument_id = ?",
                (instrument_id,),
            ).fetchone()
            return dict(row) if row else None

    def set_overrides(
        self, instrument_id: int, werte: dict[str, object], updated_at: str
    ) -> None:
        """Schreibt die manuellen Kennzahlen — immer den vollständigen Satz.

        ``None`` heißt **löschen**, nicht „unverändert": Die Oberfläche schickt
        stets alle Felder, und ein geleertes muss den Wert auch wieder entfernen
        können. Bleibt nichts übrig, verschwindet die Zeile ganz.

        Die Spaltenliste kommt aus ``OVERRIDE_FIELDS`` statt aus getippten
        Parametern — bei acht Feldern wäre eine Signatur aus Einzelwerten nicht
        mehr zu lesen, und jede neue Kennzahl müsste an vier Stellen nachgezogen
        werden.
        """
        gefiltert = {feld: werte.get(feld) for feld in OVERRIDE_FIELDS}
        gefiltert["accumulating"] = (
            None if gefiltert["accumulating"] is None else int(bool(gefiltert["accumulating"]))
        )

        with self._connect() as connection:
            if all(wert is None for wert in gefiltert.values()):
                connection.execute(
                    "DELETE FROM instrument_overrides WHERE instrument_id = ?",
                    (instrument_id,),
                )
                return

            spalten = ", ".join(OVERRIDE_FIELDS)
            platzhalter = ", ".join("?" for _ in OVERRIDE_FIELDS)
            zuweisungen = ", ".join(f"{feld} = excluded.{feld}" for feld in OVERRIDE_FIELDS)
            connection.execute(
                f"INSERT INTO instrument_overrides (instrument_id, {spalten}, updated_at) "
                f"VALUES (?, {platzhalter}, ?) "
                f"ON CONFLICT(instrument_id) DO UPDATE SET {zuweisungen}, "
                "updated_at = excluded.updated_at",
                (instrument_id, *(gefiltert[feld] for feld in OVERRIDE_FIELDS), updated_at),
            )

    def set_volatility(self, instrument_id: int, volatility: float) -> None:
        """Aktualisiert gezielt die Volatilität eines Instruments."""
        with self._connect() as connection:
            connection.execute(
                "UPDATE instruments SET volatility = ? WHERE id = ?",
                (volatility, instrument_id),
            )

    def delete_by_symbol(self, symbol: str) -> bool:
        """Löscht ein Instrument (und seine Quotes via Cascade) anhand des Symbols.

        Für Wertpapiere ohne ISIN (nur per Symbol erfasst).

        Returns:
            True, wenn ein Instrument gelöscht wurde, sonst False.
        """
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM instruments WHERE symbol = ?", (symbol,)
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
        """Legt das Instrument an oder aktualisiert seine Metadaten.

        Ein UNIQUE-Konflikt beim Anlegen (paralleler Erst-Request oder
        Scheduler) wird aufgelöst, indem auf das inzwischen existierende
        Instrument aktualisiert wird.
        """
        existing_id = self._find_instrument_id(
            connection, response.isin, response.symbol
        )
        meta = {field: getattr(response, field) for field in _META_FIELDS}

        if existing_id is None:
            try:
                return self._insert_instrument(connection, response, meta)
            except sqlite3.IntegrityError:
                existing_id = self._find_instrument_id(
                    connection, response.isin, response.symbol
                )
                if existing_id is None:
                    raise

        assignments = ", ".join(f"{field} = ?" for field in _META_FIELDS)
        connection.execute(
            f"UPDATE instruments SET {assignments}, meta_fetched_at = ? WHERE id = ?",
            [*meta.values(), response.fetched_at, existing_id],
        )
        return existing_id

    @staticmethod
    def _insert_instrument(
        connection: sqlite3.Connection, response: QuoteResponse, meta: dict
    ) -> int:
        """Legt ein neues Instrument an und gibt seine ID zurück."""
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

    def get_fx_rate(self, base: str, quote: str) -> dict | None:
        """Gibt den gecachten Wechselkurs für ein Paar zurück (oder ``None``)."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM fx_rates WHERE base = ? AND quote = ?", (base, quote)
            ).fetchone()
            return dict(row) if row else None

    def save_fx_rate(
        self, base: str, quote: str, rate: float, quote_time: str, fetched_at: str
    ) -> None:
        """Speichert/aktualisiert einen Wechselkurs (Upsert auf (base, quote))."""
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO fx_rates (base, quote, rate, quote_time, fetched_at) "
                "VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT (base, quote) DO UPDATE SET "
                "rate = excluded.rate, quote_time = excluded.quote_time, "
                "fetched_at = excluded.fetched_at",
                (base, quote, rate, quote_time, fetched_at),
            )
