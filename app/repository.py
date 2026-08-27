"""SQLite-Repository — kapselt allen Datenbankzugriff.

Kein Raw-SQL außerhalb dieser Schicht. Jede Methode nutzt eine eigene, kurz
gehaltene Verbindung — so ist der Zugriff thread-safe (Request-Threadpool und
Hintergrund-Scheduler teilen sich keine Connection).
"""

import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import structlog

from app.db import get_connection
from app.exchanges import canonical_identity, identity_from_symbol
from app.models import OVERRIDE_FIELDS, QuoteResponse

logger = structlog.get_logger()


class IncompleteIdentityError(ValueError):
    """Ein Papier soll angelegt werden, ohne dass seine Identität feststeht.

    Seit T-21 Teil 3 gibt es dafür keinen Zustand mehr: `ticker` und `mic`
    sind Pflicht, und zwar im Schema. Ohne diesen Fehler liefe der Aufrufer in
    eine `NOT NULL`-Verletzung — dieselbe Ablehnung, nur als `500` und ohne zu
    sagen, was fehlt.
    """

    def __init__(self, symbol: str) -> None:
        super().__init__(
            f"'{symbol}' trägt keine kanonische Identität (ticker und MIC)"
        )
        self.symbol = symbol


# Die beiden Kennungen des `409`. Sie sind die einzige Stelle, an der ein
# Konsument die zwei Fälle auseinanderhalten kann — beide tragen denselben
# Status, und der Status allein sagt nicht, was zu tun ist.
REASON_IDENTITY_CONFLICT = "identity_conflict"
REASON_SYMBOL_AMBIGUOUS = "symbol_ambiguous"


class AmbiguousSymbolError(ValueError):
    """Mehrere Listings tragen dieses Symbol — die API rät nicht.

    **Seit T-24 zugesagt** (`identity.ambiguous_symbol_status`), bis Runde 45
    aber nirgends erzeugt: `symbol` ist Anzeigename und nicht garantiert
    eindeutig, seit `US` in `XNYS` und `XNAS` zerfällt. Der Lookup lautete
    `ORDER BY id LIMIT 1` und traf damit **definiert das Falsche** — die
    ältere Zeile, unabhängig davon, welche gemeint war. Auf dem
    verändernden Weg war es schlimmer: `DELETE /instruments/by-symbol/{symbol}`
    löschte alle passenden Zeilen auf einmal.

    Der Fehler trägt die Kandidaten mit, weil ein `409` ohne sie den Aufrufer
    ratlos zurückließe: Er hat nur das mehrdeutige Symbol und bekäme keinen
    Weg, es aufzulösen. Mit `listing_id` je Kandidat hat er einen.
    """

    def __init__(self, symbol: str, candidates: list[dict]) -> None:
        super().__init__(f"Symbol ist mehrdeutig: {symbol}")
        self.symbol = symbol
        self.candidates = candidates


class IdentityConflictError(ValueError):
    """Zwei Zeilen beanspruchen dieselbe kanonische Identität.

    Der Fall entsteht aus einem **gewachsenen** Bestand, nicht aus einem
    Programmfehler: `AAPL/XNAS` liegt ohne ISIN im Bestand, `AAPL/XNYS` mit
    ISIN — und dieselbe ISIN wandert nach XNAS. Die ISIN-Suche findet dann die
    XNYS-Zeile, deren Aktualisierung mit der XNAS-Zeile kollidiert.

    Beide Zeilen beschreiben nach `one_active_listing_per_isin` dasselbe
    Listing; sie **zusammenzuführen** ist eine Datenoperation mit eigener
    Entscheidung (welche `listing_id` überlebt, wohin die Kurspunkte wandern)
    und gehört nicht in einen Kursabruf. Bis dahin sagt dieser Fehler, was der
    Fall ist, statt als `IntegrityError` ein `500` zu werden.

    **Bis Runde 43 endete er trotzdem als `500`** — geworfen wurde er hier,
    behandelt nirgends. Der Weg nach draußen ist jetzt ein zugesagter `409`
    (`app/main.py`, `identity_conflict`), und er gilt für jeden Endpunkt, der
    speichert: Kursabruf wie Aufnahmeweg stolpern über dieselbe Zeile.
    """

    def __init__(self, ticker: str, mic: str, isin: str | None) -> None:
        super().__init__(
            f"'{ticker}/{mic}' ist bereits vergeben; ISIN {isin} zeigt auf eine "
            "andere Zeile"
        )
        self.ticker = ticker
        self.mic = mic
        self.isin = isin


