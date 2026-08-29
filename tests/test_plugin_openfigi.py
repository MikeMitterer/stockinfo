"""Das OpenFIGI-Plugin ohne Netz — Zuständigkeit, Übersetzung, Vertrag.

Hier steht, was sich **ohne** einen fremden Dienst entscheiden lässt: Wann
das Plugin gar nicht erst fragt, wie es die Antwort des Kern-Resolvers in die
Typen des Vertrags übersetzt, und ob es `ResolverContract` erfüllt. Der echte
Netzfall steht getrennt in `test_plugin_openfigi_integration.py`.

**Die Trennung war ein Befund.** Vorher trug die Integrationsdatei einen
modulweiten Marker, und damit fiel auch der Test mit dem vergifteten Client
unter `-m "not integration"` heraus — obwohl er nie ein Netz brauchte. Ein
Unit-Test, der sich mit den Netzfällen abwählen lässt, fehlt genau dann, wenn
man ihn am dringendsten hätte: ohne Netz.

Das Double unten ist **testlokal und klein**. Es ist keine wiederverwendbare
Fake-Infrastruktur — die zu bauen war der Fehler, den P-09 beschreibt.
"""

from typing import Any

import pytest

from stockinfo_plugin import (
    NotFound,
    NotResponsible,
    Resolved,
    ResolveRequest,
    Unavailable,
)
from stockinfo_plugin.testing import ResolverContract

from app.plugins.openfigi_resolver import OpenFigiResolverPlugin
from app.providers.base import SourceUnavailableError
from app.providers.openfigi_provider import FigiMatch


class FakeFigiClient:
    """Ein `OpenFigiClient`, der antwortet, was der Test ihm sagt.

    Zwei Zeilen Zustand statt einer Fixture-Schicht: Was drei Tests brauchen,
    braucht keinen eigenen Baukasten.
    """

    def __init__(self, answers: dict[tuple[str, str], str | None] | None = None,
                 error: Exception | None = None) -> None:
        """
        Args:
            answers: ``(isin, id_value) → Ticker`` oder ``None`` für „kennt er
                nicht".
            error: Wird geworfen, statt zu antworten.
        """
        self._answers = answers or {}
        self._error = error
        self.calls: list[tuple[str, str, str]] = []

    def map_isin(
        self, isin: str, id_value: str, id_type: str = "micCode"
    ) -> FigiMatch | None:
        """Antwortet nach Tabelle und merkt sich, dass gefragt wurde."""
        self.calls.append((isin, id_value, id_type))
        if self._error is not None:
            raise self._error
        hit = self._answers.get((isin, id_value))
        if not hit:
            return None
        # **Name und Gattung reisen mit, seit T-38 sie zu Pflichtfeldern
        # gemacht hat.** Ein Double, das sie wegließe, prüfte nicht mehr die
        # Übersetzung, sondern nur noch, dass die neue Vollständigkeitsregel
        # anschlägt — und die hat ihre eigenen Tests. Echte OpenFIGI-Treffer
        # tragen beides; ein Treffer *ohne* sie ist der Sonderfall und steht
        # in `test_contract_required_fields.py`.
        return FigiMatch(hit, name=f"{hit} Testpapier", instrument_type="etf")


class PoisonedFigiClient:
    """Ein Client, dessen Benutzung ein Fehler ist."""

    def map_isin(self, *args: Any, **kwargs: Any) -> FigiMatch:
        raise AssertionError("es wurde gefragt, obwohl das nicht passieren darf")


class TestOpenFigiPluginContract(ResolverContract):
    """Der vollständige Resolver-Vertrag — geerbt, nicht geschrieben.

    Der Vertrag prüft unter anderem, dass ein Treffer einen **echten** MIC
    trägt. Genau daran ist die erste Fassung dieses Plugins gescheitert: Sie
    lieferte `Resolved(mic="US")`, und `US` ist ein Sammelcode.
    """

    responsible = ResolveRequest(isin="IE00B3RBWM25", preferred_mic="XETR")
    # **Ohne ISIN**, nicht mit einer kaputten. OpenFIGI deckt alle Märkte ab —
    # für jede gültige ISIN ist diese Quelle zuständig, und ein
    # `not_responsible` mit falscher Prüfziffer würde die Formprüfung messen
    # statt der Zuständigkeit. Genau das verbietet
    # `test_die_eigenen_pruefdaten_sind_gueltige_isins`, und es hat meine
    # erste Fassung dieser Zeile gefunden.
    not_responsible = ResolveRequest(symbol="AAPL", preferred_mic="XETR")
    unknown = ResolveRequest(isin="CA0679011084", preferred_mic="XETR")

    def make_source(self) -> OpenFigiResolverPlugin:
        """Ein Plugin, das genau das eine bekannte Papier kennt."""
        return OpenFigiResolverPlugin(
            client=FakeFigiClient({("IE00B3RBWM25", "XETR"): "VGWL"}),
            home_fallback=False,
        )


