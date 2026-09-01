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

**Die Fachdatendatei gehört den Tests.** Sie liegt in `tests/_resources/`
und wird hier benutzt, nicht nachgebaut. Vorher lag sie neben ihrem Ticket —
und weil ein erledigtes Ticket nach `solved/` wandert, hätte dieser
vorgesehene Schritt den ganzen Lauf rot gemacht. Werte, die ein Test
festhält, gehören dorthin, wo der Test sie verantwortet.

**Was diese Datei bewusst nicht prüft.** Die Browserzeile `#6` verlangt einen
Lauf mit Augen; ein grüner Test hier ersetzt ihn nicht und behauptet es auch
nicht.

Die Zeilen `#3`, `#4` und `#7` prüfen die Kaskaden für `quotes`, `daily` und
`fx` unten durch den öffentlichen Weg, mit unterscheidbaren Werten statt
Typprüfungen.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.container import (
    get_cached_quote_service,
    get_daily_history_service,
    get_fx_service,
    get_quote_analyzer,
    get_sources_config,
)
from app.main import app

_SERVICE_CACHES = (
    get_cached_quote_service,
    get_daily_history_service,
    get_fx_service,
    get_quote_analyzer,
)
"""Jeder gecachte Dienst, der Quellen festhält — **vollständig**, nicht auf Zuruf.

Ein Dienst, der hier fehlt, überlebt den Profilwechsel mit den Quellen des
vorigen Tests. Das fällt nicht auf, solange sein Test der erste seiner Art im
Lauf ist.

**Der Analyzer gehört seit T-46 dazu.** Er bekommt die Ketten in den
Konstruktor und ist selbst gecacht — ohne diese Zeile misst die Diagnose nach
einem Profilwechsel weiter die Kette davor.

**Die Konfiguration steht bewusst nicht dabei.** Sie wird beim Profilwechsel
einmal neu gelesen, und die Ketten hängen daran über die **Identität** des
Objekts. Sie danach noch einmal zu verwerfen hieße, `/sources` eine dritte
Konfiguration unterzuschieben — die Rollen meldeten dann „noch nicht gebaut".
"""

SAMPLE = Path(__file__).parent / "_resources" / "assets.yaml"

# Zwei Kursquellen, die **vor** der Datei stehen. Sie belegen die beiden
# Hälften der Kaskade: Wer liefert, gewinnt; wer schweigt, reicht weiter.
_ALWAYS_ANSWERS = '''
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
'''

_COUNTING_ONLINE = '''
from datetime import datetime, timezone
from pathlib import Path

from stockinfo_plugin import Quote, QuoteSource


class CountingOnline(QuoteSource):
    """Steht **vor** der Datei und kennt nur das ETF-Papier.

    Sie zählt ihre Aufrufe in eine Datei — der Test läuft im selben Prozess,
    aber die Quelle wird vom Lader gebaut und ist von außen nicht greifbar.
    """

    name = "counting-online"
    api_version = 2
    SUPPORTED_KINDS = frozenset({"listed", "pair", "isin_only"})
    SUPPORTED_TYPES = frozenset({"stock", "etf", "etc", "fund", "crypto", "bond"})

    MINE = "IE00B4L5Y983"
    TALLY = Path(__file__).parent.parent / "online-calls.txt"

    def handles(self, request) -> bool:
        return getattr(request.identity, "isin", None) == self.MINE

    def fetch_quote(self, request):
        if getattr(request.identity, "isin", None) != self.MINE:
            return None
        seen = int(self.TALLY.read_text()) if self.TALLY.exists() else 0
        self.TALLY.write_text(str(seen + 1))
        return Quote(
            price=999.0,
            currency="EUR",
            as_of=datetime(2026, 8, 30, 12, 0, tzinfo=timezone.utc),
        )


SOURCES = [CountingOnline]
'''

