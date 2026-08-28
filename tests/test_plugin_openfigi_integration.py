"""Das OpenFIGI-Plugin gegen die **echte** API.

Kein Mock, keine Aufzeichnung: Der Test fragt den Dienst, den die App auch im
Betrieb fragt. Was er damit belegt, kann kein Double belegen — dass das
Anfrageformat noch stimmt, dass die Antwort noch so aussieht wie gedacht, und
dass die Übersetzung in die Rollen des Vertrags trägt.

Der Preis dafür ist ehrlich zu nennen: Der Test hängt an einem fremden Dienst
und an dessen Ratenlimit. Er trägt deshalb den Marker `integration` und lässt
sich mit ``-m "not integration"`` abwählen — der Marker ist eine Möglichkeit,
kein Vorschlag, ihn zu überspringen.

    pytest tests/test_plugin_openfigi_integration.py     # fragt OpenFIGI
    pytest -m "not integration"                          # ohne fremde Dienste

**Die Golden-Werte stammen nicht aus dem Dienst.** ``AAPL`` an ``XNAS`` und
``VGWL`` an ``XETR`` sind nachgeschlagen und hier hingeschrieben. Käme der
Erwartungswert aus derselben Antwort, die geprüft wird, prüfte der Test nur,
ob der Dienst mit sich selbst übereinstimmt.
"""

import pytest

from stockinfo_plugin import NotFound, NotResponsible, Resolved, ResolveRequest

from app.plugins.openfigi_resolver import OpenFigiResolver

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def resolver() -> OpenFigiResolver:
    """Ein Resolver ohne Schlüssel — so, wie ihn ein Beiträger auch hat."""
    return OpenFigiResolver()


@pytest.mark.parametrize(
    ("isin", "mic", "ticker"),
    [
        # `US` ist der Sammelcode der eigenen Tabelle und **kein** MIC —
        # gemessen: Apple ist über `micCode=XNAS` bei OpenFIGI nicht zu
        # finden, über `exchCode=US` schon.
        ("US0378331005", "US", "AAPL"),
        ("IE00B3RBWM25", "XETR", "VGWL"),
    ],
)
def test_ein_bekanntes_papier_wird_aufgeloest(
    resolver: OpenFigiResolver, isin: str, mic: str, ticker: str
) -> None:
    """Zwei Papiere über zwei verschiedene Anfragewege.

    Mit nur einem Fall bliebe offen, ob die Börse überhaupt in die Anfrage
    eingeht: Ein Plugin, das ``preferred_mic`` verwirft und irgendein Listing
    zurückgibt, bestünde einen Einzelfall mühelos. Und die beiden Fälle nehmen
    **verschiedene** Wege — `micCode` und `exchCode` —, was ein Plugin, das
    `figi_lookup` umgeht, sofort auffliegen ließe.
    """
    answer = resolver.resolve(ResolveRequest(isin=isin, preferred_mic=mic))

    assert isinstance(answer, Resolved), answer
    assert answer.ticker == ticker
    assert answer.mic == mic
    assert answer.isin == isin


def test_ein_papier_das_die_boerse_nicht_fuehrt_ist_not_found(
    resolver: OpenFigiResolver,
) -> None:
    """Der gemessene Anlass für `examples/canada_file.py`.

    Die Royal Bank of Canada ist an Xetra über OpenFIGI nicht zu finden — genau
    deshalb gibt es die von Hand gepflegte Tabelle als zweiten Weg. Der Test
    hält fest, dass daraus `NotFound` wird und **nicht** `Unavailable`: An
    dieser Unterscheidung hängt, ob die App eine andere Quelle fragt oder es
    später noch einmal versucht.
    """
    answer = resolver.resolve(
        ResolveRequest(isin="CA78012H5675", preferred_mic="XETR")
    )

    assert isinstance(answer, NotFound), answer


def test_eine_falsche_pruefziffer_kostet_kein_ratenlimit() -> None:
    """`handles` weist ab, bevor überhaupt jemand gefragt wird.

    Der Client ist hier einer, dessen Benutzung ein Fehler ist. Ohne ihn bewiese
    der Test nur, dass `NotResponsible` herauskommt — nicht, dass unterwegs
    niemand gefragt wurde. Und das ist die Aussage, um die es geht: Ein
    Ratenlimit, das für eine unmögliche Frage draufgeht, fehlt später bei einer
    echten.
    """

    class PoisonedClient:
        """Ein Client, der nicht gefragt werden darf."""

        def map_isin(self, *args: object, **kwargs: object) -> str:
            raise AssertionError("es wurde gefragt, obwohl handles() ablehnt")

    resolver = OpenFigiResolver(client=PoisonedClient())
    request = ResolveRequest(isin="US0378331006", preferred_mic="XNAS")

    assert resolver.handles(request) is False
    assert isinstance(resolver.resolve(request), NotResponsible)
