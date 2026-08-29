"""Beispiel-Plugin: Kurse, Historie und Devisen aus gepflegten Tabellen.

Dasselbe Prinzip wie `canada_file` eine Ebene weiter: *Wo keine Quelle etwas
weiß, trägt der Mensch die Werte ein.* Für einen Markt ohne kostenlosen
Anbieter — oder für ein Papier, das keine Quelle führt — ist eine von Hand
gepflegte Tabelle die einzige Alternative zum Warten.

**Warum drei Rollen in einem Beispiel.** Weil es der Regelfall ist: Die
kommerziellen Anbieter decken üblicherweise alles ab — Auflösung, Kurs,
Historie, Devisen aus einer Hand. Ein Beispiel, das nur eine Rolle zeigt,
beantwortet die naheliegendste Frage eines Plugin-Autors nicht.

Zwei Dateien, beide mit Semikolon und Kopfzeile::

    # closes.csv — Schlusskurse, ein Tag je Zeile
    ticker;mic;day;close;currency
    RY;XTSE;2025-12-30;140.10;CAD
    RY;XTSE;2025-12-31;141.55;CAD

    # fx.csv — Wechselkurse, ein Paar und Tag je Zeile
    base;quote;day;rate
    CAD;EUR;2025-12-31;0.6412

Der aktuelle Kurs ist der **jüngste** Eintrag der Historie. Das ist keine
Bequemlichkeit, sondern die ehrliche Aussage einer Datei: Sie kennt keinen
Intraday-Stand, und einen zu behaupten wäre schlimmer, als keinen zu haben.
"""

import csv
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any

from stockinfo_plugin import (
    DailyBar,
    DailyCloseSource,
    DailyRequest,
    DailyResult,
    DailySeries,
    FxRate,
    FxRequest,
    FxResult,
    FxSource,
    ListedIdentity,
    NotFound,
    NotResponsible,
    Quote,
    QuoteRequest,
    QuoteResult,
    QuoteSource,
    Unavailable,
)

MARKET_CLOSE = time(21, 0, tzinfo=timezone.utc)
"""Wann ein Tagesschlusskurs als „gültig ab" gilt.

Eine Datei mit Tagesdaten kennt keine Uhrzeit, der Vertrag verlangt aber einen
Zeitpunkt **mit Zone** — zu Recht: ``17:30`` ist in Toronto ein anderer
Augenblick als in Frankfurt. Statt eine Zeit zu erfinden, die genauer aussieht,
als sie ist, steht hier ein erklärter Ankerpunkt: der späteste Schluss, den die
abgedeckten Börsen haben. Wer stundengenaue Daten braucht, nimmt keine
CSV-Datei.
"""


def _read_rows(path: Path) -> list[dict[str, str]]:
    """Liest eine Semikolon-Tabelle. Wirft `OSError`, wenn die Datei fehlt."""
    with path.open(encoding="utf-8", newline="") as handle:
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(handle, delimiter=";")
        ]


class _FileBacked:
    """Was sich die drei Rollen teilen: eine Datei und ihre Zuständigkeit.

    Ein gemeinsamer Vorfahr und keine dreifache Kopie — die Datei zu finden,
    zu lesen und ihr Fehlen als `Unavailable` zu melden ist an allen drei
    Stellen dieselbe Aufgabe. Er erbt **nicht** von `Source`: Sonst stünde in
    der Ahnenreihe jeder Rolle zweimal derselbe Vertrag.
    """

    default_path = "/data/prices.csv"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """
        Args:
            config: ``path`` — Pfad zur Tabelle.
        """
        super().__init__(config)
        self._path = Path(self._config.get("path", self.default_path))

    def configuration_problem(self) -> str:
        """Ohne Datei gibt es nichts nachzuschlagen — mit Pfad in der Meldung."""
        if self._path.is_file():
            return ""
        return f"Tabelle {self._path} nicht gefunden — Pfad in der Konfiguration prüfen"


