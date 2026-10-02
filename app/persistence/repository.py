"""SQLite-Repository über SQLModel — kapselt allen Datenbankzugriff.

Jede Methode öffnet eine eigene, kurz gehaltene Session (`open_session`) —
so ist der Zugriff thread-safe (Request-Threadpool und Hintergrund-Scheduler
teilen sich keine Verbindung). Die Kerntabellen laufen über die Modelle aus
`tables.py`; `meta`, `daily_meta` und `fx_rates` bis T-92 über `text()` in
derselben Session und Transaktion.
"""

import json
import uuid
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import cast

import structlog
from sqlalchemy import (
    ColumnElement,
    CursorResult,
    Result,
    Select,
    and_,
    delete,
    func,
    or_,
    select,
    text,
    update,
)
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col

from app.calculated_metrics import CALCULATED_SOURCE
from app.detail_models import DetailDefinition
from app.exchanges import canonical_identity, identity_from_symbol
from app.models import (
    IDENTITY_COLUMNS,
    OVERRIDE_FIELDS,
    IdentityOut,
    IsinOnlyIdentityOut,
    ListedIdentityOut,
    PairIdentityOut,
    QuoteResponse,
    identity_columns,
    identity_from_columns,
)
from app.persistence import detail_store
from app.persistence.quote_store import PROTECTED_META_FIELDS, SavedQuote
from app.persistence.session import fetch_all, fetch_one, open_session
from app.persistence.tables import (
    DailyCloseRecord,
    DetailOverrideRecord,
    DetailValueRecord,
    InstrumentRecord,
    QuoteRecord,
    table_of,
)

_INSTRUMENTS = table_of(InstrumentRecord)
_QUOTES = table_of(QuoteRecord)
_DAILY_CLOSES = table_of(DailyCloseRecord)


def _changed(result: Result) -> CursorResult:
    """Das Ergebnis eines `INSERT`/`DELETE` mit Zeilenzahl und neuer Zeilen-ID.

    SQLAlchemy liefert hier zur Laufzeit ein `CursorResult`, typisiert aber
    `Result`; nur das erste kennt `rowcount` und `lastrowid`.
    """
    return cast(CursorResult, result)

logger = structlog.get_logger()


def _identity_label(identity: IdentityOut) -> str:
    """Wie eine Identität in einer Meldung erscheint.

    Je Form die Felder, die sie ausmachen — und nicht ein Format, das für die
    anderen beiden erfundene Werte bräuchte. Die Meldung liest ein Mensch, der
    danach in der Datenbank nachsieht; sie muss ihn dorthin führen.
    """
    if isinstance(identity, PairIdentityOut):
        return f"'{identity.base}/{identity.quote_currency}'"
    if isinstance(identity, ListedIdentityOut):
        return f"'{identity.ticker}/{identity.mic}'"
    return f"'{identity.isin}'"


def _isin_of(identity: IdentityOut) -> str | None:
    """Die ISIN dieser Identität, falls die Form eine trägt.

    Ein Währungspaar **hat** keine — ``None`` erfindet hier nichts, anders als
    ein Ticker, den man für ein Paar nur ausdenken könnte.
    """
    return getattr(identity, "isin", None)


def identity_condition(identity: IdentityOut) -> ColumnElement[bool]:
    """Die Bedingung, die genau diese Identität trifft.

    Je Form eine andere, und je Form liegt ein eigener partieller Unique-Index
    darauf. Eine gemeinsame Bedingung über alle sechs Spalten gäbe es zwar,
    aber sie könnte keinen Index nutzen und träfe bei ``NULL`` ohnehin nichts —
    SQLite hält zwei ``NULL`` nie für gleich.

    Args:
        identity: Die gesuchte Identität.

    Returns:
        Die Bedingung für ein ``select(...).where(...)``.
    """
    if isinstance(identity, PairIdentityOut):
        return and_(
            col(InstrumentRecord.kind) == "pair",
            col(InstrumentRecord.base) == identity.base,
            col(InstrumentRecord.quote_currency) == identity.quote_currency,
        )
    if isinstance(identity, IsinOnlyIdentityOut):
        return and_(col(InstrumentRecord.kind) == "isin_only", col(InstrumentRecord.isin) == identity.isin)
    return and_(
        col(InstrumentRecord.kind) == "listed",
        col(InstrumentRecord.ticker) == identity.ticker,
        col(InstrumentRecord.mic) == identity.mic,
    )


