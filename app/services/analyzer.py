"""On-Demand-Diagnose — misst, was die **konfigurierte Kette** wirklich tut.

Bewusst cache-umgehend: Der Zweck ist die Messung des echten Pfades aus der
Server-Umgebung. Jede Quelle ist best-effort — ein Fehler bricht die Analyse
nicht ab, sondern wird erfasst.

**Gemessen werden die Quellen, entschieden wird woanders.** Der Analyzer legt
eine Stoppuhr um jede Quelle und lässt danach die **vorhandenen** Kaskaden
laufen. Er baut ihre Regel nicht nach: „erste gültige Antwort gewinnt" steht in
`CompositeQuoteProvider` und `CompositeDailyCloseProvider`, und eine zweite
Fassung hier wäre die Stelle, an der beide beim nächsten Nachtrag
auseinanderlaufen. Was der Analyzer weiß, weiß er deshalb aus der Beobachtung:
Eine Quelle, die keine Messung hinterlässt, wurde nicht gefragt.
"""

import time
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from stockinfo_plugin.types import NotFound, NotResponsible, Unavailable, Unsupported

from app.models import AnalyzeResult, AnalyzeStage
from app.providers.base import ResolvedInstrument, SourceAnswer, declared_name
from app.resolver import CompositeResolver
from app.providers.composite_etf import CompositeEtfEnricher
from app.providers.composite_market import (
    CompositeDailyCloseProvider,
    CompositeQuoteProvider,
)

# Die Rollen, die eine Frage zu **einem Papier** beantworten, in der
# Reihenfolge, in der die App sie stellt. `fx` fehlt mit Absicht: Ein
# Wechselkurs gehört zu einem Währungspaar, nicht zu einem Wertpapier.
ROLES = ("resolvers", "quotes", "daily", "etf_meta")

# Wie weit zurück die Tagesreihe angefragt wird. Ein Jahr plus Puffer — dieselbe
# Spanne wie bisher, damit die Messung vergleichbar bleibt.
_DAILY_WINDOW_DAYS = 370


@dataclass
class _Record:
    """Eine Messung — was eine Quelle in einer Rolle getan hat."""

    role: str
    source: str
    seconds: float
    status: str
    detail: str | None = None


class _Stopwatch:
    """Sammelt die Messungen eines einzelnen Analyselaufs.

    **Ein Objekt je Lauf, kein Zustand am Dienst.** Zwei gleichzeitige Anfragen
    schrieben sich sonst gegenseitig die Messwerte um — derselbe Grund, aus dem
    `RawQuote.source` an der Antwort reist und nicht am Anbieter hängt.
    """

    def __init__(self) -> None:
        self.records: list[_Record] = []

    def measure(self, role: str, source: str, call: Any) -> Any:
        """Führt ``call`` aus, hält Dauer und Ausgang fest und reicht durch.

        Args:
            role: Die Rolle, in der die Quelle gerade steht.
            source: Ihr Name aus der Konfiguration.
            call: Die aufzurufende Funktion ohne Argumente.

        Returns:
            Was die Quelle geliefert hat — unverändert. Wirft sie, wird das
            erfasst und statt der Antwort ein „gestört" **in der Form dieser
            Rolle** weitergereicht (`_BROKEN`): Die Kaskade fällt dann weiter,
            wie sie es zusagt, statt an einer unpassenden Ersatzantwort
            abzubrechen und die übrigen Quellen ungefragt zu lassen.
        """
        start = time.perf_counter()
        try:
            value = call()
        except Exception as exc:  # noqa: BLE001 — eine Diagnose erfasst Fehler
            self.records.append(
                _Record(role, source, _elapsed(start), "error", type(exc).__name__)
            )
            return _BROKEN[role]()
        seconds = _elapsed(start)
        status, detail = _classify(value)
        self.records.append(_Record(role, source, seconds, status, detail))
        return value


class _Timed:
    """Eine Quelle mit Stoppuhr — sonst unverändert.

    Die Kaskade merkt nichts davon: Sie sieht denselben Namen und dieselben
    Methoden. Gemessen werden nur die Abrufe, nicht `handles()` — das ist eine
    Frage an den Speicher, keine an die Außenwelt.
    """

    def __init__(
        self, stopwatch: _Stopwatch, role: str, inner: Any, measured: set[str]
    ) -> None:
        self._stopwatch = stopwatch
        self._role = role
        self._inner = inner
        self._measured = measured
        self.name = declared_name(inner) or "?"

    def __getattr__(self, item: str) -> Any:
        attribute = getattr(self._inner, item)
        if item not in self._measured or not callable(attribute):
            return attribute

        def timed(*args: Any, **kwargs: Any) -> Any:
            return self._stopwatch.measure(
                self._role, self.name, lambda: attribute(*args, **kwargs)
            )

        return timed