def test_eine_falsche_pruefziffer_kostet_kein_ratenlimit() -> None:
    """`handles` weist ab, **bevor** überhaupt jemand gefragt wird.

    Der Client ist hier einer, dessen Benutzung ein Fehler ist. Ohne ihn bewiese
    der Test nur, dass `NotResponsible` herauskommt — nicht, dass unterwegs
    niemand gefragt wurde. Und darum geht es: Ein Ratenlimit, das für eine
    unmögliche Frage draufgeht, fehlt später bei einer echten.
    """
    plugin = OpenFigiResolverPlugin(client=PoisonedFigiClient())
    request = ResolveRequest(isin="US0378331006", preferred_mic="XETR")

    assert plugin.handles(request) is False
    assert isinstance(plugin.resolve(request), NotResponsible)


def test_ein_treffer_wird_mit_ticker_und_mic_uebersetzt() -> None:
    """Der Regelfall — und die Felder, die der Vertrag verlangt."""
    client = FakeFigiClient({("IE00B3RBWM25", "XETR"): "VGWL"})
    plugin = OpenFigiResolverPlugin(client=client, home_fallback=False)

    answer = plugin.resolve(ResolveRequest(isin="IE00B3RBWM25", preferred_mic="XETR"))

    assert isinstance(answer, Resolved), answer
    assert (answer.identity.ticker, answer.identity.mic) == ("VGWL", "XETR")
    assert answer.identity.isin == "IE00B3RBWM25"


def test_ein_sammelcode_erzeugt_keinen_treffer_mit_erfundenem_mic() -> None:
    """**Der Befund aus Runde 4, und der Grund für diese ganze Nacharbeit.**

    `US` fasst sechs Handelsplätze zusammen. OpenFIGI beantwortet darauf
    „welcher Ticker", nicht „welche Börse" — ohne echten MIC ist die Identität
    unvollständig. Der Kern-Resolver fragt deshalb **gar nicht erst**, und
    genau das prüft dieser Test mit: Der Client darf nicht benutzt werden.

    Meine erste Fassung umging den Kern-Resolver, fragte trotzdem, bekam
    `AAPL` und lieferte `Resolved(mic="US")` — einen Treffer, dessen MIC keiner
    ist. `ResolverContract` verbietet das, und zwar zu Recht.
    """
    plugin = OpenFigiResolverPlugin(client=PoisonedFigiClient(), home_fallback=False)

    answer = plugin.resolve(ResolveRequest(isin="US0378331005", preferred_mic="US"))

    assert isinstance(answer, NotFound), answer


def test_ein_ausfall_bleibt_ein_ausfall() -> None:
    """`Unavailable`, nicht `NotFound` — daran hängt, ob die App erneut fragt.

    Diese Unterscheidung hat den Kern-Resolver einmal einen Umbau gekostet:
    Solange beides als ``None`` zurückkam, wurde aus einem 502 ein 404, und die
    App hörte auf zu fragen. Ein Plugin, das sie wieder einebnet, macht den
    Fehler ein zweites Mal.
    """
    plugin = OpenFigiResolverPlugin(
        client=FakeFigiClient(error=SourceUnavailableError("openfigi: Netz weg")),
        home_fallback=False,
    )

    answer = plugin.resolve(ResolveRequest(isin="IE00B3RBWM25", preferred_mic="XETR"))

    assert isinstance(answer, Unavailable), answer
    assert "Netz weg" in answer.error


def test_ein_unbekanntes_papier_ist_not_found() -> None:
    """Der Dienst kennt es nicht — das ist eine Antwort, keine Störung."""
    plugin = OpenFigiResolverPlugin(client=FakeFigiClient(), home_fallback=False)

    answer = plugin.resolve(ResolveRequest(isin="CA0679011084", preferred_mic="XETR"))

    assert isinstance(answer, NotFound), answer


def test_die_heimatboerse_wird_gefragt_wenn_die_bevorzugte_nichts_hat() -> None:
    """Die Kaskade aus T-18 — geerbt, nicht nachgebaut.

    Das Plugin enthält davon keine Zeile; es reicht `home_fallback` durch. Der
    Test steht trotzdem hier, weil er belegt, dass die Kaskade **über das
    Plugin hinweg** noch wirkt — ein Adapter, der sie unterwegs verliert, wäre
    von außen nicht zu unterscheiden.
    """
    client = FakeFigiClient({("CA78012H5675", "XTSE"): "RY"})
    plugin = OpenFigiResolverPlugin(client=client, home_fallback=True)

    answer = plugin.resolve(ResolveRequest(isin="CA78012H5675", preferred_mic="XETR"))

    assert isinstance(answer, Resolved), answer
    assert (answer.identity.ticker, answer.identity.mic) == ("RY", "XTSE")
    assert [call[1] for call in client.calls] == ["XETR", "XTSE"], (
        "erst die bevorzugte Börse, dann die Heimatbörse aus dem ISIN-Präfix"
    )


@pytest.mark.parametrize("key", ["", "geheim"])
def test_die_quelle_meldet_kein_konfigurationsproblem(key: str) -> None:
    """Sie läuft mit und ohne Schlüssel — und sagt in beiden Fällen nichts.

    Eine Diagnose, die auch im Normalfall spricht, wird nach dem dritten Mal
    überlesen und fehlt dann dort, wofür sie gebaut wurde.
    """
    plugin = OpenFigiResolverPlugin({"api_key": key}, client=FakeFigiClient())

    assert plugin.configuration_problem() == ""
    assert plugin.is_configured() is True
