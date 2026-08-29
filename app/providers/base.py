"""Domänen-Datentypen und Provider-Schnittstellen der Kursbeschaffung.

Provider geben rohe Datentypen zurück; die Service-Schicht setzt daraus die
API-Antwort zusammen. Protokolle ermöglichen austauschbare Implementierungen
(Strategy Pattern) und einfaches Mocken in Tests.
"""

from dataclasses import dataclass
from typing import Protocol

from stockinfo_plugin.types import (
    Identity,
    IsinOnlyIdentity,
    ListedIdentity,
    NotFound,
    NotResponsible,
    PairIdentity,
    Unavailable,
)

# Der kanonische Gattungskatalog (T-31, Entscheidung 2 · T-38 kanonisiert ihn).
# **Offen, nicht abschließend**: Ein neuer Wert ist ein Nachtrag und kein Bruch,
# und was die App nicht kennt, zeigt sie als das, was die Quelle sagt — statt es
# auf `stock` zu runden. Das Runden war der Fehler.
INSTRUMENT_TYPES = ("stock", "etf", "etc", "fund", "crypto", "bond")

# Yahoo quoteType → interner Typ. **Erkennen, nicht Raten** (T-31, Matrix `#4`).
#
# `MUTUALFUND` bildete bis T-31 auf `etf` ab, und das war eine Unwahrheit mit
# Folgen: Ein nicht börsengehandelter Fonds bekam die ETF-Anreicherung samt
# TER-Frage an justETF, wo er nicht geführt wird. Seit Mikes Entscheidung vom
# 2026-08-29 gibt es `fund` als eigene Gattung.
QUOTE_TYPE_MAP = {
    "ETF": "etf",
    "MUTUALFUND": "fund",
    "EQUITY": "stock",
    "CRYPTOCURRENCY": "crypto",
    "BOND": "bond",
}


@dataclass
class ResolvedInstrument:
    """Ein aufgelöstes Wertpapier — genug Information, um einen Kurs abzufragen."""

    symbol: str
    isin: str | None = None
    exchange: str | None = None
    name: str | None = None
    type: str | None = None
    currency: str | None = None

    # Die kanonische Identität (T-21), seit T-31 in **drei Formen**. `symbol`
    # bleibt daneben stehen: Es ist der **Anbieter-Alias**, mit dem yfinance den
    # Kurs holt und an dem die Profil-Links hängen — die Identität ist das, was
    # jede andere Quelle versteht.
    #
    # Flach gehalten und nicht als verschachteltes Objekt: Die Datenbank führt
    # dieselben Spalten, und der `CHECK` je `kind` bindet sie dort. Die Union
    # entsteht daraus über `identity()` — an **einer** Stelle, damit die Regel
    # nicht an jeder Verwendung neu formuliert wird.
    kind: str = "listed"
    ticker: str | None = None
    mic: str | None = None
    base: str | None = None
    quote_currency: str | None = None

    def identity(self) -> Identity | None:
        """Die Identität in der Form, die `kind` nennt.

        Returns:
            Die passende `Identity`, oder ``None``, wenn die Felder der Form
            nicht vollständig sind. ``None`` heißt „noch keine Identität" und
            ist etwas anderes als eine erfundene — geraten wird nichts.
        """
        return identity_from_row(self)


def identity_from_row(row: object) -> Identity | None:
    """Die Identität einer gespeicherten Instrumentenzeile.

    Die Datenbank führt die Union flach, gebunden durch den `CHECK` je `kind`.
    Diese Funktion setzt sie wieder zusammen; **welche Form** vollständig ist,
    entscheidet `app.exchanges.identity_form` — dieselbe Weiche, die auch die
    REST-Seite benutzt. `ResolvedInstrument.identity()` ruft hierher durch.

    Args:
        row: Eine Instrumentenzeile als Mapping (``sqlite3.Row`` oder ``dict``).

    Returns:
        Die Identität, oder ``None``, wenn die Zeile die Felder ihrer Form
        nicht vollständig trägt.
    """
    # Lokal: `app.exchanges` bezieht seine Regeln aus dem Vertrag, und ein
    # Modulimport von hier dorthin und zurück schlösse den Kreis.
    from app.exchanges import identity_form

    read = (
        row.get
        if hasattr(row, "get")
        else (
            (lambda key: row[key])
            if hasattr(row, "keys")
            else (lambda key: getattr(row, key, None))
        )
    )
    form = identity_form(row)
    if form == "pair":
        return PairIdentity(base=read("base"), quote_currency=read("quote_currency"))
    if form == "isin_only":
        return IsinOnlyIdentity(isin=read("isin"))
    if form == "listed":
        return ListedIdentity(ticker=read("ticker"), mic=read("mic"), isin=read("isin"))
    return None


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
    """Löst ein Papier zu einer Identität auf — über ISIN **oder** Symbol.

    `handles` beantwortet die Frage **vor** der Anfrage: Eine Quelle, die für
    ein Papier gar nicht zuständig ist, soll nichts kosten — kein Netz, kein
    Kontingent. Erst danach entscheidet `resolve_isin`, ob sie das Papier
    kennt (`NotFound`) oder gerade nicht nachsehen kann (`Unavailable`).

    **`resolve_symbol` kam mit T-31 dazu, und der Anlass ist ein Orakel.**
    Matrix `#5` verlangt die Identitätsform aus dem *Gattungs-Befund der
    Quelle*, `#6` eine eigene Kennung für eine nicht aufgenommene Gattung.
    Beides setzt voraus, dass überhaupt jemand gefragt wird — und über den
    By-Symbol-Weg gab es dafür keinen Einstieg: `QuoteRequest` verlangt eine
    fertige Identität, also genau das, was noch fehlt.

    Aus dem Symbol zu raten schied aus. Ein `^GDAXI` trägt kein Merkmal, an
    dem sich eine Gattung ablesen ließe; jede Ableitung aus der Symbolform
    endete beim Zufallsbefund „kein Börsensuffix", den `#6` ausdrücklich
    verbietet. Der Vertrag hatte die Antwort längst — `ResolveRequest.symbol`
    steht seit T-27a darin und wurde von niemandem gelesen.

    Eine Quelle, die nur ISINs kennt, gibt `NotResponsible` zurück; die
    Vorgabe in `CompositeResolver` tut das für sie.
    """

    def handles(self, isin: str) -> bool: ...

    def resolve_isin(self, isin: str) -> Resolution: ...

    def resolve_symbol(self, symbol: str) -> Resolution: ...