class IncompleteIdentityError(ValueError):
    """Ein Papier soll angelegt werden, ohne dass seine Identität feststeht.

    Seit T-21 Teil 3 gibt es dafür keinen Zustand mehr, und seit T-31 ist
    „vollständig" je **Form** definiert: Ticker und MIC bei `listed`, Basiswert
    und Quote-Währung bei `pair`, die ISIN bei `isin_only`. Der `CHECK` im
    Schema erzwingt es; ohne diesen Fehler liefe der Aufrufer in eine
    `CHECK`-Verletzung — dieselbe Ablehnung, nur als `500` und ohne zu sagen,
    was fehlt.
    """

    def __init__(self, symbol: str) -> None:
        super().__init__(
            f"'{symbol}' trägt keine vollständige Identität in einer der drei "
            "Formen (listed, pair, isin_only)"
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

    def __init__(self, identity: IdentityOut, isin: str | None) -> None:
        super().__init__(
            f"{_identity_label(identity)} ist bereits vergeben; ISIN {isin} "
            "zeigt auf eine andere Zeile"
        )
        self.identity = identity
        self.isin = isin


@dataclass(frozen=True)
class _InstrumentFacts:
    """Was `_insert_instrument` von seiner Vorlage wirklich liest.

    Eine `QuoteResponse` erfüllt diese Form von selbst; ein Papier ohne Kurs
    kann sie nicht bilden, weil ihm der Preis fehlt. Diese vier Felder sind
    der gemeinsame Nenner — und dass es nur vier sind, ist der Grund, warum
    beide Wege dieselbe Einfügung benutzen können.
    """

    identity: object
    symbol: str
    fetched_at: str
    metadata_complete: bool = False


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

KEEP_IF_UNKNOWN = frozenset({"name", "type"})
"""Felder, die eine **leere** Antwort nicht überschreiben darf.

Der Unterschied zu `PROTECTED_META_FIELDS` ist der Anlass, nicht die Absicht:
Dort entscheidet die *Herkunft* der Antwort (`metadata_complete`), hier der
*Wert*. Ein `NULL` heißt „ich weiß es nicht" und ist nie mehr wert als das,
was schon dasteht — ein echter neuer Name dagegen schon, und der wird
geschrieben.

**Warum das überhaupt nötig ist.** Name und Gattung beschreiben das *Papier*,
nicht den *Kurs*. Der Plugin-Vertrag trennt das sauber: `Resolved` trägt
`name` und `instrument_type`, `Quote` trägt Preis, Währung, Zeitpunkt und
Volumen — und kein Namensfeld. Das ist richtig so; ein Kurs ist ein Preis zu
einer Zeit und weiß nichts über die Gattung seines Papiers.

Nur schrieb der Kurs-Weg diese Spalten trotzdem mit, aus der Zeit, als der
Anbieter beides mitlieferte. Im UI-Lauf von T-35 dauerte es genau einen
Klick: Nach `POST /refresh/{isin}` war der Name **weg**, bei jedem Papier.

**Nur beim Aktualisieren.** Beim Anlegen muss der Wert geschrieben werden,
sonst entstünde die Zeile ohne Namen — der erste Anlauf dieser Änderung tat
genau das und ließ die beiden Plugin-Durchstiche auffliegen.
"""


class QuoteRepository:
    """Liest und schreibt Instrumente und Kurs-Zeitreihen in SQLite."""

    def __init__(self, database_path: str) -> None:
        """
        Args:
            database_path: Pfad zur SQLite-Datei.
        """
        self._database_path = database_path

    def _session(self, *, write: bool = False) -> AbstractContextManager[Session]:
        """Eine Session auf diese Datenbank; committet bei Erfolg.

        **Jeder schreibende Zugriff mit `write=True`.** Dann nimmt die Session
        die Schreibsperre gleich mit `BEGIN IMMEDIATE`. Mit einem
        gewöhnlichen `BEGIN` läsen parallele Schreiber zuerst denselben alten
        Stand; im WAL-Modus scheitert danach der Wechsel zur Schreibsperre
        sofort mit „database is locked", ohne die Wartezeit abzuwarten. So
        warten sie der Reihe nach, und der zweite sieht, was der erste
        geschrieben hat.
        """
        return open_session(self._database_path, immediate=write)

    def get_instrument_by_isin(self, isin: str) -> dict | None:
        """Gibt das Instrument zur ISIN zurück (oder ``None``)."""
        with self._session() as session:
            row = fetch_one(session, select(_INSTRUMENTS).where(col(InstrumentRecord.isin) == isin))
            return detail_store.read(session, row) if row else None

    def get_instrument_by_symbol(self, symbol: str) -> dict | None:
        """Gibt das **eindeutige** Instrument zum Symbol zurück (oder ``None``).

        Raises:
            AmbiguousSymbolError: Mehrere Listings tragen dieses Symbol.
        """
        with self._session() as session:
            row = self._unique_symbol_row(session, symbol)
            return detail_store.read(session, row) if row else None

    def get_instrument_by_identity(self, identity: IdentityOut) -> dict | None:
        """Gibt das Instrument zur **kanonischen Identität** zurück.

        Der Aufnahmeweg schlägt hierüber nach, nicht über `symbol` — und das
        ist der Unterschied, der `AAPL.XNAS` von `AAPL.XNYS` trennt. Beide
        tragen denselben Abrufalias `AAPL`, weil die US-Plätze keinen Suffix
        führen; eine Suche über das Symbol fände deshalb die falsche Börse
        oder, auf leerem Bestand, gar nichts Eindeutiges.

        Die Abfrage ist eindeutig: Auf der Bedingung jeder Form liegt ein
        partieller Unique-Index.

        Args:
            identity: Die gesuchte Identität, in ihrer Form.

        Returns:
            Die Zeile, oder ``None``.
        """
        with self._session() as session:
            row = self._identity_row(session, identity)
            return detail_store.read(session, row) if row else None

    @staticmethod
    def _identity_row(session: Session, identity: IdentityOut) -> dict | None:
        """Die **eine** Abfrage über die kanonische Identität.

        Zwei Aufrufer stellen dieselbe Frage aus verschiedenen Lagen:
        `get_instrument_by_identity` mit eigener Verbindung für den
        Aufnahmeweg, `_find_instrument_id` innerhalb der laufenden
        Schreibtransaktion. Getrennt formuliert liefen sie beim ersten
        Sonderfall auseinander — und genau dort ist der Unterschied teuer, weil
        er über die Zuordnung eines Papiers entscheidet.
        """
        return fetch_one(session, select(_INSTRUMENTS).where(identity_condition(identity)))

    # Was ein Kandidat im `409` über sich verrät. Genau die Felder der Fixture
    # `contract/fixtures/quote-409-ambiguous-symbol.json` — der Rumpf ist seit
    # T-24 zugesagt und wird hier nicht neu erfunden.
    _CANDIDATE_COLUMNS = ("listing_id", "symbol", "mic", "exchange", "isin")

    @staticmethod
    def _unique_symbol_row(session: Session, symbol: str) -> dict | None:
        """Die **eine** Auskunft „eindeutig oder mehrdeutig?" über ein Symbol.

        Jeder Weg, der ein Symbol als Eingabe nimmt, fragt hierüber — lesend
        wie verändernd. Getrennt formuliert lief jede Stelle für sich, und sie
        liefen auseinander: Das Lesen nahm die älteste Zeile
        (`ORDER BY id LIMIT 1`), das Löschen nahm **alle**. Beides ist das von
        T-24 verbotene stille Raten, nur in verschiedene Richtungen.

        Args:
            session: Session der laufenden Abfrage.
            symbol: Der Anzeigename, der kein Bezeichner ist.

        Returns:
            Die eine Zeile, oder ``None`` wenn es keine gibt.

        Raises:
            AmbiguousSymbolError: Mehr als eine Zeile trägt dieses Symbol.
        """
        rows = fetch_all(
            session,
            select(_INSTRUMENTS).where(col(InstrumentRecord.symbol) == symbol).order_by(col(InstrumentRecord.id)),
        )
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
        with self._session() as session:
            return fetch_one(
                session,
                select(_QUOTES)
                .where(col(QuoteRecord.instrument_id) == instrument_id)
                .order_by(col(QuoteRecord.quote_time).desc())
                .limit(1),
            )

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
        statement = select(_QUOTES).where(col(QuoteRecord.instrument_id) == instrument_id)
        if date_from:
            statement = statement.where(col(QuoteRecord.quote_time) >= date_from)
        if date_to:
            statement = statement.where(col(QuoteRecord.quote_time) <= date_to)
        statement = statement.order_by(col(QuoteRecord.quote_time).desc()).limit(limit)
        with self._session() as session:
            return fetch_all(session, statement)

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
        statement = select(_DAILY_CLOSES).where(col(DailyCloseRecord.instrument_id) == instrument_id)
        if date_from:
            statement = statement.where(col(DailyCloseRecord.date) >= date_from)
        with self._session() as session:
            return fetch_all(session, statement.order_by(col(DailyCloseRecord.date)))

    def upsert_daily_closes(self, instrument_id: int, rows: list[dict]) -> None:
        """Speichert/aktualisiert Tages-Schlusskurse (Update bei gleichem Datum).

        Args:
            instrument_id: ID des Instruments.
            rows: Liste von ``{"date", "close", "currency"}``.
        """
        if not rows:
            return
        # Ohne `values(...)` und mit einer Parameterliste: SQLAlchemy führt das
        # als `executemany` aus. Eine einzige `VALUES`-Liste über die ganze
        # Historie stieße an die Platzhaltergrenze von SQLite.
        statement = insert(DailyCloseRecord)
        statement = statement.on_conflict_do_update(
            index_elements=["instrument_id", "date"],
            set_={"close": statement.excluded.close, "currency": statement.excluded.currency},
        )
        with self._session(write=True) as session:
            session.execute(
                statement,
                [
                    {
                        "instrument_id": instrument_id,
                        "date": row["date"],
                        "close": row["close"],
                        "currency": row.get("currency"),
                    }
                    for row in rows
                ],
            )

    def daily_closes_range(self, instrument_id: int) -> tuple[str, str] | None:
        """Gibt (min, max) der gecachten Datumsgrenzen zurück (oder ``None``)."""
        with self._session() as session:
            row = session.execute(
                select(func.min(col(DailyCloseRecord.date)), func.max(col(DailyCloseRecord.date)))
                .where(col(DailyCloseRecord.instrument_id) == instrument_id)
            ).one()
            if row[0] is None:
                return None
            return (row[0], row[1])

    def get_daily_meta(self, instrument_id: int) -> dict | None:
        """Gibt die Fetch-Wasserzeichen (fetched_from/to) zurück (oder ``None``).

        ``None`` in einer Spalte bedeutet 'unbegrenzt' (gesamte Historie).
        """
        with self._session() as session:
            return fetch_one(
                session,
                text("SELECT * FROM daily_meta WHERE instrument_id = :id").bindparams(id=instrument_id),
            )

    def set_daily_meta(
        self, instrument_id: int, fetched_from: str | None, fetched_to: str | None
    ) -> None:
        """Setzt die Fetch-Wasserzeichen für ein Instrument."""
        with self._session(write=True) as session:
            session.execute(
                text(
                    "INSERT INTO daily_meta (instrument_id, fetched_from, fetched_to) "
                    "VALUES (:id, :fetched_from, :fetched_to) "
                    "ON CONFLICT (instrument_id) DO UPDATE SET "
                    "fetched_from = excluded.fetched_from, fetched_to = excluded.fetched_to"
                ),
                {"id": instrument_id, "fetched_from": fetched_from, "fetched_to": fetched_to},
            )

    def list_instruments(self) -> list[dict]:
        """Gibt alle bekannten Instrumente zurück (für den Hintergrund-Refresh)."""
        with self._session() as session:
            return [detail_store.read(session, row) for row in fetch_all(session, select(_INSTRUMENTS))]

    def list_instruments_with_latest(self) -> list[dict]:
        """Gibt alle Instrumente inkl. jüngstem Kurs, History-Anzahl und Overrides zurück.

        Die manuellen Werte kommen **roh** mit (``manual_*``) — die Vorrang-Regel
        gehört in die Fachschicht, nicht in SQL. Sonst stünde die Regel an einer
        Stelle, die niemand liest, wenn er sie sucht.
        """
        with self._session() as session:
            rows = fetch_all(session, self._instrument_query())
            return [detail_store.read(session, row) for row in rows]

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
        with self._session() as session:
            row = fetch_one(
                session, self._instrument_query().where(col(InstrumentRecord.id) == instrument_id)
            )
            return detail_store.read(session, row) if row else None

    @staticmethod
    def _instrument_query() -> Select:
        """Die **eine** Abfrage hinter Übersicht und Einzelzeile.

        Jede Instrumentenzeile mit ihrem jüngsten Kurspunkt (`latest_*`) und der
        Anzahl ihrer Kurspunkte (`history_count`).
        """
        # Ein eigener Alias für die Unterabfragen: Ohne ihn bezöge SQLAlchemy
        # deren `quotes` auf die verknüpfte Tabelle außen, und es bliebe keine
        # Tabelle übrig, aus der sie lesen.
        inner = _QUOTES.alias("inner_quotes")
        latest_id = (
            select(inner.c.id)
            .where(inner.c.instrument_id == col(InstrumentRecord.id))
            .order_by(inner.c.quote_time.desc())
            .limit(1)
            .correlate(_INSTRUMENTS)
            .scalar_subquery()
        )
        history_count = (
            select(func.count())
            .select_from(inner)
            .where(inner.c.instrument_id == col(InstrumentRecord.id))
            .correlate(_INSTRUMENTS)
            .scalar_subquery()
        )
        return (
            select(
                _INSTRUMENTS,
                col(QuoteRecord.price).label("latest_price"),
                col(QuoteRecord.quote_time).label("latest_quote_time"),
                col(QuoteRecord.currency).label("latest_currency"),
                col(QuoteRecord.fetched_at).label("latest_fetched_at"),
                history_count.label("history_count"),
            )
            .select_from(_INSTRUMENTS.outerjoin(_QUOTES, col(QuoteRecord.id) == latest_id))
            .order_by(col(InstrumentRecord.symbol))
        )

    def count_instruments(self) -> int:
        """Gibt die Anzahl bekannter Instrumente zurück (günstiger als eine Liste)."""
        with self._session() as session:
            return int(session.scalar(select(func.count()).select_from(_INSTRUMENTS)) or 0)

    def delete_instrument(self, isin: str) -> bool:
        """Löscht ein Instrument (und seine Quotes via Cascade) anhand der ISIN.

        Returns:
            True, wenn ein Instrument gelöscht wurde, sonst False.
        """
        with self._session(write=True) as session:
            result = _changed(session.execute(delete(InstrumentRecord).where(col(InstrumentRecord.isin) == isin)))
            return result.rowcount > 0

    def set_isin(self, symbol: str, isin: str) -> None:
        """Trägt die ISIN eines Instruments nachträglich ein (per Symbol).

        Aktualisiert die **eindeutige** Zeile zum Symbol. Bis Runde 45 nahm sie
        die älteste — bei zwei gleichnamigen Listings hätte der Benutzer damit
        die ISIN an einen Handelsplatz geschrieben, den er nicht gemeint hat,
        und es nicht gemerkt.

        Raises:
            AmbiguousSymbolError: Mehrere Listings tragen dieses Symbol.
        """
        with self._session(write=True) as session:
            row = self._unique_symbol_row(session, symbol)
            if row is None:
                return
            session.execute(
                update(InstrumentRecord).where(col(InstrumentRecord.id) == row["id"]).values(isin=isin)
            )

    def get_overrides(self, instrument_id: int) -> dict | None:
        """Kompatibilitätsprojektion der generischen manuellen Eingaben."""

        with self._session() as session:
            rows = fetch_all(
                session,
                select(
                    col(DetailOverrideRecord.field),
                    col(DetailOverrideRecord.value),
                    col(DetailOverrideRecord.as_of),
                ).where(col(DetailOverrideRecord.instrument_id) == instrument_id),
            )
            if not rows:
                return None
            values: dict[str, object] = {field: None for field in OVERRIDE_FIELDS}
            values.update({row['field']: json.loads(row['value']) for row in rows if row['field'] in values})
            values['instrument_id'] = instrument_id
            values['updated_at'] = max(row['as_of'] or '' for row in rows)
            return values

    def set_overrides(self, instrument_id: int, values: dict[str, object], updated_at: str, currency: str | None = None) -> None:
        """Der alte Vollsatz schreibt denselben Speicher wie generische Overrides."""
        with self._session(write=True) as session:
            for field in OVERRIDE_FIELDS:
                detail_store.put_manual(session, instrument_id, field, values.get(field), currency if field == 'fund_size' else None, updated_at)

    def set_detail_overrides(self, instrument_id: int, values: dict, updated_at: str) -> None:
        """Schreibt einen bereits validierten Patch atomar."""
        with self._session(write=True) as session:
            for field, entry in values.items():
                detail_store.put_manual(session, instrument_id, field, entry.value, entry.currency, updated_at)

    def detail_generation(self) -> str:
        """Bleibt über Neustarts erhalten und reist mit Sicherungen mit."""
        with self._session() as session:
            return session.execute(text("SELECT value FROM meta WHERE key='details_generation_id'")).one()[0]

    def has_detail_catalog(self) -> bool:
        """Unterscheidet ein leeres Profilschema vom alten internen Aufruf ohne Schema."""
        with self._session() as session:
            return session.execute(text("SELECT 1 FROM meta WHERE key='details_schema'")).first() is not None

    def detail_catalog(
        self, definitions: list[DetailDefinition] | None = None
    ) -> tuple[list[DetailDefinition], int]:
        """Liest das Profilschema oder schreibt eine neue Version atomar."""
        with self._session(write=definitions is not None) as session:
            if definitions is not None:
                version = detail_store.sync_catalog(session, definitions)
            else:
                row = session.execute(text("SELECT value FROM meta WHERE key='details_version'")).first()
                version = int(row[0]) if row else 0
            return detail_store.catalog(session), version

    def get_instrument_by_listing_id(self, listing_id: str) -> dict | None:
        """Eindeutiger öffentlicher Schreibweg, auch bei gleichnamigen Listings."""
        with self._session() as session:
            row = fetch_one(session, select(_INSTRUMENTS).where(col(InstrumentRecord.listing_id) == listing_id))
            return detail_store.read(session, row) if row else None

    def set_volatility(
        self, instrument_id: int, volatility: float, as_of: str | None = None
    ) -> None:
        """Berechnete Volatilität ist ebenfalls ein generischer Quellenwert.

        Args:
            instrument_id: ID des Instruments.
            volatility: Annualisierte Volatilität in Prozent.
            as_of: Datum des letzten Tagesschlusskurses, aus dem sie stammt;
                ``None``, wenn es unbekannt ist.
        """
        with self._session(write=True) as session:
            detail_store.put_provider(session, instrument_id, 'volatility',
                {'value': volatility, 'source': CALCULATED_SOURCE, 'as_of': as_of})

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
        with self._session(write=True) as session:
            row = self._unique_symbol_row(session, symbol)
            if row is None:
                return False
            result = _changed(session.execute(delete(InstrumentRecord).where(col(InstrumentRecord.id) == row["id"])))
            return result.rowcount > 0

    def save_instrument(self, resolved: object, fetched_at: str) -> SavedQuote:
        """Legt ein Papier **ohne Kurs** an — der Fall der OTC-Anleihe (T-31).

        `save_quote` speichert Instrument und Kurspunkt zusammen, weil beides
        üblicherweise zusammen ankommt. Für ein Papier, das keine Kursquelle
        hat, ist das die falsche Klammer: Die Auflösung war erfolgreich,
        Identität, Name und Gattung stehen fest — nur einen Preis gibt es
        nicht, und den zu erfinden verbietet das Ticket ausdrücklich („Kein
        Preis heißt kein Quote-Datensatz, nicht ein Quote mit Lücke").

        Benutzt wird dieselbe Einfügung wie beim Kursweg. `_insert_instrument`
        liest von seiner Vorlage ohnehin nur vier Dinge — Identität, Symbol,
        Zeitstempel und ob die Metadaten belastbar sind —, und ein zweiter
        Einfügepfad wäre die Stelle, an der `listing_id` oder der `CHECK` beim
        nächsten Umbau nur auf einer Seite nachgezogen würde.

        Args:
            resolved: Das aufgelöste Papier.
            fetched_at: Wann die Auflösung stattfand.

        Returns:
            Die ID und ob die Zeile in diesem Aufruf entstanden ist.
        """
        facts = _InstrumentFacts(
            identity=identity_from_columns(resolved),
            symbol=resolved.symbol,
            fetched_at=fetched_at,
        )
        if facts.identity is None:
            raise IncompleteIdentityError(resolved.symbol)

        meta = {
            "name": resolved.name,
            "type": resolved.type,
            "exchange": resolved.exchange,
            "currency": resolved.currency,
        }
        with self._session(write=True) as session:
            existing_id = self._find_instrument_id(session, facts.symbol, facts.identity)
            if existing_id is not None:
                return SavedQuote(existing_id, created=False)
            return SavedQuote(self._insert_instrument(session, facts, meta), created=True)

    def save_quote(self, response: QuoteResponse) -> SavedQuote:
        """Speichert Instrument-Metadaten und hängt den Kurspunkt an.

        Args:
            response: Frisch beschaffte Kurs-Antwort.

        Returns:
            Die ID des (angelegten oder aktualisierten) Instruments und ob es
            in genau diesem Aufruf entstanden ist.
        """
        with self._session(write=True) as session:
            saved = self._upsert_instrument(session, response)
            self._insert_quote(session, saved.instrument_id, response)
            for source, readings in response.detail_readings.items():
                # Migrierte Sammelquellen wie yfinance+justetf werden beim ersten
                # Einzelquellen-Refresh durch die feldweise Herkunft ersetzt.
                session.execute(delete(DetailValueRecord).where(
                    col(DetailValueRecord.instrument_id) == saved.instrument_id,
                    or_(
                        col(DetailValueRecord.source) == source,
                        func.instr("+" + col(DetailValueRecord.source) + "+", f"+{source}+") > 0,
                        col(DetailValueRecord.source) == "legacy",
                    ),
                ))
                for field, entry in readings.items():
                    detail_store.put_provider(session, saved.instrument_id, field,
                        {**entry, 'source': source, 'as_of': response.fetched_at})
            # Alte Provider und berechnete Kennzahlen benutzen denselben Speicher.
            declared = {field for readings in response.detail_readings.values() for field in readings}
            for field in self._writable_fields(response):
                if field in OVERRIDE_FIELDS and field not in declared and not response.detail_readings:
                    session.execute(delete(DetailValueRecord).where(
                        col(DetailValueRecord.instrument_id) == saved.instrument_id,
                        col(DetailValueRecord.field) == field,
                    ))
                    detail_store.put_provider(session, saved.instrument_id, field,
                        {'value': getattr(response, field), 'source': response.source or 'legacy',
                         'currency': response.fund_currency if field == 'fund_size' else None,
                         'as_of': response.fetched_at})
            return saved

    def _upsert_instrument(self, session: Session, response: QuoteResponse) -> SavedQuote:
        """Legt das Instrument an oder aktualisiert seine Metadaten.

        Ein UNIQUE-Konflikt beim Anlegen (paralleler Erst-Request oder
        Scheduler) wird aufgelöst, indem auf das inzwischen existierende
        Instrument aktualisiert wird — und **genau dieser Zweig** ist der
        Grund, warum `created` von hier kommt und nicht aus dem Aufrufer:
        Der Konflikt ist der einzige Ort, an dem sichtbar wird, dass ein
        anderer schneller war.
        """
        existing_id = self._find_instrument_id(session, response.symbol, response.identity)
        meta = {field: getattr(response, field) for field in self._writable_fields(response) if field not in OVERRIDE_FIELDS}

        if existing_id is None:
            try:
                # Scheitert das Anlegen am UNIQUE-Index, nimmt SQLite nur diese
                # eine Anweisung zurück; die Transaktion bleibt nutzbar, und der
                # Retry darunter findet die Zeile des Schnelleren. Ein SAVEPOINT
                # ist dafür nicht nötig (Test
                # `test_der_verlorene_anlegeversuch_kostet_die_transaktion_nicht`).
                return SavedQuote(
                    self._insert_instrument(session, response, meta), created=True
                )
            except IntegrityError:
                # **Mit derselben Auskunft wie oben.** Bis Runde 42 fragte der
                # Retry nur nach ISIN und Symbol — und fand damit ausgerechnet
                # das nicht wieder, worüber er gerade gestolpert war: ein
                # aliasloses Listing ohne ISIN, dessen Konflikt am
                # `(ticker, mic)`-Index entstand. Aus dem zugesagten
                # `created=false` wurde so ein `500`.
                existing_id = self._find_instrument_id(
                    session, response.symbol, response.identity
                )
                if existing_id is None:
                    raise

        meta = {**meta, **self._identity_update(session, existing_id, response)}
        # Ab hier wird **aktualisiert**, nicht angelegt: Was die Antwort nicht
        # weiß, bleibt stehen. Siehe `KEEP_IF_UNKNOWN`.
        #
        # **`not value` statt `value is not None`, seit T-38** — und der
        # Unterschied ist gemessen, nicht vorsorglich. Solange `name` nullbar
        # war, hieß „weiß ich nicht" immer ``None``, und die Prüfung stimmte.
        # Mit dem Pflichtfeld gibt es diesen Wert nicht mehr; was bleibt, ist
        # der **leere String** — konstruierbar, für das Repository von einer
        # Auskunft nicht zu unterscheiden, und er hat den gespeicherten Namen
        # überschrieben. Genau der Befund aus dem UI-Lauf, nur eine Schicht
        # tiefer und mit anderem Vorzeichen.
        #
        # Ein Pflichtfeld verhindert das Weglassen, nicht das Füllen mit
        # nichts. Diese Zeile schließt die zweite Hälfte.
        meta = {
            field: value
            for field, value in meta.items()
            if value or field not in KEEP_IF_UNKNOWN
        }

        # Der Zeitstempel wandert nur mit, wenn die Antwort die ETF-Felder
        # tatsächlich kennt. Sonst gälte ein Stand als frisch, den nie jemand
        # geholt hat: `_etf_metadata_is_stale` liest genau diese Spalte, der
        # Scheduler läuft weit häufiger als `metadata_ttl_days`, und justETF
        # käme nach dem ersten Kontakt nie wieder an die Reihe.
        if response.metadata_complete:
            meta["meta_fetched_at"] = response.fetched_at
        try:
            session.execute(
                update(InstrumentRecord).where(col(InstrumentRecord.id) == existing_id).values(meta)
            )
        except IntegrityError as exc:
            # Die Zeile, die über die ISIN gefunden wurde, soll eine Identität
            # annehmen, die eine **andere** Zeile schon trägt. Das ist kein
            # Rennen und keine Verletzung des Aufrufers, sondern ein gewachsener
            # Bestand, in dem zwei Zeilen dasselbe Listing meinen.
            raise IdentityConflictError(
                response.identity, _isin_of(response.identity)
            ) from exc
        return SavedQuote(existing_id, created=False)

    @staticmethod
    def _identity_update(session: Session, instrument_id: int, response: QuoteResponse) -> dict:
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
            session: Session innerhalb der Transaktion.
            instrument_id: Die Zeile, die aktualisiert wird.
            response: Die zu speichernde Antwort.

        Returns:
            Die zu schreibenden Identitätsfelder — leer, wenn nichts zu tun ist.
        """
        identity = response.identity
        if isinstance(identity, ListedIdentityOut) and not canonical_identity(
            identity.ticker, identity.mic
        ):
            # **Die `listed`-Hälfte bleibt streng** (T-31, Matrix `#3`): Ein
            # Ticker ohne echten MIC war noch nie eine Identität, und die Union
            # ändert daran nichts. Die beiden anderen Formen prüft der Vertrag
            # bereits an der Quelle, und der `CHECK` fängt den Rest.
            return {}

        row = fetch_one(
            session,
            select(*(col(getattr(InstrumentRecord, column)) for column in IDENTITY_COLUMNS))
            .where(col(InstrumentRecord.id) == instrument_id),
        )
        stored = identity_from_columns(row) if row else None
        if stored == identity:
            return {}

        if stored is not None:
            logger.info(
                "identity_changed",
                instrument_id=instrument_id,
                symbol=response.symbol,
                previous=_identity_label(stored),
                current=_identity_label(identity),
            )
        # **Alle sechs Spalten**, nicht nur die der neuen Form: Wechselt eine
        # Zeile die Form, blieben die Felder der alten sonst stehen und der
        # `CHECK` schlüge zu.
        return identity_columns(identity)

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
    def _insert_instrument(session: Session, response: QuoteResponse, meta: dict) -> int:
        """Legt ein neues Instrument an und gibt seine ID zurück.

        Die Spalten kommen aus `meta`, nicht aus `_META_FIELDS`: Eine
        unvollständige Antwort schreibt nur einen Teil der Felder (siehe
        `_writable_fields`); die übrigen bleiben leer, statt mit ``None``
        überschrieben zu werden.
        """
        identity = response.identity
        if isinstance(identity, ListedIdentityOut) and not canonical_identity(
            identity.ticker, identity.mic
        ):
            # **Kein Anlegen ohne Identität** (T-21 Teil 3, `#2b2`). Vorher
            # entstand hier eine Zeile mit `identity_status =
            # legacy_unresolved`; seit die halbe Identität nirgends mehr
            # weiterleben darf, ist das kein Zustand mehr, sondern ein Fehler
            # des Aufrufers — und er gehört dort beantwortet, wo er entsteht.
            #
            # Geprüft wird nur die `listed`-Form: Sie ist die einzige, für die
            # „echter MIC" überhaupt eine Frage ist. Die beiden anderen bindet
            # der `CHECK` im Schema.
            raise IncompleteIdentityError(response.symbol)

        result = _changed(session.execute(
            insert(InstrumentRecord).values(
                symbol=response.symbol,
                first_seen=response.fetched_at,
                # Kein Zeitstempel ohne belastbare Metadaten — `None` heißt „nie
                # geholt" und macht den Stand beim nächsten Abruf sofort fällig.
                meta_fetched_at=response.fetched_at if response.metadata_complete else None,
                # Die dauerhafte Kennung entsteht **hier**, nicht erst beim
                # nächsten Start. Sie allein in der Migration zu vergeben ließ
                # jede zur Laufzeit angelegte Zeile ohne — und weil SQLite
                # `NULL` im Eindeutigkeits-Index als eigenen Wert zählt, fiel
                # das nicht einmal auf.
                listing_id=str(uuid.uuid4()),
                **identity_columns(identity),
                **meta,
            )
        ))
        return int(result.lastrowid)

    @staticmethod
    def _find_instrument_id(session: Session, symbol: str, identity: IdentityOut) -> int | None:
        """Sucht ein Instrument — ISIN, dann Identität, dann Symbol.

        Die Reihenfolge trägt drei verschiedene Zusagen:

        1. **Die ISIN zuerst.** Sie ist eindeutig und überdauert einen Wechsel
           des Handelsplatzes. Nur so zieht der nächste Kurs eine überholte
           Zuordnung gerade, statt ein zweites Listing anzulegen.
        2. **Dann die Identität in ihrer Form.** Für ein Papier ohne ISIN —
           ein Währungspaar etwa — ist sie das einzige, was es bezeichnet, und
           auf der Bedingung jeder Form liegt ein partieller Unique-Index.
        3. **Das Symbol nur, wenn es eindeutig ist.** Und genau hier lag der
           Fehler: `AAPL` ist *kein* Bezeichner eines Listings — die US-Plätze
           führen keinen Suffix, also heißen `AAPL/XNAS` und `AAPL/XNYS` beide
           so. Eine Suche darüber fand die falsche Notierung und schrieb ihr
           anschließend die neue Börse in die Zeile. Zerlegbar ist ein Symbol
           genau dann, wenn `identity_from_symbol` etwas liefert; sonst
           identifiziert es nichts und wird nicht gefragt.

        Args:
            session: Session der laufenden Transaktion.
            symbol: Das Anbietersymbol.
            identity: Die Identität der Antwort, in ihrer Form.

        Returns:
            Die ID des gefundenen Instruments, oder ``None``.
        """
        isin = _isin_of(identity)
        if isin:
            found = session.scalar(select(col(InstrumentRecord.id)).where(col(InstrumentRecord.isin) == isin))
            if found is not None:
                return int(found)

        row = QuoteRepository._identity_row(session, identity)
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
        row = QuoteRepository._unique_symbol_row(session, symbol)
        return int(row["id"]) if row else None

    @staticmethod
    def _insert_quote(session: Session, instrument_id: int, response: QuoteResponse) -> None:
        """Schreibt einen Kurspunkt; ein Wert zum selben Zeitpunkt wird ersetzt.

        **Ein korrigierter Preis darf die vorhandene Zeile gewinnen.** Wer in
        einer gepflegten Datei nur den Preis ändert und den Zeitstempel stehen
        lässt, träfe sonst eine Zeile, die den neuen Wert verwirft — ohne
        Protokolleintrag und mit einer Erfolgsmeldung. Für zwei gleiche Abrufe
        ändert sich nichts: Dieselben Werte überschreiben sich selbst.
        """
        statement = insert(QuoteRecord).values(
            instrument_id=instrument_id,
            price=response.price,
            quote_time=response.quote_time,
            volume=response.volume,
            currency=response.currency,
            fetched_at=response.fetched_at,
        )
        session.execute(statement.on_conflict_do_update(
            index_elements=["instrument_id", "quote_time"],
            set_={
                "price": statement.excluded.price,
                "volume": statement.excluded.volume,
                "currency": statement.excluded.currency,
                "fetched_at": statement.excluded.fetched_at,
            },
        ))

    def get_fx_rate(self, base: str, quote: str) -> dict | None:
        """Gibt den gecachten Wechselkurs für ein Paar zurück (oder ``None``)."""
        with self._session() as session:
            return fetch_one(
                session,
                text("SELECT * FROM fx_rates WHERE base = :base AND quote = :quote")
                .bindparams(base=base, quote=quote),
            )

    def save_fx_rate(
        self,
        base: str,
        quote: str,
        rate: float,
        quote_time: str,
        fetched_at: str,
        source: str | None = None,
    ) -> None:
        """Speichert/aktualisiert einen Wechselkurs (Upsert auf (base, quote)).

        **`source` wird mitgespeichert**, seit T-36 Runde 3. Vorher ging die
        Herkunft beim ersten Cache-Treffer verloren, und der Leseweg setzte
        ersatzweise `"cache"` ein — eine Angabe, die `cached: true` ohnehin
        macht, und die den eigentlichen Lieferanten verschwieg.
        """
        with self._session(write=True) as session:
            session.execute(
                text(
                    "INSERT INTO fx_rates (base, quote, rate, quote_time, fetched_at, source) "
                    "VALUES (:base, :quote, :rate, :quote_time, :fetched_at, :source) "
                    "ON CONFLICT (base, quote) DO UPDATE SET "
                    "rate = excluded.rate, quote_time = excluded.quote_time, "
                    "fetched_at = excluded.fetched_at, source = excluded.source"
                ),
                {
                    "base": base,
                    "quote": quote,
                    "rate": rate,
                    "quote_time": quote_time,
                    "fetched_at": fetched_at,
                    "source": source,
                },
            )