_ANSWERS_NEVER = '''
from stockinfo_plugin import DailyCloseSource, FxSource, NotFound, QuoteSource


class AnswersNever(QuoteSource, DailyCloseSource, FxSource):
    """Zustaendig, hat aber nie eine Antwort — in allen drei Rollen."""

    name = "answers-never"
    api_version = 2
    SUPPORTED_KINDS = frozenset({"listed", "pair", "isin_only"})
    SUPPORTED_TYPES = frozenset({"stock", "etf", "etc", "fund", "crypto", "bond"})

    def handles(self, request) -> bool:
        return True

    def fetch_quote(self, request):
        return NotFound()

    def fetch_daily(self, request):
        return NotFound()

    def fetch_rate(self, request):
        return NotFound()


SOURCES = [AnswersNever]
'''

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
    from app.sources_config import ROLES
    from app.sources_registry import build_chain

    get_sources_config.cache_clear()
    config = get_sources_config()
    for role in ROLES:
        try:
            build_chain(role, config, get_settings())
        except Exception:  # noqa: BLE001, S110 — unbekannte Namen sind hier Absicht
            pass
    # **Die Dienste halten ihre Quellen fest.** Die Ketten neu zu bauen genügt
    # nicht: Jeder gecachte Dienst hat beim Start eine Instanz erzeugt, und die
    # trägt die alten Anbieter weiter. Ohne diese Zeilen zeigte `/sources` das
    # neue Profil und `/quote` antwortete aus dem Netz — die Auskunft und das
    # Verhalten wären auseinandergelaufen.
    #
    # **Alle, nicht nur der Kursdienst.** `/fx`, die Historie und seit T-46 die
    # Diagnose hängen an eigenen Caches; ein Test dafür wäre grün gewesen,
    # solange er zufällig der erste seiner Art im Lauf war — und beim nächsten
    # hinzugefügten Test still umgekippt.
    for cache in _SERVICE_CACHES:
        cache.cache_clear()


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
    # **Vor dem Start**, nicht im Test: Plugins werden beim Lifespan geladen,
    # und eine Datei, die danach entsteht, findet niemand mehr. Geladen zu sein
    # heißt nicht, in einer Kette zu stehen — das entscheidet `sources.yaml`.
    (plugins / "vorne.py").write_text(_ALWAYS_ANSWERS, encoding="utf-8")
    (plugins / "stumm.py").write_text(_ANSWERS_NEVER, encoding="utf-8")
    (plugins / "zaehlend.py").write_text(_COUNTING_ONLINE, encoding="utf-8")
    return tmp_path


