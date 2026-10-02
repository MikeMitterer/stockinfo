"""SQLModel-Abbild der Kerntabellen — nur innerhalb von `app/persistence/`.

Die Modelle beschreiben das bestehende Schema; angelegt und migriert wird es
weiterhin vom DDL in `db.py` und `detail_store.py`. Darum kein `create_all`:
Zwei Schemaquellen liefen beim ersten neuen Feld auseinander. Dass jedes
Modell genau die Spalten seiner Tabelle trägt, prüft
`tests/test_persistence_tables.py`.

Nach außen gehen nur `dict`s. Ein Modellobjekt, das durch die App wandert,
wäre ein Datenbankzugriff an jeder Stelle, die es anfasst.
"""

from sqlalchemy import Table
from sqlmodel import Field, SQLModel


def table_of(record: type[SQLModel]) -> Table:
    """Die Tabelle hinter einem Modell — für Abfragen, die Spalten statt Objekte liefern.

    SQLModel setzt `__table__` erst zur Laufzeit; der Typprüfer sieht es nicht.
    Hier steht der eine Zugriff darauf.
    """
    return record.__table__  # pyright: ignore[reportAttributeAccessIssue]


class InstrumentRecord(SQLModel, table=True):
    """Eine Zeile aus `instruments`."""

    __tablename__ = "instruments"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    isin: str | None = None
    symbol: str
    kind: str = "listed"
    ticker: str | None = None
    mic: str | None = None
    base: str | None = None
    quote_currency: str | None = None
    listing_id: str | None = None
    exchange: str | None = None
    name: str | None = None
    type: str | None = None
    currency: str | None = None
    provider: str | None = None
    ter: float | None = None
    replication: str | None = None
    fund_size: float | None = None
    volatility: float | None = None
    accumulating: int | None = None
    fund_domicile: str | None = None
    fund_currency: str | None = None
    source: str | None = None
    first_seen: str
    meta_fetched_at: str | None = None


class QuoteRecord(SQLModel, table=True):
    """Ein Kurspunkt aus `quotes`."""

    __tablename__ = "quotes"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    instrument_id: int
    price: float
    quote_time: str
    volume: int | None = None
    currency: str | None = None
    fetched_at: str


class DailyCloseRecord(SQLModel, table=True):
    """Ein Tagesschlusskurs aus `daily_closes`."""

    __tablename__ = "daily_closes"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    instrument_id: int
    date: str
    close: float
    currency: str | None = None


class DetailValueRecord(SQLModel, table=True):
    """Ein Quellenwert aus `detail_values`; `value` ist JSON-Text."""

    __tablename__ = "detail_values"  # type: ignore[assignment]

    instrument_id: int = Field(primary_key=True)
    field: str = Field(primary_key=True)
    source: str = Field(primary_key=True)
    value: str
    currency: str | None = None
    as_of: str | None = None


class DetailOverrideRecord(SQLModel, table=True):
    """Eine manuelle Eingabe aus `detail_overrides`; `value` ist JSON-Text."""

    __tablename__ = "detail_overrides"  # type: ignore[assignment]

    instrument_id: int = Field(primary_key=True)
    field: str = Field(primary_key=True)
    value: str
    currency: str | None = None
    as_of: str | None = None
