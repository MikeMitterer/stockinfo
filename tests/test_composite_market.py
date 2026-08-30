"""Die konfigurierte Reihenfolge wird wirklich abgefragt.

`sources.yaml` erlaubt für `quotes`, `daily` und `fx` mehrere Quellen. Eine
Anleihe ohne Online-Kurs muss das dahinter konfigurierte `yaml-file` erreichen.

**Zwei Aussagen, und die zweite ist die schwerere.** Dass ein Treffer gewinnt,
ist leicht zu prüfen und war nie das Problem: Bei nur einer gefragten Quelle
gewinnt sie immer. Die Zusage, an der es hing, lautet *„ein Fehlschlag fällt
weiter"* — und ein Test dafür braucht eine zweite Quelle, die tatsächlich
gefragt wird.

Deshalb zählt jedes Double seine Aufrufe. Ohne diese Zählung wäre „die erste
gewinnt" auch dann grün, wenn die zweite gar nicht existierte.
"""

import pytest

from app.providers.base import RawQuote, ResolvedInstrument
from app.providers.composite_market import (
    CompositeDailyCloseProvider,
    CompositeQuoteProvider,
)

_INSTRUMENT = ResolvedInstrument(
    symbol="EUNL.DE", ticker="EUNL", mic="XETR", isin="IE00B4L5Y983"
)


def _quote(price: float) -> RawQuote:
    return RawQuote(
        symbol="EUNL.DE",
        name="iShares Core MSCI World",
        price=price,
        quote_time="2026-08-30T10:00:00+00:00",
        currency="EUR",
        type="etf",
    )


class _QuoteSource:
    """Eine Kursquelle, die eine feste Antwort gibt — und mitschreibt.

    Das Protokoll für die Aufrufzählung: Ohne sie ließe sich nicht
    unterscheiden, ob eine Quelle nicht geantwortet oder ob niemand sie
    gefragt hat.
    """

    def __init__(self, name: str, answer: RawQuote | None) -> None:
        self.name = name
        self._answer = answer
        self.calls = 0

    def fetch_quote(self, instrument: ResolvedInstrument) -> RawQuote | None:
        self.calls += 1
        return self._answer


class _DailySource:
    """Dasselbe für die Historie."""

    def __init__(self, name: str, answer: list[dict] | None) -> None:
        self.name = name
        self._answer = answer
        self.calls = 0

    def fetch_daily_closes(
        self,
        symbol: str,
        start: str | None = None,
        *,
        identity: object | None = None,
        instrument_type: str | None = None,
    ) -> list[dict] | None:
        self.calls += 1
        return self._answer


# ─── Kurse ────────────────────────────────────────────────────────────────────


def test_der_erste_treffer_gewinnt() -> None:
    """Wer zuerst liefert, gewinnt — und danach wird niemand mehr gefragt.

    Die zweite Zusicherung ist die eigentliche: Eine Kaskade, die alle Quellen
    fragt und dann auswählt, kostet bei jedem Abruf ein Ratenlimit für eine
    Antwort, die niemand verwendet.
    """
    first = _QuoteSource("online", _quote(128.21))
    second = _QuoteSource("yaml-file", _quote(111.11))

    answer = CompositeQuoteProvider(first, second).fetch_quote(_INSTRUMENT)

    assert answer.price == 128.21
    assert second.calls == 0, "die zweite Quelle wurde trotz Treffer gefragt"


def test_ein_fehlschlag_faellt_weiter() -> None:
    """**Die Zusage, an der es hing.** Ohne Treffer kommt die nächste dran."""
    first = _QuoteSource("online", None)
    second = _QuoteSource("yaml-file", _quote(111.11))

    answer = CompositeQuoteProvider(first, second).fetch_quote(_INSTRUMENT)

    assert answer.price == 111.11, "die Datei hinter der stummen Quelle kam nicht dran"
    assert first.calls == 1 and second.calls == 1


def test_ohne_jeden_treffer_bleibt_es_beim_fehlschlag() -> None:
    """Alle gefragt, keine geliefert — dann ist ``None`` die ehrliche Antwort.

    Der Aufrufer bekommt damit denselben Fall wie bei einer einzelnen Quelle,
    und sein vorhandener Rückfall auf den gespeicherten Stand greift
    unverändert.
    """
    sources = [_QuoteSource("a", None), _QuoteSource("b", None)]

    assert CompositeQuoteProvider(*sources).fetch_quote(_INSTRUMENT) is None
    assert [source.calls for source in sources] == [1, 1]


