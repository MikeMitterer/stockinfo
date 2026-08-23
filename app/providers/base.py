"""Domänen-Datentypen und Provider-Schnittstellen der Kursbeschaffung.

Provider geben rohe Datentypen zurück; die Service-Schicht setzt daraus die
API-Antwort zusammen. Protokolle ermöglichen austauschbare Implementierungen
(Strategy Pattern) und einfaches Mocken in Tests.
"""

from dataclasses import dataclass
from typing import Protocol

from stockinfo_plugin.types import NotFound, NotResponsible, Unavailable

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

    # Die kanonische Identität (T-21). `symbol` bleibt daneben stehen: Es ist
    # der **Anbieter-Alias**, mit dem yfinance den Kurs holt und an dem die
    # Profil-Links hängen — `ticker` + `mic` sind das, was jede andere Quelle
    # versteht. Beide sind `None`, solange die Zuordnung nicht eindeutig ist;
    # geraten wird nichts.
    ticker: str | None = None
    mic: str | None = None


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


class SourceUnavailableError(Exception):
    """Eine Quelle war nicht arbeitsfähig — Netz, Kontingent, Fehlerantwort.

    Der Unterschied zu „nichts gefunden" ist der ganze Zweck: Ein Client, der
    beides als ``None`` meldet, macht aus einem Ausfall ein „gibt es nicht"
    und damit aus einem 502 ein 404. Wer einen Dienst anspricht, wirft
    deshalb, statt leer zurückzukommen.
    """


Resolution = ResolvedInstrument | NotResponsible | NotFound | Unavailable
"""Was ein Resolver antworten kann.

Die drei Fehlfälle kommen aus `stockinfo_plugin.types`, dem Vertrag für
Plugins — sie hier ein zweites Mal zu definieren hieße, zwei Wahrheiten über
denselben Vertrag zu führen.

Der Erfolgsfall ist noch `ResolvedInstrument` und nicht das `Resolved` des
Plugin-Vertrags: Jenes trägt `ticker` und `mic` getrennt statt eines fertigen
Anbieter-Symbols, und diese Umstellung ist die Identitätsfrage aus **T-21**.
Sie hier vorwegzunehmen hieße, zwei Umbauten in einem Diff zu vermischen.
"""


class InstrumentResolver(Protocol):
    """Löst eine ISIN zu einem handelbaren Symbol auf.

    `handles` beantwortet die Frage **vor** der Anfrage: Eine Quelle, die für
    ein Papier gar nicht zuständig ist, soll nichts kosten — kein Netz, kein
    Kontingent. Erst danach entscheidet `resolve_isin`, ob sie das Papier
    kennt (`NotFound`) oder gerade nicht nachsehen kann (`Unavailable`).
    """

    def handles(self, isin: str) -> bool: ...

    def resolve_isin(self, isin: str) -> Resolution: ...


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

    def is_responsible(
        self,
        isin: str | None,
        *,
        exchange: str | None = None,
        currency: str | None = None,
    ) -> bool: ...

    def fetch_etf(
        self,
        isin: str | None,
        symbol: str | None = None,
        *,
        exchange: str | None = None,
        currency: str | None = None,
    ) -> EtfDetails | None: ...