def _elapsed(start: float) -> float:
    """Vergangene Zeit seit ``start`` in Sekunden, auf 3 Stellen gerundet."""
    return round(time.perf_counter() - start, 3)


_UNREACHABLE = "Quelle nicht erreichbar"


def _classify(value: Any) -> tuple[str, str | None]:
    """Was die Antwort einer Quelle bedeutet — Status und Grund.

    **Der Unterschied zwischen `empty` und `error` ist der Zweck dieses
    Endpunkts.** „Nichts gefunden" und „konnte nicht nachsehen" führen zu
    verschiedenen nächsten Schritten; sie beide grau zu färben nähme der
    Diagnose genau die Auskunft, für die es sie gibt. Die Tabelle stand vor
    T-46 schon einmal hier und ist beim Umbau auf Rollen verloren gegangen:

    | Antwort | Status | Detail |
    |---|---|---|
    | `ResolvedInstrument` | `ok` | das Symbol |
    | `Unsupported` | `empty` | die **Gattung** — erkannt, nur nicht geführt |
    | `Unavailable` | **`error`** | der genannte Grund |
    | `NotResponsible` | `empty` | sein `reason`, falls einer dasteht |
    | `NotFound` | `empty` | — nachgesehen, nichts da |
    | `SourceAnswer` ohne Wert, `disturbed` | **`error`** | Störung der Quelle |
    | `SourceAnswer` ohne Wert | `empty` | — |
    | `SourceAnswer` mit Reihe | `ok` | die Zeilenzahl |

    **`Unsupported` ist `empty` und nicht `error`** (T-31, Matrix `#6`): Die
    Kette hat einwandfrei gearbeitet — sie hat das Papier sogar erkannt. Ein
    `error` schickte den Betreiber auf die Suche nach einer Störung, die es
    nicht gibt.
    """
    if isinstance(value, ResolvedInstrument):
        return "ok", value.symbol
    if isinstance(value, Unsupported):
        return "empty", f"Gattung {value.instrument_type} wird nicht geführt"
    if isinstance(value, Unavailable):
        return "error", value.error or _UNREACHABLE
    if isinstance(value, NotResponsible):
        return "empty", value.reason or None
    if isinstance(value, NotFound):
        return "empty", None
    if isinstance(value, SourceAnswer):
        if not value.is_hit:
            return ("error", _UNREACHABLE) if value.disturbed else ("empty", None)
        rows = value.value
        return "ok", (f"{len(rows)} Zeilen" if isinstance(rows, list) else None)
    if value is None or (isinstance(value, (list, tuple)) and not value):
        return "empty", None
    return "ok", None


# Welche Methode je Rolle die Außenwelt fragt — und damit gemessen wird.
_MEASURED = {
    "resolvers": {"resolve_isin", "resolve_symbol"},
    "quotes": {"fetch_quote"},
    "daily": {"fetch_daily_closes"},
    "etf_meta": {"fetch_etf"},
}

# Wie eine **kaputte** Quelle in ihrer Rolle aussieht.
#
# **Eine Diagnose darf die Kette nicht anders laufen lassen als der Betrieb.**
# Wirft eine Quelle, gab die Stoppuhr bisher schlicht ``None`` zurück — in der
# Rolle `daily` erwartet die Kaskade dort aber eine `SourceAnswer` und stürzte
# an `None.is_hit` ab. Die zweite Quelle wurde dann nie gefragt, obwohl die
# Kaskade genau das zusagt. Der Ersatz ist deshalb keine Kaskadenregel, sondern
# eine Formfrage: „gestört" in der Sprache der jeweiligen Rolle.
_BROKEN = {
    "resolvers": lambda: Unavailable(error=_UNREACHABLE),
    "quotes": lambda: None,
    "daily": lambda: SourceAnswer(disturbed=True),
    "etf_meta": lambda: None,
}