def test_die_kaskade_traegt_den_namen_der_ersten_quelle() -> None:
    """Ein Name muss sein — das Protokoll verlangt ihn.

    Der Name der Kaskade ist der der ersten Quelle und nicht etwa „composite":
    Wo er auftaucht, soll ein Betreiber eine Quelle wiedererkennen, die er
    konfiguriert hat. Welche Quelle eine **einzelne** Antwort geliefert hat,
    steht ohnehin an der Antwort und nicht an der Kette.
    """
    assert CompositeQuoteProvider(
        _QuoteSource("online", None), _QuoteSource("yaml-file", None)
    ).name == "online"


# ─── Tagesreihen ──────────────────────────────────────────────────────────────


def test_die_erste_reihe_gewinnt() -> None:
    first = _DailySource("online", [{"day": "2026-08-27", "close": 128.21}])
    second = _DailySource("yaml-file", [{"day": "2026-08-27", "close": 111.11}])

    answer = CompositeDailyCloseProvider(first, second).fetch_daily_closes("EUNL.DE")

    assert answer == [{"day": "2026-08-27", "close": 128.21}]
    assert second.calls == 0


def test_eine_leere_reihe_ist_ein_treffer_und_stoppt_die_kette() -> None:
    """**Der Unterschied, an dem der ganze Vertrag hängt.**

    ``[]`` heißt „nachgesehen, in diesem Zeitraum nichts"; ``None`` heißt
    „konnte nicht nachsehen". Beides gleich zu behandeln wäre bequem und
    falsch: Die leere Reihe ist eine belastbare Auskunft, und die nächste
    Quelle danach zu fragen hieße, eine Antwort zu suchen, die es nicht gibt —
    im Zweifel eine **andere**, weil eine zweite Quelle für denselben Zeitraum
    Werte führen kann, die die erste bewusst nicht hat.
    """
    first = _DailySource("online", [])
    second = _DailySource("yaml-file", [{"day": "2026-08-27", "close": 111.11}])

    answer = CompositeDailyCloseProvider(first, second).fetch_daily_closes("EUNL.DE")

    assert answer == []
    assert second.calls == 0, "die leere Reihe wurde als Fehlschlag behandelt"


def test_ein_ausfall_faellt_weiter() -> None:
    first = _DailySource("online", None)
    second = _DailySource("yaml-file", [{"day": "2026-08-27", "close": 111.11}])

    answer = CompositeDailyCloseProvider(first, second).fetch_daily_closes("EUNL.DE")

    assert answer == [{"day": "2026-08-27", "close": 111.11}]
    assert first.calls == 1 and second.calls == 1


def test_ohne_jede_reihe_bleibt_es_beim_ausfall() -> None:
    """Nach dem Gesamtausfall bleibt ``None`` — und das Wasserzeichen stehen.

    `DailyCloseSync` unterscheidet daran, ob es seinen Stand vorrücken darf.
    Käme hier ``[]`` heraus, hielte die App einen Ausfall für eine Auskunft
    und rückte vor, ohne etwas geholt zu haben.
    """
    sources = [_DailySource("a", None), _DailySource("b", None)]

    assert CompositeDailyCloseProvider(*sources).fetch_daily_closes("X") is None
    assert [source.calls for source in sources] == [1, 1]


def test_die_anfrage_reist_unveraendert_weiter() -> None:
    """Jede Quelle bekommt dieselbe Frage — samt Identität und Gattung.

    Ohne sie fragte die zweite Quelle etwas anderes als die erste: Das
    Das Anbieter-Symbol allein genügt nicht, weil die fünf US-Börsen dieselbe
    Schreibweise führen.
    """
    seen: list[tuple] = []

    class _Recording(_DailySource):
        def fetch_daily_closes(self, symbol, start=None, *, identity=None,
                               instrument_type=None):
            seen.append((symbol, start, identity, instrument_type))
            return super().fetch_daily_closes(
                symbol, start, identity=identity, instrument_type=instrument_type
            )

    CompositeDailyCloseProvider(
        _Recording("a", None), _Recording("b", [])
    ).fetch_daily_closes(
        "EUNL.DE", "2026-08-01", identity=None, instrument_type="etf"
    )

    assert seen == [
        ("EUNL.DE", "2026-08-01", None, "etf"),
        ("EUNL.DE", "2026-08-01", None, "etf"),
    ]


# ─── Was für beide gilt ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "composite", [CompositeQuoteProvider, CompositeDailyCloseProvider]
)
def test_eine_kaskade_ohne_quellen_ist_ein_fehler(composite: type) -> None:
    """Eine leere Kette antwortet nie — und soll das beim Bauen sagen.

    Stillschweigend ``None`` zu liefern hieße, einen Konfigurationsfehler als
    Ausfall auszugeben: Der Betreiber suchte beim Anbieter nach einer Ursache,
    die in seiner `sources.yaml` steht.
    """
    with pytest.raises(ValueError, match="ohne Quellen"):
        composite()