class PricesFileDailySource(_FileBacked, DailyCloseSource):
    """Tages-Schlusskurse aus `closes.csv`."""

    name = "prices-file-daily"
    cost = "free"
    api_version = 2
    SUPPORTED_KINDS = frozenset({"listed"})
    # **Ausgeschrieben, weil eine leere Menge "nichts zugesagt" heisst.**
    # Die Tabelle fuehrt Kurse, gleich welcher Gattung — sie liest eine
    # Zeile, keine Fondsdaten. Das steht jetzt da, statt es der leeren
    # Menge zu ueberlassen, die der Host zu Recht als Nichtzusage liest.
    SUPPORTED_TYPES = frozenset(
        {"stock", "etf", "etc", "fund", "crypto", "bond"}
    )
    default_path = "/data/closes.csv"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """
        Args:
            config: ``path`` — Pfad zur Tabelle. ``adjusted`` — ob die Kurse um
                Splits und Ausschüttungen bereinigt sind. Vorgabe ``False``:
                Eine von Hand gepflegte Tabelle ist es fast nie, und die
                freundlichere Annahme wäre hier die gefährlichere.
        """
        super().__init__(config)
        self._adjusted = bool(self._config.get("adjusted", False))

    def handles(self, request: DailyRequest) -> bool:
        """Zuständig, sobald Ticker und MIC gesetzt sind.

        Ob die Tabelle das Papier **führt**, ist eine andere Frage — sie wird
        in `fetch_daily` mit `NotFound` beantwortet. Zuständigkeit hier an der
        Dateizeile festzumachen hieße, für jede Prüfung die Datei zu lesen, und
        `handles` soll nach dem Vertrag nichts kosten.

        Die Tabelle führt Ticker und MIC als Spalten; ein Paar und eine
        ISIN-only-Anleihe sind darin gar nicht adressierbar.
        """
        return isinstance(request.identity, ListedIdentity) and bool(
            request.identity.ticker and request.identity.mic
        )

    def fetch_daily(self, request: DailyRequest) -> DailyResult:
        """Liest die Zeilen des Listings und schneidet den Zeitraum zu."""
        if not self.handles(request):
            return NotResponsible(
                "die Tabelle findet nur Listings über Ticker und MIC"
            )
        try:
            rows = _read_rows(self._path)
        except OSError as exc:
            return Unavailable(f"{self._path} nicht lesbar: {exc}")

        identity = request.identity
        hits = [
            row
            for row in rows
            if row.get("ticker", "").upper() == identity.ticker.upper()
            and row.get("mic", "").upper() == identity.mic.upper()
        ]
        if not hits:
            return NotFound()

        try:
            bars = tuple(
                DailyBar(day=date.fromisoformat(row["day"]), close=float(row["close"]))
                for row in hits
                if _within(date.fromisoformat(row["day"]), request)
            )
        except (KeyError, ValueError) as exc:
            # Eine kaputte Zeile ist ein Fehler der **Datei**, nicht des
            # Papiers. `NotFound` behauptete, das Papier gebe es nicht — und
            # der Betreiber suchte an der falschen Stelle.
            return Unavailable(f"{self._path} enthält eine unlesbare Zeile: {exc}")

        # **Eine Reihe hat genau eine Währung** — die erste Zeile zu nehmen war
        # ein Befund aus Runde 1. Eine von Hand gepflegte Tabelle bekommt über
        # die Jahre Zeilen von verschiedenen Leuten; schreibt einer CAD und ein
        # anderer USD für dasselbe Listing, entstand vorher stillschweigend eine
        # „einheitliche" Reihe mit gemischten Beträgen — und daraus danach ein
        # Kurs, dessen Währung von der Sortierreihenfolge abhing.
        #
        # `Unavailable` und nicht die abweichenden Zeilen wegwerfen: Das ist ein
        # Fehler der Datei, den ein Mensch beheben kann. Eine Teilmenge still zu
        # liefern hieße, ihn zu verstecken.
        currencies = {(row.get("currency") or "").upper() for row in hits}
        if len(currencies) > 1:
            return Unavailable(
                f"{self._path} führt {identity.ticker}/{identity.mic} in mehreren "
                f"Währungen ({', '.join(sorted(currencies))}) — eine Reihe hat "
                "genau eine; bitte die Tabelle bereinigen"
            )

        # Sortiert und doppelfrei, statt sich auf die Reihenfolge in der Datei
        # zu verlassen. Wer von Hand pflegt, hängt neue Zeilen unten an — auch
        # rückwirkende. Der Vertrag verlangt streng aufsteigend, und das ist
        # hier billiger zu erfüllen als zu prüfen.
        unique_days = {bar.day: bar for bar in bars}
        return DailySeries(
            bars=tuple(unique_days[day] for day in sorted(unique_days)),
            currency=currencies.pop(),
            adjusted=self._adjusted,
        )


