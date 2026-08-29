"""Pflichtfelder im Plugin-Vertrag — die Orakel vor der Umsetzung (T-38).

**Diese Datei entsteht wieder vor dem Code, und diesmal ist der Grund im
Ticket selbst nachzulesen.** T-38 existiert, weil drei der fünf Befunde aus
dem UI-Lauf *derselbe* Fehler waren: Ein Wert fehlte, und nichts hat gefragt.
Der Name war leer, die Gattung war leer, und weil die Gattung leer war, wurde
die Metadatenquelle nie befragt — ohne Meldung, ohne Protokolleintrag,
monatelang.

Ein Test, der nach der Umsetzung entsteht, prüft, was gebaut wurde. Genau das
ist hier wertlos: Die Anforderung lautet nicht „das Feld ist als Pflicht
deklariert", sondern **„eine unvollständige Antwort bleibt nicht folgenlos"**.
Das eine lässt sich am Typ ablesen, das andere nur am Verhalten der Kette.

Die Orakel stammen aus der Verify-Matrix des Tickets:

============ ================================================================
Matrix `#2`  `Resolved.name` und `Resolved.instrument_type` sind Pflicht
Matrix `#4`  Das Contract-Kit schlägt an — der Autor merkt es beim Bauen
Matrix `#5`  Eine Antwort ohne Pflichtfeld ist ein **Befund**, nie still; die
             App leitet nichts ab, insbesondere nicht `stock`
Matrix `#6b` `GET /fields` weist `name` und `type` als Pflicht aus
Matrix `#8`  Die eingebauten Plugins liefern beides — oder sagen ehrlich nichts
============ ================================================================

**Der Punkt, an dem der Typ allein nicht reicht.** Ein Feld ohne Vorgabewert
verhindert das *Weglassen* — mehr nicht. ``Resolved(identity=…, name=None,
instrument_type=None)`` bleibt konstruierbar, und genau so sieht die Antwort
einer Quelle aus, die ihre Felder nicht füllt. Der wirksame Riegel liegt
deshalb an der **Host-Grenze** und im **Contract-Kit**, nicht in der
Dataclass. Wer nur das Pflichtfeld setzt und hier grün wird, hat die Regel
aufgeschrieben und nicht durchgesetzt.

**Orakel und Verdrahtung sind zweierlei.** Die `assert`-Zeilen stehen fest;
die Fakes darüber folgen dem Entwurf. Wer beim Grünmachen eine Zusicherung
ändert, hat den Test an die Lösung angepasst statt umgekehrt.
"""

from dataclasses import MISSING, fields
from pathlib import Path

import pytest
import structlog
from fastapi.testclient import TestClient

from stockinfo_plugin.sources import Resolver
from stockinfo_plugin.types import ListedIdentity, NotFound, Resolved

from app.main import app
from app.plugin_adapters import ResolverAdapter
from app.providers.base import ResolvedInstrument
from app.repository import QuoteRepository
from app.resolver import CompositeResolver
from tests.boundaries import wire_real_chain

_ISIN = "IE00B4L5Y983"


class _SilentlyIncomplete(Resolver):
    """Eine Quelle, die auflöst und die Pflichtfelder leer lässt.

    **Kein erfundener Fehlerfall.** Genau so verhielt sich die Yahoo-Suche im
    UI-Lauf vom 2026-08-28: Identität vollständig, `name` und
    `instrument_type` leer. Die App hat es angenommen, gespeichert und
    angezeigt — und die Metadatenkaskade übersprungen, weil die Gattung
    fehlte.

    Args:
        name: Was die Quelle als Namen liefert.
        instrument_type: Was sie als Gattung liefert.
    """

    name = "unvollstaendig"
    api_version = 2
    SUPPORTED_KINDS = frozenset({"listed"})
    SUPPORTED_TYPES = frozenset({"etf"})

    def __init__(self, name: str | None = None, instrument_type: str | None = None):
        super().__init__(None)
        self._name = name
        self._type = instrument_type

    def handles(self, request) -> bool:
        return True

    def resolve(self, request):
        return Resolved(
            identity=ListedIdentity(ticker="EUNL", mic="XETR", isin=request.isin),
            name=self._name,
            instrument_type=self._type,
        )


class _QuoteSource:
    """Die Kursgrenze — liefert immer, damit der Test die Auflösung misst."""

    def fetch_quote(self, instrument: ResolvedInstrument):
        from app.providers.base import RawQuote

        return RawQuote(
            symbol=instrument.symbol,
            price=98.5,
            quote_time="2026-08-29T17:00:00+00:00",
            currency="EUR",
            type=instrument.type,
        )


def _chain(db_path: str, source: object) -> tuple[TestClient, QuoteRepository]:
    """Die echte Kette über einer frischen Datei — nur die Quelle wechselt."""
    from app.container import get_cached_quote_service

    service, repository = wire_real_chain(
        db_path, _QuoteSource(), CompositeResolver(ResolverAdapter(source, "XETR"))
    )
    app.dependency_overrides[get_cached_quote_service] = lambda: service
    return TestClient(app), repository


