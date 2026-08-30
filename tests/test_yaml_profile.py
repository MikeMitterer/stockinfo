"""Ein Plugin, eine Datei, fünf Rollen — die Orakel vor der Umsetzung (T-37).

Die Zusicherungen stammen aus der Verify-Matrix des Tickets und nicht aus dem
Code, der sie erfüllen soll:

============ ================================================================
Matrix `#2`  Alle fünf Rollen werden aus **einer** Datei bedient; `/sources`
             zeigt `yaml-file` in allen fünf und genau einen Pfad
Matrix `#4`  Liefert eine Online-Quelle einen Wert, gewinnt sie. YAML
             ergänzt nur, wo die Kette nichts hat
Matrix `#5`  Manuelle History gilt nur, wo keine Quelle sie abfragen kann;
             fehlt `price`, darf der jüngste Schlusskurs einspringen
Matrix `#8`  Kein CSV-Profil und keine vier Dateiquellen bleiben übrig
Matrix `#9`  Fehlende Datei, ungültiges YAML und doppelte Kennungen werden
             verständlich gemeldet
============ ================================================================

**Die Fachdatendatei ist die aus dem Ticket.** `_tickets/T-37-single-file-sample.yaml`
wird hier nicht nachgebaut, sondern benutzt. Eine Kopie im Testordner wäre
bequemer und würde beim ersten Nachtrag auseinanderlaufen — dann beschriebe das
Ticket ein Format, das niemand mehr prüft.

**Was diese Datei bewusst nicht prüft.** Die Browserzeilen `#6` und `#7` der
Matrix verlangen einen Lauf mit Augen; ein grüner Test hier ersetzt ihn nicht
und behauptet es auch nicht.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.container import get_sources_config
from app.main import app

SAMPLE = Path(__file__).parent.parent / "_tickets" / "T-37-single-file-sample.yaml"

# Die Papiere aus der Beispieldatei, mit dem, was an ihnen geprüft wird.
_ETF = "IE00B4L5Y983"
_BOND = "DE0001102531"
_FUND = "DE0009848119"


def _profile(volume: Path, chains: dict[str, list[str]]) -> None:
    """Schreibt eine `sources.yaml`, die auf die Beispieldatei zeigt.

    Args:
        volume: Das Datenvolume des Laufs.
        chains: Rolle → Quellen, in Reihenfolge.
    """
    lines = [f"{role}: [{', '.join(sources)}]" for role, sources in chains.items()]
    lines += ["", "providers:", "  yaml-file:", f"    path: {SAMPLE}"]
    (volume / "sources.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.fixture
def volume(tmp_path: Path) -> Path:
    """Ein Datenvolume, wie es beim Betreiber aussieht."""
    (tmp_path / "plugins").mkdir()
    return tmp_path


@pytest.fixture
def client(volume: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Die App auf einem frischen Volume — Lifespan inklusive.

    Als Kontextmanager, damit der Lifespan wirklich läuft: Dort werden die
    Plugins geladen. Ohne ihn prüfte der Test eine App, die den Ladevorgang nie
    ausgeführt hat.
    """
    monkeypatch.setenv("DATABASE_PATH", str(volume / "stockinfo.db"))
    from app.config import get_settings
    from app.container import get_cached_quote_service

    for cache in (get_settings, get_sources_config, get_cached_quote_service):
        cache.cache_clear()
    with TestClient(app) as opened:
        yield opened
    for cache in (get_settings, get_sources_config, get_cached_quote_service):
        cache.cache_clear()


# ─── Matrix #2 · eine Datei, fünf Rollen ──────────────────────────────────────


def test_eine_quelle_steht_in_allen_fuenf_rollen(volume: Path, client) -> None:
    """Dasselbe Plugin bedient jede Rolle — und nennt genau einen Pfad.

    Der Pfad ist die eigentliche Aussage. Fünf Rollen, die je eine eigene Datei
    lesen, wären wieder vier Quellen mit anderem Namen; die Zusage des Tickets
    ist **eine** vom Benutzer gepflegte Datei.
    """
    _profile(
        volume,
        {
            "resolvers": ["yaml-file"],
            "etf_meta": ["yaml-file"],
            "quotes": ["yaml-file"],
            "daily": ["yaml-file"],
            "fx": ["yaml-file"],
        },
    )

    sources = client.get("/sources").json()

    for role in ("resolvers", "etf_meta", "quotes", "daily", "fx"):
        names = [entry["name"] for entry in sources[role]]
        assert names == ["yaml-file"], f"Rolle {role}: {names}"


