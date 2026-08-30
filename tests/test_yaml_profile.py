"""Ein Plugin, eine Datei, fünf Rollen — die Orakel vor der Umsetzung (T-37).

Die Zusicherungen stammen aus der Verify-Matrix des Tickets und nicht aus dem
Code, der sie erfüllen soll:

============ ================================================================
Matrix `#2`  Alle fünf Rollen werden aus **einer** Datei bedient; `/sources`
             zeigt `yaml-file` in allen fünf und genau einen Pfad
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

**Was diese Datei bewusst nicht prüft.** Die Browserzeile `#6` verlangt einen
Lauf mit Augen; ein grüner Test hier ersetzt ihn nicht und behauptet es auch
nicht.

Die Zeilen `#3`, `#4` und `#7` fehlen hier ebenfalls, und zwar als
**Entscheidung**: Sie verlangen eine Kaskade für `quotes`, `daily` und `fx`,
die es in der App nicht gibt. Sie sind als eigenes Ergebnis abgespalten; der
Abschnitt weiter unten sagt, warum ein Test dazu hier nichts belegen würde.
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
    _restart_chains()


def _restart_chains() -> None:
    """Baut die Ketten neu — wie ein Neustart es täte.

    `/sources` zeigt die **laufende** Kette, nicht die Datei: Der Schnappschuss
    entsteht beim Bauen. Eine Konfiguration, die erst danach geschrieben wird,
    erreicht ihn nicht — ein Test ohne diesen Schritt misst die Vorgabekette
    und damit das Netz.
    """
    from app.config import get_settings
    from app.container import get_cached_quote_service
    from app.sources_config import ROLES
    from app.sources_registry import build_chain

    get_sources_config.cache_clear()
    config = get_sources_config()
    for role in ROLES:
        try:
            build_chain(role, config, get_settings())
        except Exception:  # noqa: BLE001, S110 — unbekannte Namen sind hier Absicht
            pass
    # **Der Dienst hält seine Quellen fest.** Die Ketten neu zu bauen genügt
    # nicht: `get_cached_quote_service` hat beim Start eine Instanz erzeugt und
    # zwischengespeichert, und die trägt die alten Anbieter weiter. Ohne diese
    # Zeile zeigte `/sources` das neue Profil und `/quote` antwortete aus dem
    # Netz — die Auskunft und das Verhalten wären auseinandergelaufen.
    get_cached_quote_service.cache_clear()


@pytest.fixture
def volume(tmp_path: Path) -> Path:
    """Ein Datenvolume, wie es beim Betreiber aussieht.

    Die zusätzliche Kursquelle liegt **hier** und nicht im Test, der sie
    braucht: Plugins werden beim Start geladen, und eine Datei, die danach
    entsteht, findet niemand mehr. Geladen zu sein heißt nicht, in einer Kette
    zu stehen — das entscheidet allein `sources.yaml`.
    """
    plugins = tmp_path / "plugins"
    plugins.mkdir()
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

    listed = client.get("/sources").json()["sources"]

    for role in ("resolvers", "etf_meta", "quotes", "daily", "fx"):
        names = [entry["name"] for entry in listed if entry["role"] == role]
        assert names == ["yaml-file"], f"Rolle {role}: {names}"


@pytest.mark.parametrize(
    ("isin", "expected_type", "expected_price"),
    [(_ETF, "etf", 128.21), (_BOND, "bond", 99.42), (_FUND, "fund", 142.50)],
)
def test_jede_identitaetsform_kommt_aus_der_datei(
    volume: Path, client, isin: str, expected_type: str, expected_price: float
) -> None:
    """Listing, Anleihe und Fonds — aus derselben Datei, über den echten Weg.

    Geprüft wird die öffentliche Antwort, nicht der Parser. Wie oft die Datei
    dabei gelesen wird, ist **keine** Zusage dieses Tickets: Der Host baut je
    Rolle eine Instanz, gemessen sind das fünf Lesevorgänge. Zugesagt ist eine
    Datei, ein Parser, ein Schema — dass ein Papier jeder Form herauskommt,
    ist die Anforderung.

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