def _stored(repository: QuoteRepository, isin: str) -> dict:
    """Die gespeicherte Zeile — Name und Gattung, wie sie wirklich dastehen."""
    with repository._connect() as connection:
        row = connection.execute(
            "SELECT name, type FROM instruments WHERE isin = ?", (isin,)
        ).fetchone()
    return dict(row) if row else {}


# ─── Matrix #2 · der Typ sagt es zu ───────────────────────────────────────────


@pytest.mark.parametrize("field_name", ["name", "instrument_type"])
def test_eine_aufloesung_ohne_pflichtfeld_ist_nicht_baubar(field_name: str) -> None:
    """`Resolved` verlangt beide Felder — kein Vorgabewert.

    Das ist die **schwächste** der Zusicherungen dieser Datei und steht
    trotzdem am Anfang: Sie ist die einzige, die ein Plugin-Autor beim
    Tippen bemerkt. Die Fälle darunter fangen, was sie durchlässt.
    """
    declared = {field.name: field for field in fields(Resolved)}

    assert declared[field_name].default is MISSING, (
        f"{field_name} hat einen Vorgabewert — damit ist es optional, und eine "
        "Quelle kann es weglassen, ohne es zu merken"
    )
    assert declared[field_name].default_factory is MISSING, (
        f"{field_name} hat eine Vorgabefabrik — dasselbe in Grün"
    )


# ─── Matrix #5 · die Host-Grenze ──────────────────────────────────────────────


@pytest.mark.parametrize(
    ("name", "instrument_type", "missing"),
    [
        (None, "etf", "name"),
        ("iShares Core MSCI World", None, "instrument_type"),
        ("", "etf", "leerer name"),
        ("iShares Core MSCI World", "", "leere Gattung"),
    ],
    ids=["ohne-name", "ohne-gattung", "leerer-name", "leere-gattung"],
)
def test_eine_unvollstaendige_antwort_legt_keine_zeile_an(
    tmp_path: Path, name: str | None, instrument_type: str | None, missing: str
) -> None:
    """**Das Kernorakel.** Nichts Halbes kommt in den Bestand.

    Die leeren Zeichenketten stehen absichtlich daneben: Ein Pflichtfeld im
    Typ verhindert das Weglassen, nicht das Füllen mit nichts. Wer nur
    ``default`` entfernt, wird bei den ersten beiden Fällen grün und bei den
    letzten beiden rot — und genau diese Lücke war der Fehler, den T-36
    gefunden hat.

    Geprüft wird das **Ergebnis**, nicht der Weg: Es entsteht keine Zeile mit
    leerem Namen oder leerer Gattung. Ob die Kette dafür `Unavailable`,
    `NotFound` oder etwas Drittes meldet, entscheidet der Entwurf.
    """
    client, repository = _chain(
        str(tmp_path / f"{missing}.db"), _SilentlyIncomplete(name, instrument_type)
    )
    try:
        client.get(f"/quote/{_ISIN}")

        assert _stored(repository, _ISIN) == {}, (
            f"eine Zeile ohne {missing} ist im Bestand gelandet — genau der "
            "stille Verlust, den dieses Ticket verhindern soll"
        )
    finally:
        app.dependency_overrides.clear()


def test_die_app_leitet_keine_gattung_ab(tmp_path: Path) -> None:
    """Nichts wird geraten — insbesondere nicht `stock`.

    Der Satz steht wörtlich in Matrix `#5`, und er hat einen Anlass: Ein
    geratenes ``"stock"`` sähe vollständig aus und schaltete die
    ETF-Anreicherung stillschweigend ab. Eine falsche Antwort ist hier teurer
    als gar keine, weil niemand mehr einen Anlass hat nachzusehen.
    """
    client, repository = _chain(
        str(tmp_path / "geraten.db"), _SilentlyIncomplete("iShares", None)
    )
    try:
        client.get(f"/quote/{_ISIN}")

        assert _stored(repository, _ISIN).get("type") not in ("stock", "etf"), (
            "die Gattung wurde erfunden statt festgestellt"
        )
    finally:
        app.dependency_overrides.clear()


def test_das_fehlende_feld_steht_im_protokoll(tmp_path: Path) -> None:
    """Ein Befund, kein Schweigen — und er nennt Quelle **und** Feld.

    „Nicht angenommen" allein hilft dem Betreiber nicht: Er sieht ein Papier,
    das nicht hereinkommt, und hat vier Quellen zur Auswahl. Der Protokolleintrag
    ist die einzige Stelle, an der steht, **wer** was schuldig geblieben ist.
    """
    client, _ = _chain(str(tmp_path / "protokoll.db"), _SilentlyIncomplete(None, "etf"))
    try:
        with structlog.testing.capture_logs() as logs:
            client.get(f"/quote/{_ISIN}")

        said = " ".join(str(entry) for entry in logs)
        assert "unvollstaendig" in said, f"die Quelle wird nicht genannt: {logs}"
        assert "name" in said, f"das fehlende Feld wird nicht genannt: {logs}"
    finally:
        app.dependency_overrides.clear()