@pytest.mark.parametrize(
    ("isin", "expected_type", "expected_price"),
    [(_ETF, "etf", 128.21), (_BOND, "bond", 99.42), (_FUND, "fund", 142.50)],
)
def test_jede_identitaetsform_kommt_aus_der_datei(
    volume: Path, client, isin: str, expected_type: str, expected_price: float
) -> None:
    """Listing, Anleihe und Fonds — aus derselben Datei, über den echten Weg.

    Geprüft wird die öffentliche Antwort, nicht der Parser: Ob das Plugin die
    Datei einmal oder fünfmal liest, ist seine Sache; dass ein Papier jeder
    Form herauskommt, ist die Anforderung.

    **Der Preis steht in der Zusicherung, und er ist dort kein Beiwerk.** Er
    ist der Beleg, dass die Antwort wirklich aus der Datei kommt. Ohne ihn war
    dieser Fall grün, bevor es das Plugin gab: Eine unbekannte Quelle in
    `sources.yaml` lässt die Kette leer, die App fällt auf ihre eingebauten
    Online-Quellen zurück, und für ein bekanntes Papier antwortet dann das
    Netz. Ein Orakel, das jede Antwort akzeptiert, prüft die Verkabelung des
    Testaufbaus.
    """
    _profile(
        volume,
        {
            "resolvers": ["yaml-file"],
            "etf_meta": ["yaml-file"],
            "quotes": ["yaml-file"],
            "daily": ["yaml-file"],
            "fx": ["yaml-file"],
        },
    )

    response = client.get(f"/quote/{isin}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["type"] == expected_type
    assert body["name"], "Name ist seit T-38 Pflicht"
    assert body["price"] == expected_price, (
        "der Kurs stammt nicht aus der Beispieldatei — dann hat eine andere "
        f"Quelle geantwortet: {body}"
    )


def test_das_paar_kommt_ueber_sein_symbol(volume: Path, client) -> None:
    """`BTC-EUR` hat keine ISIN — der Eintritt ist das Symbol.

    Die Datei führt es als `pair`; ohne diese Form gäbe es für eine Coin
    überhaupt keinen Weg herein.
    """
    _profile(
        volume,
        {
            "resolvers": ["yaml-file"],
            "etf_meta": ["yaml-file"],
            "quotes": ["yaml-file"],
            "daily": ["yaml-file"],
            "fx": ["yaml-file"],
        },
    )

    response = client.get("/quote", params={"symbol": "BTC-EUR"})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["identity"]["kind"] == "pair"
    assert body["type"] == "crypto"
    assert body["currency"] == "EUR"
    # Derselbe Grund wie oben: Ohne den Wert aus der Datei war dieser Fall
    # grün, weil bei leerer Kette das Netz einsprang.
    assert body["price"] == 94500.00, (
        f"der Kurs stammt nicht aus der Beispieldatei: {body}"
    )


# ─── Matrix #4 · Online gewinnt, YAML ergänzt ─────────────────────────────────


def test_die_online_quelle_gewinnt_bei_ueberschneidung(volume: Path, client) -> None:
    """YAML ist der letzte Rückfall, kein Override.

    Der Fall ist der ganze Zweck des Online-Profils: Dieselbe ISIN steht in der
    Datei **und** wird von einer Quelle davor beantwortet. Gewönne die Datei,
    hätte ein Betreiber seine Online-Kurse mit einem gepflegten Stand von
    gestern überschrieben, ohne es zu bemerken.
    """
    _profile(
        volume,
        {
            "resolvers": ["yaml-file"],
            "etf_meta": [],
            "quotes": ["always-answers", "yaml-file"],
            "daily": ["yaml-file"],
            "fx": ["yaml-file"],
        },
    )
    _install_always_answering_quote_source(volume)

    price = client.get(f"/quote/{_ETF}").json()["price"]

    assert price == 999.0, (
        "die Datei hat die vorgelagerte Quelle überschrieben — sie ist der "
        "Rückfall und nicht die Wahrheit"
    )


def _install_always_answering_quote_source(volume: Path) -> None:
    """Eine Kursquelle vor der Datei, die immer einen erkennbaren Wert liefert."""
    (volume / "plugins" / "vorne.py").write_text(
        '''
from datetime import datetime, timezone

from stockinfo_plugin import Quote, QuoteSource


class AlwaysAnswers(QuoteSource):
    """Steht vor der Datei und antwortet auf alles."""

    name = "always-answers"
    api_version = 2
    SUPPORTED_KINDS = frozenset({"listed", "pair", "isin_only"})
    SUPPORTED_TYPES = frozenset({"stock", "etf", "etc", "fund", "crypto", "bond"})

    def handles(self, request) -> bool:
        return True

    def fetch_quote(self, request):
        return Quote(
            price=999.0,
            currency="EUR",
            as_of=datetime(2026, 8, 30, 12, 0, tzinfo=timezone.utc),
        )


SOURCES = [AlwaysAnswers]
''',
        encoding="utf-8",
    )


# ─── Matrix #5 · die manuelle History als Rückfall ────────────────────────────


def test_die_anleihe_bekommt_ihren_preis_aus_der_history(volume: Path, client) -> None:
    """Ohne `price` springt der jüngste Schlusskurs ein.

    Die Bundesanleihe in der Beispieldatei hat keinen aktuellen Kurs, aber drei
    Schlusskurse. Ein Papier, das nur deshalb ohne Preis dastünde, wäre für den
    Betreiber wertlos — und die Datei enthält die Angabe ja.
    """
    _profile(
        volume,
        {
            "resolvers": ["yaml-file"],
            "etf_meta": [],
            "quotes": ["yaml-file"],
            "daily": ["yaml-file"],
            "fx": ["yaml-file"],
        },
    )

    body = client.get(f"/quote/{_BOND}").json()

    assert body["price"] == 99.42, "der jüngste Schlusskurs ist der Rückfall"
    assert body["currency"] == "EUR"


def test_die_manuelle_history_kommt_als_tagesreihe(volume: Path, client) -> None:
    """Drei gepflegte Schlusskurse, drei Punkte — in der Reihenfolge der Datei."""
    _profile(
        volume,
        {
            "resolvers": ["yaml-file"],
            "etf_meta": [],
            "quotes": ["yaml-file"],
            "daily": ["yaml-file"],
            "fx": ["yaml-file"],
        },
    )

    points = client.get(f"/quote/{_BOND}/daily", params={"period": "1m"}).json()

    assert [point["close"] for point in points] == [99.18, 99.31, 99.42]


# ─── Matrix #9 · die Fehlerfälle ──────────────────────────────────────────────


@pytest.mark.parametrize(
    ("content", "expected_in_reason"),
    [
        ("instruments: [", "yaml"),
        (
            "version: 1\ninstruments:\n"
            "  - id: doppelt\n    identity: {kind: isin_only, isin: DE0001102531}\n"
            "    name: A\n    instrument_type: bond\n"
            "  - id: doppelt\n    identity: {kind: isin_only, isin: DE0009848119}\n"
            "    name: B\n    instrument_type: fund\n",
            "doppelt",
        ),
    ],
    ids=["ungueltiges-yaml", "doppelte-kennung"],
)
def test_eine_kaputte_datei_nennt_ihren_grund(
    volume: Path, client, content: str, expected_in_reason: str
) -> None:
    """Nicht einsatzbereit — **mit** Grund, nicht als stille Leerantwort.

    Eine Quelle, die sich wegen einer kaputten Datei abschaltet und dazu
    schweigt, kostet den Betreiber den Nachmittag: Er sieht leere Listen und
    sucht den Fehler in der App.
    """
    broken = volume / "kaputt.yaml"
    broken.write_text(content, encoding="utf-8")
    (volume / "sources.yaml").write_text(
        "resolvers: [yaml-file]\netf_meta: []\nquotes: [yaml-file]\n"
        "daily: []\nfx: []\n\nproviders:\n  yaml-file:\n"
        f"    path: {broken}\n",
        encoding="utf-8",
    )

    entry = next(
        source
        for source in client.get("/sources").json()["resolvers"]
        if source["name"] == "yaml-file"
    )

    assert entry["configured"] is False
    assert expected_in_reason in (entry["reason"] or "").lower(), entry


def test_eine_fehlende_datei_ist_nicht_einsatzbereit(volume: Path, client) -> None:
    """Der häufigste Betriebsfall: Der Pfad zeigt ins Leere."""
    (volume / "sources.yaml").write_text(
        "resolvers: [yaml-file]\netf_meta: []\nquotes: []\ndaily: []\nfx: []\n\n"
        "providers:\n  yaml-file:\n    path: /gibt/es/nicht.yaml\n",
        encoding="utf-8",
    )

    entry = next(
        source
        for source in client.get("/sources").json()["resolvers"]
        if source["name"] == "yaml-file"
    )

    assert entry["configured"] is False
    assert entry["reason"], "abgeschaltet ohne Begründung ist der halbe Fehler"


# ─── Matrix #8 · die vier Dateiquellen sind weg ───────────────────────────────


def test_kein_csv_beispiel_bleibt_uebrig() -> None:
    """Vier Quellen werden durch eine ersetzt — nicht um eine ergänzt.

    Das Ticket sagt „entfernt statt parallel unterstützt". Bliebe eines der
    CSV-Beispiele stehen, gäbe es zwei Dateiformate mit je eigener Fachlogik,
    und die Prüfstrecke wäre wieder doppelt.
    """
    examples = Path(__file__).parent.parent / "plugin_api" / "examples"

    remaining = sorted(
        path.name
        for path in examples.glob("*.py")
        if path.name not in ("__init__.py", "yaml_file.py")
    )

    assert remaining == [], f"CSV-Beispiele stehen noch: {remaining}"


def test_die_dateiquelle_deklariert_alle_formen_und_gattungen() -> None:
    """Eine leere Deklaration hieße „nichts zugesagt", nicht „alles".

    Der Host überspringt seit T-31 jede Quelle, die eine **bekannte** Gattung
    nicht deklariert. `yaml-file` liest eine Dateizeile und ist damit für jede
    Gattung des Katalogs zuständig — steht das nicht da, wird die Quelle
    übersprungen, obwohl sie die einzige ist, die antworten könnte.
    """
    from stockinfo_plugin_examples.yaml_file import YamlFileSource

    assert YamlFileSource.SUPPORTED_KINDS == frozenset(
        {"listed", "pair", "isin_only"}
    )
    assert YamlFileSource.SUPPORTED_TYPES == frozenset(
        {"stock", "etf", "etc", "fund", "crypto", "bond"}
    )