class QuoteAnalyzer:
    """Misst, was die konfigurierte Kette für **ein** Papier tut."""

    def __init__(self, chains: dict[str, list]) -> None:
        """
        Args:
            chains: Rolle → einsatzbereite Quellen, in Rangfolge. Genau die
                Listen, aus denen der Betrieb seine Kaskaden baut; der Analyzer
                bekommt sie herein, statt sie sich zu besorgen — sonst misst er
                eine zweite Konfiguration.
        """
        self._chains = chains

    def analyze(
        self, *, isin: str | None = None, symbol: str | None = None
    ) -> AnalyzeResult:
        """Fragt die Kette Rolle für Rolle und liefert die Messung.

        **Kein Abbruch bei einem Fehlschlag.** Eine Rolle, die nichts liefert,
        ist selbst eine Auskunft — und die folgenden Rollen sagen dann, ob sie
        ohne sie überhaupt arbeiten können.

        Args:
            isin: Die ISIN, falls danach gefragt wurde.
            symbol: Das Symbol, falls danach gefragt wurde.

        Returns:
            Je konfigurierte Quelle und Rolle eine Zeile. Quellen, die die
            Kaskade nicht mehr fragen musste, stehen als ``skipped`` darin.
        """
        watch = _Stopwatch()
        start_total = time.perf_counter()

        resolved = self._resolve(watch, isin=isin, symbol=symbol)
        instrument = resolved if isinstance(resolved, ResolvedInstrument) else None

        if instrument is not None:
            self._quotes(watch, instrument)
            self._daily(watch, instrument)
            self._etf_meta(watch, instrument)

        return AnalyzeResult(
            symbol=(instrument.symbol if instrument else (symbol or isin or "")),
            isin=(instrument.isin if instrument else isin),
            total=_elapsed(start_total),
            stages=self._stages(watch),
        )

    # ─── Die vier Rollen ──────────────────────────────────────────────────────

    def _resolve(self, watch: _Stopwatch, *, isin: str | None, symbol: str | None) -> Any:
        """Die Auflösung — über die **vorhandene** Resolver-Kaskade."""
        chain = self._wrap(watch, "resolvers")
        if not chain:
            return None
        resolver = CompositeResolver(*chain)
        if isin:
            return _guarded(lambda: resolver.resolve_isin(isin))
        if symbol:
            return _guarded(lambda: resolver.resolve_symbol(symbol))
        return None

    def _quotes(self, watch: _Stopwatch, instrument: ResolvedInstrument) -> None:
        chain = self._wrap(watch, "quotes")
        if chain:
            _guarded(lambda: CompositeQuoteProvider(*chain).fetch_quote(instrument))

    def _daily(self, watch: _Stopwatch, instrument: ResolvedInstrument) -> None:
        chain = self._wrap(watch, "daily")
        if not chain:
            return
        start = (date.today() - timedelta(days=_DAILY_WINDOW_DAYS)).isoformat()
        _guarded(
            lambda: CompositeDailyCloseProvider(*chain).fetch_daily_closes(
                instrument.symbol,
                start,
                identity=instrument.identity(),
                instrument_type=instrument.type,
            )
        )

    def _etf_meta(self, watch: _Stopwatch, instrument: ResolvedInstrument) -> None:
        chain = self._wrap(watch, "etf_meta")
        if chain:
            _guarded(
                lambda: CompositeEtfEnricher(*chain).fetch_etf(
                    instrument.isin,
                    instrument.symbol,
                    exchange=instrument.exchange,
                    currency=instrument.currency,
                    identity=instrument.identity(),
                    instrument_type=instrument.type,
                )
            )

    # ─── Zusammensetzen ───────────────────────────────────────────────────────

    def _wrap(self, watch: _Stopwatch, role: str) -> list:
        """Legt die Stoppuhr um jede Quelle dieser Rolle."""
        return [
            _Timed(watch, role, source, _MEASURED[role])
            for source in self._chains.get(role, [])
        ]

    def _stages(self, watch: _Stopwatch) -> list[AnalyzeStage]:
        """Die Messungen — und für jede ungefragte Quelle eine `skipped`-Zeile.

        **Die Reihenfolge ist die der Konfiguration**, nicht die der Messung:
        Ein Betreiber liest hier seine eigene Kette und soll sie wiedererkennen.
        """
        seen = {(record.role, record.source): record for record in watch.records}
        stages: list[AnalyzeStage] = []
        for role in ROLES:
            for source in self._chains.get(role, []):
                name = declared_name(source) or "?"
                record = seen.get((role, name))
                stages.append(
                    AnalyzeStage(
                        role=role,
                        source=name,
                        seconds=record.seconds if record else 0.0,
                        status=record.status if record else "skipped",
                        detail=record.detail if record else None,
                    )
                )
        return stages


def _guarded(call: Any) -> Any:
    """Führt einen Kaskadenaufruf aus; ein Fehler beendet die Analyse nicht.

    Die einzelne Quelle ist bereits gemessen — was hier ankommt, ist ein
    Fehler der Kaskade selbst. Ihn durchzulassen hieße, die übrigen Rollen
    ungemessen zu lassen, obwohl an ihnen nichts falsch ist.
    """
    try:
        return call()
    except Exception:  # noqa: BLE001 — eine Diagnose bricht nicht ab
        return None