def test_eine_vollstaendige_antwort_kommt_weiterhin_durch(tmp_path: Path) -> None:
    """Die Gegenprobe — ohne sie prüften alle Fälle darüber nur, dass nichts geht.

    Ein Riegel, der auch die guten Antworten aussperrt, macht jeden Test
    darüber grün und das Produkt unbrauchbar.
    """
    client, repository = _chain(
        str(tmp_path / "vollstaendig.db"),
        _SilentlyIncomplete("iShares Core MSCI World", "etf"),
    )
    try:
        response = client.get(f"/quote/{_ISIN}")

        assert response.status_code == 200, response.text
        assert _stored(repository, _ISIN) == {
            "name": "iShares Core MSCI World",
            "type": "etf",
        }
    finally:
        app.dependency_overrides.clear()


# ─── Matrix #6b · die Auskunft ────────────────────────────────────────────────


def test_die_feldauskunft_kennt_den_plugin_vertrag() -> None:
    """`GET /fields` beschreibt heute nur die REST-Modelle.

    Der Endpunkt ist die Stelle, an der ein Plugin-Autor nachsieht, was er
    liefern muss. Steht der Vertrag dort nicht, muss er den Quelltext lesen —
    und die Zusage lebt an zwei Orten, von denen einer veraltet.
    """
    client = TestClient(app)

    answer = client.get("/fields").json()

    assert "plugin_contract" in answer, (
        "die Auskunft kennt den Plugin-Vertrag nicht — ein Autor findet die "
        f"Pflichtfelder nur im Quelltext. Vorhanden: {sorted(answer)}"
    )


def test_name_und_gattung_stehen_dort_als_pflicht() -> None:
    """Matrix `#6b` wörtlich: Sie stehen dort als Pflicht.

    Eine Auskunft, die `required: false` sagt, während der Vertrag das Feld
    verlangt, ist schlimmer als keine: Sie ist eine Zusage, auf die sich
    jemand verlässt.
    """
    client = TestClient(app)

    contract = client.get("/fields").json().get("plugin_contract", {})
    resolved = {field["name"]: field for field in contract.get("resolved", [])}

    assert resolved.get("name", {}).get("required") is True, resolved
    assert resolved.get("instrument_type", {}).get("required") is True, resolved


# ─── Matrix #8 · die eingebauten Quellen ──────────────────────────────────────


@pytest.mark.parametrize(
    ("figi_name", "figi_type", "missing"),
    [
        (None, "etf", "Name"),
        ("iShares Core MSCI World", None, "Gattung"),
    ],
)
def test_openfigi_sagt_lieber_nichts_als_die_haelfte(
    figi_name: str | None, figi_type: str | None, missing: str
) -> None:
    """Die eigenen Quellen halten den Vertrag, den sie fremden auferlegen.

    **Und dieser Fall ist keine Formalie, sondern eine Verhaltensänderung.**
    `FigiMatch.name` und `FigiMatch.instrument_type` sind beide ``| None``:
    OpenFIGI *kann* eine ISIN einem Ticker zuordnen, ohne einen Namen oder
    eine Gattung zu kennen. Bis heute kam so ein Treffer durch und erzeugte
    genau die halbe Zeile, wegen der T-38 existiert.

    Mit den Pflichtfeldern muss OpenFIGI dann `NotFound` sagen — und das
    Papier fällt an den Yahoo-Fallback dahinter. Das ist der Preis der Regel,
    er ist gewollt, und er soll hier sichtbar sein und nicht im Betrieb
    auffallen.
    """
    from app.plugins.openfigi_resolver import OpenFigiResolverPlugin
    from app.providers.openfigi_provider import FigiMatch
    from stockinfo_plugin.types import ResolveRequest

    class _Figi:
        def map_isin(self, isin: str, id_value: str, id_type: str = "micCode"):
            return FigiMatch("EUNL", name=figi_name, instrument_type=figi_type)

    plugin = OpenFigiResolverPlugin(client=_Figi())

    answer = plugin.resolve(ResolveRequest(isin=_ISIN, preferred_mic="XETR"))

    assert not isinstance(answer, Resolved), (
        f"OpenFIGI liefert einen Treffer ohne {missing} — die halbe Zeile, "
        "wegen der dieses Ticket existiert"
    )
    assert isinstance(answer, NotFound), (
        f"unvollstaendig bekannt ist ein NotFound, kein {type(answer).__name__}: "
        "Der Dienst war erreichbar und hat geantwortet, die Antwort trägt nur "
        "nicht, was der Vertrag verlangt"
    )