class PricesFileQuoteSource(_FileBacked, QuoteSource):
    """Der aktuelle Kurs — der jüngste Eintrag derselben Tabelle."""

    name = "prices-file-quote"
    cost = "free"
    api_version = 2
    SUPPORTED_KINDS = frozenset({"listed"})
    # **Ausgeschrieben, weil eine leere Menge "nichts zugesagt" heisst.**
    # Die Tabelle fuehrt Kurse, gleich welcher Gattung — sie liest eine
    # Zeile, keine Fondsdaten. Das steht jetzt da, statt es der leeren
    # Menge zu ueberlassen, die der Host zu Recht als Nichtzusage liest.
    SUPPORTED_TYPES = frozenset(
        {"stock", "etf", "etc", "fund", "crypto", "bond"}
    )
    default_path = "/data/closes.csv"

    def handles(self, request: QuoteRequest) -> bool:
        """Zuständig, sobald eine `listed`-Identität vollständig ist."""
        return isinstance(request.identity, ListedIdentity) and bool(
            request.identity.ticker and request.identity.mic
        )

    def fetch_quote(self, request: QuoteRequest) -> QuoteResult:
        """Nimmt den letzten Schlusskurs als aktuellen Kurs.

        Die Historienquelle macht die Arbeit; hier steht nur die Auswahl. Die
        Zeile ein zweites Mal zu lesen wäre dieselbe Regel an zwei Orten — und
        beim ersten Sonderfall liefen sie auseinander.
        """
        if not self.handles(request):
            return NotResponsible(
                "die Tabelle findet nur Listings über Ticker und MIC"
            )
        series = PricesFileDailySource(self._config).fetch_daily(
            DailyRequest(identity=request.identity)
        )
        if not isinstance(series, DailySeries):
            return series
        if not series.bars:
            return NotFound()
        latest = series.bars[-1]
        return Quote(
            price=latest.close,
            currency=series.currency,
            as_of=datetime.combine(latest.day, MARKET_CLOSE),
        )


class FxFileSource(_FileBacked, FxSource):
    """Wechselkurse aus `fx.csv`."""

    name = "fx-file"
    cost = "free"
    api_version = 2
    default_path = "/data/fx.csv"

    def handles(self, request: FxRequest) -> bool:
        """Zuständig für jedes Paar aus zwei dreistelligen Codes."""
        return len(request.base) == 3 and len(request.quote) == 3

    def fetch_rate(self, request: FxRequest) -> FxResult:
        """Schlägt das Paar nach — und beantwortet die Identität selbst.

        Der Identitätsfall steht **vor** dem Dateizugriff. Eine Währung in sich
        selbst ist genau ``1.0``, und das ist keine Auskunft, die eine Tabelle
        geben müsste: Stünde dort versehentlich ``0.9998``, wäre der Fehler
        durch die ganze App gewandert.
        """
        if not self.handles(request):
            return NotResponsible("nur dreistellige Währungscodes")
        base, quote = request.base.upper(), request.quote.upper()
        if base == quote:
            return FxRate(
                base=base,
                quote=quote,
                rate=1.0,
                as_of=datetime.combine(date.today(), MARKET_CLOSE),
            )
        try:
            rows = _read_rows(self._path)
        except OSError as exc:
            return Unavailable(f"{self._path} nicht lesbar: {exc}")

        hits = [
            row
            for row in rows
            if row.get("base", "").upper() == base
            and row.get("quote", "").upper() == quote
        ]
        if not hits:
            return NotFound()
        try:
            latest_row = max(hits, key=lambda row: date.fromisoformat(row["day"]))
            return FxRate(
                base=base,
                quote=quote,
                rate=float(latest_row["rate"]),
                as_of=datetime.combine(date.fromisoformat(latest_row["day"]), MARKET_CLOSE),
            )
        except (KeyError, ValueError) as exc:
            return Unavailable(f"{self._path} enthält eine unlesbare Zeile: {exc}")


def _within(day: date, request: DailyRequest) -> bool:
    """Liegt der Tag im angefragten Zeitraum? Offene Grenzen zählen als „ja"."""
    if request.start is not None and day < request.start:
        return False
    return not (request.end is not None and day > request.end)


SOURCES = [PricesFileQuoteSource, PricesFileDailySource, FxFileSource]
"""Was die Registry lädt, wenn diese Datei als Einzeldatei-Plugin liegt."""