@pytest.fixture
def client(volume: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Die App auf einem frischen Volume — Lifespan inklusive.

    Als Kontextmanager, damit der Lifespan wirklich läuft: Dort werden die
    Plugins geladen. Ohne ihn prüfte der Test eine App, die den Ladevorgang nie
    ausgeführt hat.
    """
    monkeypatch.setenv("DATABASE_PATH", str(volume / "stockinfo.db"))

    for cache in (get_settings, get_sources_config, *_SERVICE_CACHES):
        cache.cache_clear()
    with TestClient(app) as opened:
        yield opened
    for cache in (get_settings, get_sources_config, *_SERVICE_CACHES):
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


# ─── Die Datei hinter den Online-Quellen ──────────────────────────────────────
#
# Geprüft wird durch den öffentlichen Eintritt, mit **unterscheidbaren Werten**
# und **Aufrufzählern**: Ohne beides wäre „die erste gewinnt" auch dann grün,
# wenn die zweite gar nicht existierte — und genau diese Zusage war die
# fehlende.


def test_die_vordere_quelle_gewinnt_bei_ueberschneidung(volume: Path, client) -> None:
    """Online schlägt die Datei — sie ist Rückfall, nicht Wahrheit.

    Gewönne die Datei, hätte ein Betreiber seine frischen Kurse mit einem
    gepflegten Stand von gestern überschrieben, ohne es zu bemerken.
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

    body = client.get(f"/quote/{_ETF}").json()

    assert body["price"] == 999.0, (
        "die Datei hat die vorgelagerte Quelle überschrieben: "
        f"{body.get('price')}"
    )


def test_die_datei_schliesst_die_luecke_der_vorderen_quelle(
    volume: Path, client
) -> None:
    """Die vordere Quelle schweigt, die gepflegte Datei muss antworten.
    """
    _profile(
        volume,
        {
            "resolvers": ["yaml-file"],
            "etf_meta": [],
            "quotes": ["answers-never", "yaml-file"],
            "daily": ["yaml-file"],
            "fx": ["yaml-file"],
        },
    )

    body = client.get(f"/quote/{_BOND}").json()

    assert body["price"] == 99.42, (
        f"die Datei hinter der stummen Quelle kam nicht dran: {body}"
    )


def test_die_tagesreihe_faellt_auf_die_datei_durch(volume: Path, client) -> None:
    """Auch die Historie ist eine Kette — und ihr Ausfall fällt weiter.

    Der Unterschied zwischen „nachgesehen, nichts" (leere Reihe, die Kette
    endet) und „konnte nicht nachsehen" (die nächste ist dran) ist am
    Composite direkt geprüft; hier steht nur, dass die Wurzel die Kette
    überhaupt bis zur Datei durchreicht.
    """
    _profile(
        volume,
        {
            "resolvers": ["yaml-file"],
            "etf_meta": [],
            "quotes": ["yaml-file"],
            "daily": ["answers-never", "yaml-file"],
            "fx": ["yaml-file"],
        },
    )

    points = client.get(f"/quote/{_BOND}/daily", params={"period": "1m"}).json()

    assert [point["close"] for point in points] == [99.18, 99.31, 99.42], (
        f"die gepflegte Reihe hinter der stummen Quelle kam nicht dran: {points}"
    )


def test_die_devisenrolle_nennt_den_wirklichen_lieferanten(
    volume: Path, client
) -> None:
    """`/fx` sagt, **wer** geliefert hat — nicht, wer zuerst stand.

    Stünde dort die erste Quelle, läse ein Betreiber „always-answers" über
    einem Wert, den seine Datei beigesteuert hat, und suchte den Fehler bei
    einer Quelle, die gar nicht geantwortet hat.
    """
    _profile(
        volume,
        {
            "resolvers": ["yaml-file"],
            "etf_meta": [],
            "quotes": ["yaml-file"],
            "daily": ["yaml-file"],
            "fx": ["answers-never", "yaml-file"],
        },
    )

    body = client.get("/fx", params={"base": "CAD", "quote": "EUR"}).json()

    assert body["rate"] == 0.6412
    assert body["source"] == "yaml-file", (
        f"die Herkunft nennt nicht den Lieferanten: {body}"
    )


# ─── T-46 · die Diagnose misst die konfigurierte Kette ────────────────────────


def test_die_analyse_geht_im_dateiprofil_nicht_ins_netz(
    volume: Path, client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**Das Pflichtorakel des Tickets.** Kein Netzaufruf, wo keine Netzquelle steht.

    Bis T-46 baute der Analyzer `yf.Ticker` und rief justETF direkt. Eine
    Instanz, die bewusst offline lief, ging beim Analysieren trotzdem hinaus —
    und bekam 254 Zeilen Historie aus einer Quelle, die in ihrem Profil gar
    nicht vorkommt.

    **Dieser Test belegt den öffentlichen Weg, nicht die Abstinenz.** Er zeigt,
    dass `/analyze` im Dateiprofil genau die konfigurierten Quellen nennt und
    dabei über keine Python-Verbindung geht. Für „kein Netz" allein reicht das
    nicht: `yfinance` telefoniert über `curl_cffi`, also über libcurl, und ein
    eingebauter Mutant mit `yf.Ticker(...).history()` mitten in der Diagnose
    ließ die Steckdosenzählung unten grün. Den tragfähigen Teil der Zusage
    trägt deshalb `test_die_diagnose_kennt_keine_einzige_konkrete_quelle` in
    `tests/test_analyzer.py` — wer keine konkrete Quelle kennt, kann keine
    anrufen. Beide zusammen sind das Pflichtorakel, keines allein.
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

    attempts: list[object] = []

    def _refuse(*args: object, **kwargs: object) -> None:
        attempts.append(args[1:] if len(args) > 1 else args)
        raise OSError("kein Netz in diesem Test")

    monkeypatch.setattr("socket.socket.connect", _refuse)
    monkeypatch.setattr("socket.getaddrinfo", _refuse)

    body = client.get("/analyze", params={"isin": _ETF}).json()

    assert attempts == [], f"die Analyse hat das Netz gesucht: {attempts}"
    assert {stage["source"] for stage in body["stages"]} == {"yaml-file"}, (
        f"eine Stufe nennt eine Quelle ausserhalb des Profils: {body['stages']}"
    )
    assert [stage["status"] for stage in body["stages"]].count("error") == 0, (
        f"eine Stufe endete im Fehler: {body['stages']}"
    )
    assert body["symbol"] == "EUNL.DE"


def test_die_analyse_ueberlebt_ein_papier_ohne_boersensymbol(
    volume: Path, client
) -> None:
    """**Befund 1 des Tickets.** Eine `isin_only`-Identität ist kein Fehler.

    Die Bundesanleihe hat kein Börsensymbol; die Auflösung liefert deshalb die
    ISIN als `symbol`. `yf.Ticker("DE0001102531")` warf darauf ein
    `ValueError`, und die Route endete im `500` — in **beiden** Profilen, es
    war also nie ein Quellenproblem.
    """
    _profile(
        volume,
        {
            "resolvers": ["yaml-file"],
            "etf_meta": [],
            "quotes": ["yaml-file"],
            "daily": ["yaml-file"],
            "fx": [],
        },
    )

    response = client.get("/analyze", params={"isin": _BOND})

    assert response.status_code == 200, response.text
    assert response.json()["symbol"] == _BOND


def test_die_analyse_meldet_eine_nicht_gefragte_quelle(volume: Path, client) -> None:
    """**Das dritte Pflichtorakel.** Eine Kaskade hört beim ersten Treffer auf.

    Die zweite Quelle mit `0 ms, ok` zu melden wäre richtig gemessen und falsch
    verstanden: Sie hat nicht schnell geantwortet, sie wurde nicht gefragt. Der
    Unterschied steht deshalb in der Antwort und nicht nur in einer Zählung.
    """
    _profile(
        volume,
        {
            "resolvers": ["yaml-file"],
            "etf_meta": [],
            "quotes": ["always-answers", "yaml-file"],
            "daily": [],
            "fx": [],
        },
    )

    stages = {
        (stage["role"], stage["source"]): stage
        for stage in client.get("/analyze", params={"isin": _ETF}).json()["stages"]
    }

    assert stages[("quotes", "always-answers")]["status"] == "ok"
    assert stages[("quotes", "yaml-file")]["status"] == "skipped", (
        f"die Datei wurde trotz Treffer davor gefragt: {stages}"
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


# ─── T-48 · die Datei wirkt ohne Neustart, die Online-Kette merkt nichts ──────


def _tally(volume: Path) -> int:
    """Wie oft die zählende Online-Quelle gefragt wurde."""
    counter = volume / "online-calls.txt"
    return int(counter.read_text()) if counter.exists() else 0


def test_eine_geaenderte_datei_wirkt_ohne_neustart(volume: Path, client) -> None:
    """**Der Kern des Tickets, über den öffentlichen Weg.**

    Geändert wird **nur der Preis**; `as_of` bleibt stehen. Genau dieser Fall
    fiel vorher zweimal durch: Das Plugin hielt eine Momentaufnahme, und der
    Schreibweg verwarf den korrigierten Wert bei gleichem Zeitstempel.
    """
    eigene = volume / "assets.yaml"
    eigene.write_text(SAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    _profile_with_path(volume, eigene)

    vorher = client.get(f"/quote/{_ETF}").json()["price"]
    eigene.write_text(
        eigene.read_text(encoding="utf-8").replace("value: 128.21", "value: 131.77"),
        encoding="utf-8",
    )
    nachher = client.get(f"/quote/{_ETF}").json()

    assert vorher == 128.21
    assert nachher["price"] == 131.77, "die Änderung erreicht den laufenden Dienst nicht"
    assert nachher["cached"] is False


def test_die_online_kette_zaehlt_nicht_mehr_aufrufe_als_vorher(
    volume: Path, client
) -> None:
    """**Die Gegenprobe zu Mikes Warnung — gezählt, nicht überlegt.**

    Die Kette führt eine Online-Quelle **vor** der Datei. Das ETF-Papier
    bedienen beide, die Anleihe nur die Datei. Zugesagt ist zweierlei:

    * Das Online-Papier behält seine Frist — zwei Abfragen, **ein** Aufruf.
      Eine hintere Dateiquelle macht einen vorderen Treffer nicht cachefrei.
    * Das Datei-Papier umgeht die Frist und nimmt eine Änderung sofort an.

    Geprüft wird am Fonds, nicht an der Anleihe: Deren Preis stammt aus der
    gepflegten History, und die getrennten Cacheverträge für Historie,
    Metadaten und Devisen sind ausdrücklich nicht Teil dieses Tickets.
    """
    eigene = volume / "assets.yaml"
    eigene.write_text(SAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    _profile_with_path(volume, eigene, quotes=["counting-online", "yaml-file"])

    assert client.get(f"/quote/{_ETF}").json()["price"] == 999.0
    client.get(f"/quote/{_ETF}")
    assert _tally(volume) == 1, "die Online-Quelle wurde trotz frischem Cache erneut gefragt"

    client.get(f"/quote/{_FUND}")
    eigene.write_text(
        eigene.read_text(encoding="utf-8").replace("value: 142.50", "value: 143.75"),
        encoding="utf-8",
    )

    assert client.get(f"/quote/{_FUND}").json()["price"] == 143.75
    assert _tally(volume) == 1, "das Datei-Papier hat die Online-Quelle gekostet"


def _profile_with_path(
    volume: Path, path: Path, quotes: list[str] | None = None
) -> None:
    """Wie `_profile`, aber mit einer Datei, die der Test verändern darf."""
    chains = {
        "resolvers": ["yaml-file"],
        "etf_meta": ["yaml-file"],
        "quotes": quotes or ["yaml-file"],
        "daily": ["yaml-file"],
        "fx": ["yaml-file"],
    }
    lines = [f"{role}: [{', '.join(names)}]" for role, names in chains.items()]
    lines += ["", "providers:", "  yaml-file:", f"    path: {path}"]
    (volume / "sources.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    _restart_chains()