# ─── Matrix #4 · abgespalten ──────────────────────────────────────────────────
#
# Die Zeilen `#3`, `#4` und `#7` verlangen eine **Kaskade** für `quotes`,
# `daily` und `fx`: Online zuerst, die Datei zuletzt, und gefragt wird sie nur,
# wenn die Kette davor nichts hat. Die App kennt für diese drei Rollen keine
# Kette — `container._first` nimmt die erste einsatzbereite Quelle.
#
# Das ist eine eigene Produktabstraktion und wurde als eigenes Ergebnis
# abgespalten. Hier stehen deshalb **keine** Fälle dazu: Ein Test, der die
# Überschneidung prüft, während nur die erste Quelle gefragt wird, wäre grün,
# ohne etwas zu belegen — genau die Sorte Zusicherung, die dieses Ticket
# zweimal gefunden hat.

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
    _restart_chains()

    entry = next(
        source
        for source in client.get("/sources").json()["sources"]
        if source["name"] == "yaml-file" and source["role"] == "resolvers"
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
    _restart_chains()

    entry = next(
        source
        for source in client.get("/sources").json()["sources"]
        if source["name"] == "yaml-file" and source["role"] == "resolvers"
    )

    assert entry["configured"] is False
    assert entry["reason"], "abgeschaltet ohne Begründung ist der halbe Fehler"


# ─── Matrix #9 · jede Invariante hat ihre Gegenprobe ──────────────────────────

_GOOD_ENTRY = """version: 1
instruments:
  - id: gut
    identity: {kind: listed, isin: IE00B4L5Y983, ticker: EUNL, mic: XETR}
    name: iShares Core MSCI World
    instrument_type: etf
    price: {value: 128.21, currency: EUR, as_of: "2026-08-27T17:30:00+02:00"}
"""


@pytest.mark.parametrize(
    ("broken", "expected"),
    [
        pytest.param(
            """version: 1
instruments:
  - id: a
    identity: {kind: listed, isin: IE00B4L5Y983, ticker: EUNL, mic: XETR}
    name: Erster
    instrument_type: etf
  - id: b
    identity: {kind: listed, isin: IE00B4L5Y983, ticker: EUNL, mic: XETR}
    name: Zweiter
    instrument_type: etf
""",
            "schon vergeben",
            id="doppelte-identitaet",
        ),
        pytest.param(
            """version: 1
instruments:
  - id: a
    identity: {kind: listed, isin: XX0000000000, ticker: EUNL, mic: XETR}
    name: Falsche Pruefziffer
    instrument_type: etf
""",
            "isin",
            id="ungueltige-isin",
        ),
        pytest.param(
            """version: 1
instruments:
  - id: a
    identity: {kind: listed, isin: IE00B4L5Y983, ticker: EUNL, mic: US}
    name: Sammelcode statt MIC
    instrument_type: etf
""",
            "mic",
            id="sammelcode-statt-mic",
        ),
        pytest.param(
            """version: 1
instruments:
  - id: a
    identity: {kind: listed, isin: IE00B4L5Y983, ticker: EUNL, mic: XETR}
    name: Pence
    instrument_type: etf
    price: {value: 1.0, currency: GBX, as_of: "2026-08-27T17:30:00+02:00"}
""",
            "currency",
            id="untereinheit-als-waehrung",
        ),
        pytest.param(
            """version: 1
instruments:
  - id: a
    identity: {kind: listed, isin: IE00B4L5Y983, ticker: EUNL, mic: XETR}
    name: Ohne Zone
    instrument_type: etf
    price: {value: 1.0, currency: EUR, as_of: "2026-08-27T17:30:00"}
""",
            "zeitzone",
            id="zeitpunkt-ohne-zone",
        ),
        pytest.param(
            """version: 1
instruments:
  - id: a
    identity: {kind: listed, isin: IE00B4L5Y983, ticker: EUNL, mic: XETR}
    name: Nullkurs
    instrument_type: etf
    price: {value: 0, currency: EUR, as_of: "2026-08-27T17:30:00+02:00"}
""",
            "positiver kurs",
            id="nullkurs",
        ),
        pytest.param(
            """version: 1
instruments:
  - id: a
    identity: {kind: isin_only, isin: DE0001102531}
    name: Doppelter Tag
    instrument_type: bond
    history:
      currency: EUR
      closes:
        - {date: "2026-08-27", value: 99.42}
        - {date: "2026-08-27", value: 99.50}
""",
            "zweimal",
            id="doppelter-history-tag",
        ),
        pytest.param(
            """version: 1
instruments: []
fx_rates:
  - {base: CAD, quote: EUR, rate: -1.0, as_of: "2026-08-27T17:30:00+02:00"}
""",
            "positiver kurs",
            id="negativer-wechselkurs",
        ),
    ],
)
def test_jede_invariante_wird_beim_laden_geprueft(
    tmp_path: Path, broken: str, expected: str
) -> None:
    """**Acht Mutanten, jeder mit genau einem Fehler.**

    Eine Prüfung, die nichts abweisen kann, belegt nur, dass sie durchgelaufen
    ist. Jeder Fall hier verletzt **eine** Regel und ist sonst tadellos; die
    Meldung muss sie beim Namen nennen, sonst sucht der Betreiber in einer
    Datei mit hundert Zeilen.

    Der wichtigste ist die doppelte Identität. Sie war der stillste Fehler des
    Formats: Zwei Einträge mit derselben ISIN widersprechen sich, und bis hier
    gewann der zweite, weil eine Zuweisung den ersten überschrieb. Die Datei
    sah gültig aus, und welcher Eintrag galt, hing an der Zeilenreihenfolge.
    """
    from stockinfo_plugin_examples.yaml_file import YamlFileSource

    path = tmp_path / "kaputt.yaml"
    path.write_text(broken, encoding="utf-8")

    problem = YamlFileSource({"path": str(path)}).configuration_problem()

    assert problem, "die Quelle meldet keinen Grund und tut so, als sei alles gut"
    assert expected in problem.lower(), (
        f"die Meldung nennt die verletzte Regel nicht: {problem!r}"
    )


def test_eine_gueltige_datei_wird_nicht_beanstandet(tmp_path: Path) -> None:
    """Die Gegenprobe zu den acht Mutanten.

    Ohne sie prüften sie nur, dass *irgendetwas* abgewiesen wird — und wären
    auch grün, wenn der Parser jede Datei ablehnte.
    """
    from stockinfo_plugin_examples.yaml_file import YamlFileSource

    path = tmp_path / "gut.yaml"
    path.write_text(_GOOD_ENTRY, encoding="utf-8")

    assert YamlFileSource({"path": str(path)}).configuration_problem() == ""


def test_ein_neustart_liest_die_geaenderte_datei(tmp_path: Path) -> None:
    """Der zugesagte Reload — **gemessen**, nicht behauptet.

    Das Ticket sagt zu: „ein Neustart liest eine gültig geänderte Datei erneut
    ein". Hot Reload ist ausdrücklich nicht Teil davon; geprüft wird deshalb
    genau das, was zugesagt ist — eine **neue** Instanz, wie sie beim Start
    entsteht.
    """
    from stockinfo_plugin.types import ResolveRequest
    from stockinfo_plugin_examples.yaml_file import YamlFileSource

    path = tmp_path / "wandelbar.yaml"
    path.write_text(_GOOD_ENTRY, encoding="utf-8")
    before = YamlFileSource({"path": str(path)}).resolve(
        ResolveRequest(isin="IE00B4L5Y983")
    )
    assert before.name == "iShares Core MSCI World"

    path.write_text(
        _GOOD_ENTRY.replace("iShares Core MSCI World", "Umbenannt"), encoding="utf-8"
    )

    after = YamlFileSource({"path": str(path)}).resolve(
        ResolveRequest(isin="IE00B4L5Y983")
    )

    assert after.name == "Umbenannt", (
        "der Neustart hat den alten Stand behalten — dann wäre eine Änderung "
        "an der Datei folgenlos"
    )


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