@dataclass(frozen=True)
class SavedQuote:
    """Was das Speichern eines Kurses am Instrument bewirkt hat.

    `created` ist eine **Tatsache der schreibenden Transaktion**, keine
    Vorabfrage (T-21 Teil 3, `#2j2`). Ein Existenzcheck *vor* dem Schreiben
    wäre falsch: Ein konkurrierender Insert kann ihn überholen, und der
    Aufnahmeweg meldete `201` für ein Papier, das jemand anders gerade angelegt
    hat. Wahr ist `created` deshalb nur, wenn der `INSERT` selbst durchkam —
    im abgefangenen UNIQUE-Rennen ist er falsch.

    Bis T-21 Teil 3 gab `save_quote` nur die ID zurück und warf diese
    Information weg, obwohl sie an der Stelle vorlag, an der sie entsteht.
    """

    instrument_id: int
    created: bool

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
    # der jüngste Metadaten-Stand kommt.
    "source",
)

# Die Felder, über die allein justETF Auskunft gibt.
#
# Sie dürfen nur geschrieben werden, wenn die Antwort tatsächlich von dort
# kommt (`QuoteResponse.metadata_complete`). Sonst löscht ein einzelner
# Ausfall den gesamten gepflegten Stand — genau das ist am 2026-08-18
# passiert. `source` gehört dazu, weil er die stehengebliebenen Werte
# beschreibt und nicht den Abruf, der nichts geliefert hat.
#
# Öffentlich, weil dieselbe Menge zweimal gebraucht wird: Hier entscheidet sie,
# was **nicht geschrieben** wird, und in `CachedQuoteService` darüber, was in
# der Antwort aus dem gespeicherten Stand **stehen bleibt**. Zwei Listen liefen
# auseinander, und die Antwort widerspräche der Zeile daneben.
PROTECTED_META_FIELDS = frozenset(
    {
        "provider",
        "ter",
        "replication",
        "fund_size",
        "fund_domicile",
        "fund_currency",
        "volatility",
        "accumulating",
        "source",
    }
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
        """Gibt das **eindeutige** Instrument zum Symbol zurück (oder ``None``).

        Raises:
            AmbiguousSymbolError: Mehrere Listings tragen dieses Symbol.
        """
        with self._connect() as connection:
            row = self._unique_symbol_row(connection, symbol)
            return dict(row) if row else None

    def get_instrument_by_identity(self, ticker: str, mic: str) -> dict | None:
        """Gibt das Instrument zur **kanonischen Identität** zurück.

        Der Aufnahmeweg schlägt hierüber nach, nicht über `symbol` — und das
        ist der Unterschied, der `AAPL.XNAS` von `AAPL.XNYS` trennt. Beide
        tragen denselben Abrufalias `AAPL`, weil die US-Plätze keinen Suffix
        führen; eine Suche über das Symbol fände deshalb die falsche Börse
        oder, auf leerem Bestand, gar nichts Eindeutiges.

        Die Abfrage ist eindeutig: `idx_instruments_ticker_mic` liegt auf genau
        diesem Paar.

        Args:
            ticker: Kanonischer Ticker.
            mic: ISO-10383-MIC des Handelsplatzes.

        Returns:
            Die Zeile, oder ``None``.
        """
        with self._connect() as connection:
            row = self._identity_row(connection, ticker, mic)
            return dict(row) if row else None

    @staticmethod
    def _identity_row(
        connection: sqlite3.Connection, ticker: str, mic: str, columns: str = "*"
    ) -> sqlite3.Row | None:
        """Die **eine** Abfrage über die kanonische Identität.

        Zwei Aufrufer stellen dieselbe Frage aus verschiedenen Lagen:
        `get_instrument_by_identity` mit eigener Verbindung für den
        Aufnahmeweg, `_find_instrument_id` innerhalb der laufenden
        Schreibtransaktion. Getrennt formuliert liefen sie beim ersten
        Sonderfall auseinander — und genau dort ist der Unterschied teuer, weil
        er über die Zuordnung eines Papiers entscheidet.
        """
        return connection.execute(
            f"SELECT {columns} FROM instruments WHERE ticker = ? AND mic = ?",
            (ticker, mic),
        ).fetchone()

    # Was ein Kandidat im `409` über sich verrät. Genau die Felder der Fixture
    # `contract/fixtures/quote-409-ambiguous-symbol.json` — der Rumpf ist seit
    # T-24 zugesagt und wird hier nicht neu erfunden.
    _CANDIDATE_COLUMNS = ("listing_id", "symbol", "mic", "exchange", "isin")

    @staticmethod
    def _unique_symbol_row(
        connection: sqlite3.Connection, symbol: str
    ) -> sqlite3.Row | None:
        """Die **eine** Auskunft „eindeutig oder mehrdeutig?" über ein Symbol.

        Jeder Weg, der ein Symbol als Eingabe nimmt, fragt hierüber — lesend
        wie verändernd. Getrennt formuliert lief jede Stelle für sich, und sie
        liefen auseinander: Das Lesen nahm die älteste Zeile
        (`ORDER BY id LIMIT 1`), das Löschen nahm **alle**. Beides ist das von
        T-24 verbotene stille Raten, nur in verschiedene Richtungen.

        Args:
            connection: Offene Verbindung der laufenden Abfrage.
            symbol: Der Anzeigename, der kein Bezeichner ist.

        Returns:
            Die eine Zeile, oder ``None`` wenn es keine gibt.

        Raises:
            AmbiguousSymbolError: Mehr als eine Zeile trägt dieses Symbol.
        """
        rows = connection.execute(
            "SELECT * FROM instruments WHERE symbol = ? ORDER BY id", (symbol,)
        ).fetchall()
        if len(rows) > 1:
            raise AmbiguousSymbolError(
                symbol,
                [
                    {name: row[name] for name in QuoteRepository._CANDIDATE_COLUMNS}
                    for row in rows
                ],
            )
        return rows[0] if rows else None

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
        with self._connect() as connection:
            rows = connection.execute(self._instrument_query()).fetchall()
            return [dict(row) for row in rows]

    def get_instrument_with_latest(self, instrument_id: int) -> dict | None:
        """Dieselbe Zeile wie in der Liste, für **ein** Instrument.

        Der Aufnahmeweg liefert nach dem Speichern genau die Zeile aus, die
        `GET /instruments` auch zeigen würde. Deshalb teilt sie sich die
        Abfrage mit der Liste: Zwei getrennte `SELECT`s über dieselbe
        Verknüpfung liefen beim ersten neuen Feld auseinander, und der
        Aufnahmeweg zeigte dann etwas anderes als die Übersicht.

        Args:
            instrument_id: Die lokale ID des Instruments.

        Returns:
            Die Zeile, oder ``None`` wenn es sie nicht (mehr) gibt.
        """
        with self._connect() as connection:
            row = connection.execute(
                self._instrument_query("WHERE i.id = ?"), (instrument_id,)
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def _instrument_query(where: str = "") -> str:
        """Die **eine** Abfrage hinter Übersicht und Einzelzeile."""
        manual = ",\n                   ".join(
            f"o.{field} AS manual_{field}" for field in OVERRIDE_FIELDS
        )
        return f"""
            SELECT i.*,
                   q.price      AS latest_price,
                   q.quote_time AS latest_quote_time,
                   q.currency   AS latest_currency,
                   q.fetched_at AS latest_fetched_at,
                   {manual},
                   (SELECT COUNT(*) FROM quotes WHERE instrument_id = i.id)
                       AS history_count
            FROM instruments i
            LEFT JOIN quotes q ON q.id = (
                SELECT id FROM quotes WHERE instrument_id = i.id
                ORDER BY quote_time DESC LIMIT 1
            )
            LEFT JOIN instrument_overrides o ON o.instrument_id = i.id
            {where}
            ORDER BY i.symbol
        """

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

        Aktualisiert die **eindeutige** Zeile zum Symbol. Bis Runde 45 nahm sie
        die älteste — bei zwei gleichnamigen Listings hätte der Benutzer damit
        die ISIN an einen Handelsplatz geschrieben, den er nicht gemeint hat,
        und es nicht gemerkt.

        Raises:
            AmbiguousSymbolError: Mehrere Listings tragen dieses Symbol.
        """
        with self._connect() as connection:
            row = self._unique_symbol_row(connection, symbol)
            if row is None:
                return
            connection.execute(
                "UPDATE instruments SET isin = ? WHERE id = ?", (isin, row["id"])
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
        self, instrument_id: int, values: dict[str, object], updated_at: str
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
        filtered = {field: values.get(field) for field in OVERRIDE_FIELDS}
        filtered["accumulating"] = (
            None if filtered["accumulating"] is None else int(bool(filtered["accumulating"]))
        )

        with self._connect() as connection:
            if all(value is None for value in filtered.values()):
                connection.execute(
                    "DELETE FROM instrument_overrides WHERE instrument_id = ?",
                    (instrument_id,),
                )
                return

            columns = ", ".join(OVERRIDE_FIELDS)
            placeholders = ", ".join("?" for _ in OVERRIDE_FIELDS)
            assignments = ", ".join(f"{field} = excluded.{field}" for field in OVERRIDE_FIELDS)
            connection.execute(
                f"INSERT INTO instrument_overrides (instrument_id, {columns}, updated_at) "
                f"VALUES (?, {placeholders}, ?) "
                f"ON CONFLICT(instrument_id) DO UPDATE SET {assignments}, "
                "updated_at = excluded.updated_at",
                (instrument_id, *(filtered[field] for field in OVERRIDE_FIELDS), updated_at),
            )

    def set_volatility(self, instrument_id: int, volatility: float) -> None:
        """Aktualisiert gezielt die Volatilität eines Instruments."""
        with self._connect() as connection:
            connection.execute(
                "UPDATE instruments SET volatility = ? WHERE id = ?",
                (volatility, instrument_id),
            )

    def delete_by_symbol(self, symbol: str) -> bool:
        """Löscht **ein** Instrument (und seine Quotes via Cascade) per Symbol.

        Für Wertpapiere ohne ISIN (nur per Symbol erfasst).

        **Der schärfste der drei Symbolwege.** Bis Runde 45 lautete die Abfrage
        `DELETE FROM instruments WHERE symbol = ?` — bei zwei gleichnamigen
        Listings verschwanden beide samt Kurshistorie, auf einen Klick, ohne
        Rückfrage. Genau dieser Endpunkt ist das Beispiel, mit dem T-24 die
        `409`-Regel begründet hat.

        Returns:
            True, wenn ein Instrument gelöscht wurde, sonst False.

        Raises:
            AmbiguousSymbolError: Mehrere Listings tragen dieses Symbol.
        """
        with self._connect() as connection:
            row = self._unique_symbol_row(connection, symbol)
            if row is None:
                return False
            cursor = connection.execute(
                "DELETE FROM instruments WHERE id = ?", (row["id"],)
            )
            return cursor.rowcount > 0

    def save_quote(self, response: QuoteResponse) -> SavedQuote:
        """Speichert Instrument-Metadaten und hängt den Kurspunkt an.

        Args:
            response: Frisch beschaffte Kurs-Antwort.

        Returns:
            Die ID des (angelegten oder aktualisierten) Instruments und ob es
            in genau diesem Aufruf entstanden ist.
        """
        with self._connect() as connection:
            saved = self._upsert_instrument(connection, response)
            self._insert_quote(connection, saved.instrument_id, response)
            return saved

    def _upsert_instrument(
        self, connection: sqlite3.Connection, response: QuoteResponse
    ) -> SavedQuote:
        """Legt das Instrument an oder aktualisiert seine Metadaten.

        Ein UNIQUE-Konflikt beim Anlegen (paralleler Erst-Request oder
        Scheduler) wird aufgelöst, indem auf das inzwischen existierende
        Instrument aktualisiert wird — und **genau dieser Zweig** ist der
        Grund, warum `created` von hier kommt und nicht aus dem Aufrufer:
        Der Konflikt ist der einzige Ort, an dem sichtbar wird, dass ein
        anderer schneller war.
        """
        existing_id = self._find_instrument_id(
            connection, response.isin, response.symbol, response.ticker, response.mic
        )
        meta = {field: getattr(response, field) for field in self._writable_fields(response)}

        if existing_id is None:
            try:
                return SavedQuote(
                    self._insert_instrument(connection, response, meta), created=True
                )
            except sqlite3.IntegrityError:
                # **Mit derselben Auskunft wie oben.** Bis Runde 42 fragte der
                # Retry nur nach ISIN und Symbol — und fand damit ausgerechnet
                # das nicht wieder, worüber er gerade gestolpert war: ein
                # aliasloses Listing ohne ISIN, dessen Konflikt am
                # `(ticker, mic)`-Index entstand. Aus dem zugesagten
                # `created=false` wurde so ein `500`.
                existing_id = self._find_instrument_id(
                    connection,
                    response.isin,
                    response.symbol,
                    response.ticker,
                    response.mic,
                )
                if existing_id is None:
                    raise

        meta = {**meta, **self._identity_update(connection, existing_id, response)}

        assignments = ", ".join(f"{field} = ?" for field in meta)
        values = list(meta.values())
        # Der Zeitstempel wandert nur mit, wenn die Antwort die ETF-Felder
        # tatsächlich kennt. Sonst gälte ein Stand als frisch, den nie jemand
        # geholt hat: `_etf_metadata_is_stale` liest genau diese Spalte, der
        # Scheduler läuft weit häufiger als `metadata_ttl_days`, und justETF
        # käme nach dem ersten Kontakt nie wieder an die Reihe.
        if response.metadata_complete:
            assignments += ", meta_fetched_at = ?"
            values.append(response.fetched_at)
        try:
            connection.execute(
                f"UPDATE instruments SET {assignments} WHERE id = ?",
                [*values, existing_id],
            )
        except sqlite3.IntegrityError as exc:
            # Die Zeile, die über die ISIN gefunden wurde, soll eine Identität
            # annehmen, die eine **andere** Zeile schon trägt. Das ist kein
            # Rennen und keine Verletzung des Aufrufers, sondern ein gewachsener
            # Bestand, in dem zwei Zeilen dasselbe Listing meinen.
            if response.ticker and response.mic:
                raise IdentityConflictError(
                    response.ticker, response.mic, response.isin
                ) from exc
            raise
        return SavedQuote(existing_id, created=False)

    @staticmethod
    def _identity_update(
        connection: sqlite3.Connection, instrument_id: int, response: QuoteResponse
    ) -> dict:
        """Was diese Antwort an der gespeicherten Identität ändern darf.

        Die Regel hat **eine Richtung**: Eine vollständige Zuordnung darf eine
        offene oder überholte ersetzen, eine leere niemals eine bestehende.

        * **Nachtragen.** Die Migration lässt `AAPL` offen — den Handelsplatz
          kann sie offline nicht kennen. Die Auflösung kennt ihn (`NMS` →
          `XNAS`), und hier wird er eingetragen. Ohne diesen Weg bliebe jede
          einmal offene Zeile es für immer.
        * **Mitwandern.** Stellt jemand die bevorzugte Börse um, löst dieselbe
          ISIN auf ein anderes Listing auf. Bliebe die Identität stehen, zeigte
          `symbol` auf Mailand und `mic` auf Xetra — dieselbe Zeile, zwei
          Handelsplätze.
        * **Nicht leeren.** Weiß eine Antwort nichts, bleibt der gespeicherte
          Stand. Eine bestehende Zuordnung zu überschreiben, weil gerade
          niemand nachgesehen hat, ist derselbe Datenverlust, den
          `_writable_fields` bei den ETF-Feldern verhindert.

        Jede Änderung an einer schon vollständigen Zuordnung wird
        protokolliert: Sie ist selten und für den, der sie bemerkt, erklärungs-
        bedürftig.

        **Offen für Teil 3:** Eine von Hand gesetzte Zuordnung ist hier noch
        nicht von einer maschinellen zu unterscheiden — beide tragen
        `resolved`. Solange das so ist, kann die Auflösung eine manuelle
        Korrektur überschreiben. Teil 3 braucht dafür einen eigenen Status,
        den der automatische Weg nicht anfasst.

        Args:
            connection: Offene Verbindung innerhalb der Transaktion.
            instrument_id: Die Zeile, die aktualisiert wird.
            response: Die zu speichernde Antwort.

        Returns:
            Die zu schreibenden Identitätsfelder — leer, wenn nichts zu tun ist.
        """
        identity = canonical_identity(response.ticker, response.mic)
        if identity is None:
            return {}
        ticker, mic = identity

        row = connection.execute(
            "SELECT ticker, mic FROM instruments WHERE id = ?", (instrument_id,)
        ).fetchone()
        if row and (row["ticker"], row["mic"]) == (ticker, mic):
            return {}

        if row and row["ticker"] and row["mic"]:
            logger.info(
                "identity_changed",
                instrument_id=instrument_id,
                symbol=response.symbol,
                previous_ticker=row["ticker"],
                previous_mic=row["mic"],
                ticker=ticker,
                mic=mic,
            )
        return {"ticker": ticker, "mic": mic}

    @staticmethod
    def _writable_fields(response: QuoteResponse) -> tuple[str, ...]:
        """Welche Metadatenfelder diese Antwort überschreiben darf.

        Vollständige Antworten schreiben alles. Weiß eine Antwort über die
        ETF-Extras nichts — justETF nicht gefragt oder nicht erreichbar —,
        bleiben die zugehörigen Spalten unangetastet: Ihr gespeicherter Stand
        ist mehr wert als ein ``NULL``, das nur „ich habe gerade nicht
        nachgesehen" bedeutet.

        Args:
            response: Die zu speichernde Kurs-Antwort.

        Returns:
            Die zu schreibenden Spaltennamen, in der Reihenfolge von
            ``_META_FIELDS``.
        """
        if response.metadata_complete:
            return _META_FIELDS
        return tuple(
            field for field in _META_FIELDS if field not in PROTECTED_META_FIELDS
        )

    @staticmethod
    def _insert_instrument(
        connection: sqlite3.Connection, response: QuoteResponse, meta: dict
    ) -> int:
        """Legt ein neues Instrument an und gibt seine ID zurück.

        Die Spaltenliste kommt aus `meta`, nicht aus `_META_FIELDS`: Eine
        unvollständige Antwort schreibt nur einen Teil der Felder (siehe
        `_writable_fields`), und eine feste Spaltenliste zählte dann mehr
        Platzhalter als Werte — SQLite bricht mit `Incorrect number of
        bindings supplied` ab, mitten im ersten Anlegen eines Papiers.
        """
        identity = canonical_identity(response.ticker, response.mic)
        if identity is None:
            # **Kein Anlegen ohne Identität** (T-21 Teil 3, `#2b2`). Vorher
            # entstand hier eine Zeile mit `identity_status =
            # legacy_unresolved`; seit die halbe Identität nirgends mehr
            # weiterleben darf, ist das kein Zustand mehr, sondern ein Fehler
            # des Aufrufers — und er gehört dort beantwortet, wo er entsteht.
            raise IncompleteIdentityError(response.symbol)
        ticker, mic = identity

        columns = (
            "isin, symbol, first_seen, meta_fetched_at, "
            "ticker, mic, listing_id, " + ", ".join(meta)
        )
        placeholders = ", ".join(["?"] * (7 + len(meta)))
        values = [
            response.isin,
            response.symbol,
            response.fetched_at,
            # Kein Zeitstempel ohne belastbare Metadaten — `None` heißt „nie
            # geholt" und macht den Stand beim nächsten Abruf sofort fällig.
            response.fetched_at if response.metadata_complete else None,
            ticker,
            mic,
            # Die dauerhafte Kennung entsteht **hier**, nicht erst beim
            # nächsten Start. Sie allein in der Migration zu vergeben ließ jede
            # zur Laufzeit angelegte Zeile ohne — und weil SQLite `NULL` im
            # Eindeutigkeits-Index als eigenen Wert zählt, fiel das nicht
            # einmal auf.
            str(uuid.uuid4()),
            *meta.values(),
        ]
        cursor = connection.execute(
            f"INSERT INTO instruments ({columns}) VALUES ({placeholders})", values
        )
        return int(cursor.lastrowid)

    @staticmethod
    def _find_instrument_id(
        connection: sqlite3.Connection,
        isin: str | None,
        symbol: str,
        ticker: str | None = None,
        mic: str | None = None,
    ) -> int | None:
        """Sucht ein Instrument — ISIN, dann Identität, dann Symbol.

        Die Reihenfolge trägt drei verschiedene Zusagen:

        1. **Die ISIN zuerst.** Sie ist eindeutig und überdauert einen Wechsel
           des Handelsplatzes. Nur so zieht der nächste Kurs eine überholte
           Zuordnung gerade, statt ein zweites Listing anzulegen.
        2. **Dann `(ticker, mic)`.** Für ein Papier ohne ISIN ist das die
           kanonische Identität, und der Eindeutigkeitsindex liegt darauf.
        3. **Das Symbol nur, wenn es eindeutig ist.** Und genau hier lag der
           Fehler: `AAPL` ist *kein* Bezeichner eines Listings — die US-Plätze
           führen keinen Suffix, also heißen `AAPL/XNAS` und `AAPL/XNYS` beide
           so. Eine Suche darüber fand die falsche Notierung und schrieb ihr
           anschließend die neue Börse in die Zeile. Zerlegbar ist ein Symbol
           genau dann, wenn `identity_from_symbol` etwas liefert; sonst
           identifiziert es nichts und wird nicht gefragt.

        Args:
            connection: Offene Verbindung der laufenden Transaktion.
            isin: ISIN der Antwort, sofern bekannt.
            symbol: Das Anbietersymbol.
            ticker: Kanonischer Ticker der Antwort.
            mic: MIC der Antwort.

        Returns:
            Die ID des gefundenen Instruments, oder ``None``.
        """
        if isin:
            row = connection.execute(
                "SELECT id FROM instruments WHERE isin = ?", (isin,)
            ).fetchone()
            if row:
                return int(row["id"])

        if ticker and mic:
            row = QuoteRepository._identity_row(connection, ticker, mic, columns="id")
            if row:
                return int(row["id"])

        if identity_from_symbol(symbol) is None:
            return None

        # **Dieselbe Auskunft wie die Leseseite**, und nicht noch ein
        # `ORDER BY id LIMIT 1`: Ein Symbol, das zwei Listings trifft, darf
        # auch hier nicht still eines davon fortschreiben. Erreichbar ist der
        # Zweig heute nicht — er greift nur ohne `ticker`/`mic`, und die sind
        # seit Übergabe 2A Pflicht. Wird er es je wieder, ist die Antwort
        # dieselbe wie überall sonst.
        row = QuoteRepository._unique_symbol_row(connection, symbol)
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
