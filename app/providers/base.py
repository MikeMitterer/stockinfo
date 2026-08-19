"""Domänen-Datentypen und Provider-Schnittstellen der Kursbeschaffung.

Provider geben rohe Datentypen zurück; die Service-Schicht setzt daraus die
API-Antwort zusammen. Protokolle ermöglichen austauschbare Implementierungen
(Strategy Pattern) und einfaches Mocken in Tests.
"""

from dataclasses import dataclass
from typing import Protocol

# Yahoo quoteType → interner Typ ("etf" | "stock") — gemeinsame Konstante für
# Resolver und Provider.
QUOTE_TYPE_MAP = {"ETF": "etf", "MUTUALFUND": "etf", "EQUITY": "stock"}


@dataclass
class ResolvedInstrument:
    """Ein aufgelöstes Wertpapier — genug Information, um einen Kurs abzufragen."""

    symbol: str
    isin: str | None = None
    exchange: str | None = None
    name: str | None = None
    type: str | None = None  # "stock" | "etf"
    currency: str | None = None


@dataclass
class RawQuote:
    """Rohe Kursdaten eines Anbieters (noch nicht angereichert)."""

    symbol: str
    price: float
    quote_time: str
    currency: str | None = None
    volume: int | None = None
    name: str | None = None
    type: str | None = None
    exchange: str | None = None
    isin: str | None = None


@dataclass
class EtfDetails:
    """ETF-spezifische Zusatzdaten (z.B. von justETF)."""

    ter: float | None = None
    provider: str | None = None
    replication: str | None = None
    fund_size: float | None = None
    # Die Währung des **Fonds** — nicht die des Handelsplatzes. Die kommt von
    # yfinance und ist eine andere Aussage: EUNL handelt in EUR, der Fonds
    # rechnet in USD.
    fund_currency: str | None = None
    fund_domicile: str | None = None
    name: str | None = None
    volatility: float | None = None  # 1-Jahres-Volatilität in % (justETF)
    accumulating: bool | None = None  # Thesaurierend (True) vs. Ausschüttend (False)
    # Woher dieser Stand kommt — die Quelle beschriftet sich selbst, statt dass
    # der aufrufende Service sie rät. Seit es mehr als eine ETF-Quelle gibt,
    # wäre ein fest verdrahtetes "yfinance+justetf" für die Hälfte der Papiere
    # schlicht falsch.
    source: str | None = None


class InstrumentResolver(Protocol):
    """Löst eine ISIN zu einem handelbaren Symbol auf."""

    def resolve_isin(self, isin: str) -> ResolvedInstrument | None: ...


class QuoteProvider(Protocol):
    """Liefert den aktuellen Kurs zu einem Symbol."""

    def fetch_quote(self, symbol: str) -> RawQuote | None: ...


class EtfEnricher(Protocol):
    """Liefert ETF-Zusatzdaten zu einer ISIN.

    Die beiden Methoden beantworten bewusst **verschiedene** Fragen. Eine
    leere Antwort von `fetch_etf` heißt „gerade nichts bekommen" und schützt
    den gespeicherten Stand; `is_responsible` sagt dagegen, ob diese Quelle für
    das Papier überhaupt zuständig ist. Ohne die Trennung gilt für einen Nutzer
    außerhalb Europas jeder ETF dauerhaft als unvollständig — justETF führt nur
    europäische Papiere, und „nicht zuständig" käme als derselbe leere Wert an
    wie „ausgefallen".
    """

    def is_responsible(self, isin: str) -> bool: ...

    def fetch_etf(self, isin: str, symbol: str | None = None) -> EtfDetails | None: ...