def declared_name(source: object) -> str | None:
    """Wie sich eine Quelle selbst nennt — oder ``None``, wenn sie es nicht tut.

    **Die eine Stelle, an der die Regel steht.** In T-37 stand sie zweimal, in
    `QuoteService` und `CachedFxService`, mit demselben Rückfall — zwei
    Kopien einer Entscheidung, die beim nächsten Umbau auseinanderlaufen.

    Der Rückfall ist bewusst ``None`` und **kein Ersatzname**. Der erste
    Anlauf setzte hier ``"unbekannt"``; das ist ein deutsches Wort in einem
    Datenfeld, das die Oberfläche unübersetzt anzeigt — in der englischen
    Fassung stünde es genauso da. Eine Quelle ohne Namen ist keine Herkunft,
    und ein fehlender Wert sagt das besser als ein erfundener.
    """
    name = getattr(source, "name", None)
    return name if isinstance(name, str) and name else None


class QuoteProvider(Protocol):
    """Liefert den aktuellen Kurs zu einem Symbol."""

    name: str
    """Wie diese Quelle heißt — für die Herkunftsangabe.

    Seit T-37 Teil des Protokolls und nicht mehr nur eine Eigenschaft, die
    zufällig alle Kettenglieder haben: Wer die Herkunft aufschreiben will,
    muss sie verlangen dürfen.
    """

    def fetch_quote(self, instrument: ResolvedInstrument) -> RawQuote | None: ...


class DailyCloseProvider(Protocol):
    """Liefert echte Tages-Schlusskurse zu einem Symbol.

    **Hierher gezogen, nicht neu erfunden.** Der Vertrag stand seit jeher in
    `app/services/daily_sync.py` — also bei einem *Verbraucher* statt bei den
    Quellen. Meine erste T-22-Fassung hat ihn deshalb übersehen und daneben
    einen zweiten mit demselben Namen angelegt: zwei Wahrheiten über denselben
    Vertrag, und die Verbraucher hingen weiter an der alten. Jetzt steht er
    einmal hier, neben `QuoteProvider`, und `daily_sync` importiert ihn.

    ``None`` heißt „konnte nicht nachsehen" (Netz, Rate-Limit), die leere Liste
    „nachgesehen, nichts da". Der Unterschied entscheidet, ob ein gespeicherter
    Stand überschrieben werden darf.
    """

    def fetch_daily_closes(
        self,
        symbol: str,
        start: str | None = None,
        *,
        identity: Identity | None = None,
        instrument_type: str | None = None,
    ) -> list[dict] | None:
        """Holt Tagesschlusskurse.

        **Die Identität kommt seit T-23 mit, und das ist kein Beiwerk.**
        Das Anbieter-Symbol allein genügt nicht: Die fünf US-Börsen führen
        absichtlich keinen Alias, `AAPL/XNAS` wird als ``AAPL`` gespeichert.
        Wer daraus die Börse zurückrechnen will, rät — und der Versuch hat in
        T-23 Runde 3 alle aliaslosen Plätze still abgeschaltet.

        Der Aufrufer **hat** die Identität; sie wegzuwerfen und danach zu
        erraten ist der Umweg. Dieselbe Entscheidung wie beim Kurs.

        **Seit T-31 ist es die Union statt `ticker`/`mic`.** Ein Paar und eine
        ISIN-only-Anleihe waren mit zwei Feldern gar nicht adressierbar.
        """
        ...


class FxRateProvider(Protocol):
    """Liefert einen Wechselkurs (1 base = ? quote).

    Wie `DailyCloseProvider` hierher gezogen — der Vertrag stand in
    `app/services/fx_service.py`. Der Name bleibt `FxRateProvider` und wird
    nicht zu `FxProvider` verkürzt: Ihn beim Umzug umzubenennen hieße, jede
    bestehende Fundstelle anzufassen, ohne dass die Aussage genauer würde.
    """

    name: str
    """Wie diese Quelle heißt — für die Herkunftsangabe.

    Bei `fx.source` ist das wirklich der Kurslieferant; der Vertrag sagt dort
    „Woher der Kurs stammt". Siehe `declared_name` und
    `CachedFxService._fx_source`.
    """

    def fetch_fx_rate(self, base: str, quote: str) -> float | None: ...


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
