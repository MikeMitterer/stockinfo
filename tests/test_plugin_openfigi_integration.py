"""Das OpenFIGI-Plugin gegen die **echte** API.

Hier stehen **drei** Fälle, und jeder von ihnen fasst den Dienst wirklich an.
Alles, was sich ohne fremden Dienst entscheiden lässt — Zuständigkeit,
Übersetzung, der geerbte `ResolverContract`, der Sammelcode-Fall —, steht in
`test_plugin_openfigi.py` und läuft auch dann, wenn diese Datei abgewählt ist.

Der Sammelcode-Fall gehörte ausdrücklich **nicht** hierher: Der Kern-Resolver
bricht bei `US` ab, bevor der Client an der Reihe ist. Ein Test unter dem
Marker `integration`, der gar nichts fragt, macht die Angabe „drei echte
Netzfälle" zu einer Behauptung.

    pytest tests/test_plugin_openfigi_integration.py   # fragt OpenFIGI
    pytest -m "not integration"                        # ohne fremde Dienste

Was ein Integrationstest belegt und kein Double belegen kann: dass das
Anfrageformat noch stimmt, dass die Antwort noch so aussieht wie gedacht, und
dass die Übersetzung in die Rollen trägt. Der Preis ist die Abhängigkeit vom
Dienst und seinem Ratenlimit — deshalb der Marker.

**Die Golden-Werte stammen nicht aus dem Dienst.** `VGWL` an `XETR` und `RY` an
`XTSE` sind nachgeschlagen und hier hingeschrieben. Käme der Erwartungswert aus
derselben Antwort, die geprüft wird, prüfte der Test nur, ob der Dienst mit
sich selbst übereinstimmt.
"""

import pytest

from stockinfo_plugin import NotFound, Resolved, ResolveRequest

from app.plugins.openfigi_resolver import OpenFigiResolverPlugin

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def plugin() -> OpenFigiResolverPlugin:
    """Ein Plugin ohne Schlüssel — so, wie ein Beiträger es auch hat."""
    return OpenFigiResolverPlugin()


def test_ein_papier_an_der_bevorzugten_boerse(plugin: OpenFigiResolverPlugin) -> None:
    """Der Regelfall über einen echten MIC.

    `XETR` ist eine einzelne Börse, und OpenFIGI beantwortet die Frage
    vollständig: Ticker **und** Handelsplatz. Genau darauf besteht der Vertrag.
    """
    answer = plugin.resolve(ResolveRequest(isin="IE00B3RBWM25", preferred_mic="XETR"))

    assert isinstance(answer, Resolved), answer
    assert (answer.identity.ticker, answer.identity.mic) == ("VGWL", "XETR")
    assert answer.identity.isin == "IE00B3RBWM25"


def test_die_kaskade_auf_die_heimatboerse(plugin: OpenFigiResolverPlugin) -> None:
    """Die Kaskade aus T-18, am echten Dienst.

    Die Royal Bank of Canada hat an Xetra kein Listing, an Toronto schon. Das
    Emissionsland steckt im ISIN-Präfix — niemand muss es konfigurieren. Der
    Test belegt, dass diese Kaskade **über das Plugin hinweg** noch wirkt und
    nicht unterwegs verloren geht.

    **Die Stammaktie `CA7800871021`, nicht die Vorzugsaktie `CA78012H5675`.**
    Der Unterschied ist gemessen: Für die Vorzugsaktie liefert OpenFIGI an
    Toronto den Bloomberg-Bezeichner ``RY V3.65 PERP BB``, den
    `_is_yahoo_compatible_symbol` zu Recht verwirft — daraus wird `NotFound`,
    und genau dafür gibt es die von Hand gepflegte Tabelle in
    `examples/canada_file.py`. Mit ihr hätte dieser Test die Kaskade nie
    erreicht, sondern den Symbolfilter gemessen.
    """
    answer = plugin.resolve(ResolveRequest(isin="CA7800871021", preferred_mic="XETR"))

    assert isinstance(answer, Resolved), answer
    assert (answer.identity.ticker, answer.identity.mic) == ("RY", "XTSE")


def test_ein_papier_das_keine_der_gefragten_boersen_fuehrt(
    plugin: OpenFigiResolverPlugin,
) -> None:
    """`NotFound`, **nicht** `Unavailable`.

    Barrick Gold ist eine gültige kanadische ISIN, die OpenFIGI an Xetra nicht
    führt. An dieser Unterscheidung hängt, ob die App eine andere Quelle fragt
    oder es später noch einmal versucht — sie war der Anlass für T-20.

    Die Zusage ist **fest**: `NotFound`. Ein Test, der sich an jede Antwort
    anpasst — „entweder Treffer oder nicht" —, prüft nichts. Führt OpenFIGI
    das Papier eines Tages doch, soll er laut fehlschlagen; dann ist die
    Erwartung nachzuziehen, und das ist eine Information.
    """
    answer = plugin.resolve(
        ResolveRequest(isin="CA0679011084", preferred_mic="XETR")
    )

    assert isinstance(answer, NotFound), answer
