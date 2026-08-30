"""Ein Datei-Plugin und ein echter Entry-Point, ganz durch: Registry → Core → REST.

Das ist die Aussage, an der T-23 gemessen wird — und sie ist der Grund, warum
Runde 1 nicht reichte. Dort wurden Plugins geladen, geprüft und angezeigt; den
Core erreichte keines. Der damalige „Auswahltest" verlangte sogar ausdrücklich,
dass `quotes: [yfinance]` **kein** Plugin baut: Er hat die Lücke als
Eigenschaft festgeschrieben.

Hier läuft es andersherum. Zwei Ladewege, beide echt:

* **Entry-Point** — `yaml-file` ist in `plugin_api/pyproject.toml` unter der
  Gruppe `stockinfo.sources` angemeldet und im Environment installiert. Kein
  Nachstellen: `importlib.metadata` findet ihn, weil er wirklich da ist.
* **Datei** — eine `*.py` im Plugin-Verzeichnis des Datenvolumes.

Beide benutzen das **vorhandene** Beispiel-Plugin aus `plugin_api/examples/`.
Ein zweites Plugin für den Test zu schreiben hieße, ein zweites Format und
eine zweite Fachlogik zu pflegen — für etwas, das bereits existiert und
vertraglich geprüft ist.
"""

import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from stockinfo_plugin import (
    ListedIdentity,
    MetadataSource,
    PairIdentity,
    NotResponsible,
    Resolved,
    Resolver,
    Unavailable,
    Unsupported,
)

from app.container import get_sources_config
from app.main import app
from app.plugin_adapters import MetadataAdapter, ResolverAdapter
from app.plugin_loader import ENTRY_POINT_GROUP, load_all
from app.sources_registry import register_loaded, specs_by_name

EXAMPLES = Path(__file__).parent.parent / "plugin_api" / "examples"

# Ein Papier, das OpenFIGI an der Vorgabebörse **nicht** kennt — genau der
# gemessene Anlass für die Handpflege. Der Kurs steht in der Datei unten und
# nirgends sonst; er ist der Beweis, dass die Antwort von dort kommt.
ASSETS = """version: 1
instruments:
  - id: rbc
    identity:
      kind: listed
      isin: CA78012H5675
      ticker: RY
      mic: XTSE
    name: Royal Bank of Canada
    instrument_type: stock
    price:
      value: 141.55
      currency: CAD
      as_of: "2026-01-03T21:00:00+00:00"
"""

# **Die Beispieldatei wird wirklich kopiert**, nicht importiert. Ein Import aus
# der installierten Distribution prüfte am Ende denselben Ladeweg wie der
# Entry-Point und ließe die Datei-Variante ungeprüft. Ein Betreiber legt eine
# **Datei** ab, kein Paket.
#
# Angehängt wird nur ein eigener Name, damit sich beide Wege im selben Lauf
# unterscheiden lassen.
FILE_SUFFIX = '''

class LocalFileSource(YamlFileSource):
    """Dasselbe Beispiel, aus dem Datenvolume geladen."""

    name = "local-file"
    # Geerbt genuegt nicht: Der Loader verlangt die Deklaration an der
    # konkreten Klasse, sonst reichte eine Basisklasse sie fuer beliebige
    # Ableitungen weiter — und die Schranke praefte wieder nichts.
    api_version = 2


SOURCES = [LocalFileSource]
'''


@pytest.fixture
def volume(tmp_path: Path) -> Path:
    """Ein Datenvolume, wie es beim Betreiber aussieht."""
    (tmp_path / "assets.yaml").write_text(ASSETS, encoding="utf-8")
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    # Die echte Beispieldatei, Zeile für Zeile — so, wie ein Betreiber sie
    # kopieren würde.
    shutil.copy(EXAMPLES / "yaml_file.py", plugins / "lokal.py")
    with (plugins / "lokal.py").open("a", encoding="utf-8") as handle:
        handle.write(FILE_SUFFIX)
    return tmp_path


@pytest.fixture(autouse=True)
def _empty_registry() -> Iterator[None]:
    """Kein Test erbt die geladenen Plugins eines anderen."""
    register_loaded(())
    yield
    register_loaded(())
    get_sources_config.cache_clear()


def _restart_chains() -> None:
    """Baut die Ketten neu — wie ein Neustart es täte.

    `/sources` zeigt die **laufende** Kette, nicht die Datei: Ein Schnappschuss
    wird beim Bauen gesetzt, und genau das ist der Punkt (siehe Befund 3 der
    Runde 3). Eine geänderte `sources.yaml` gilt deshalb erst nach einem
    Neustart — im Test wird er hier nachgestellt statt umgangen.
    """
    from app.config import get_settings
    from app.sources_config import ROLES
    from app.sources_registry import build_chain

    config = get_sources_config()
    for role in ROLES:
        try:
            build_chain(role, config, get_settings())
        except Exception:  # noqa: BLE001, S110 — unbekannte Namen sind hier Absicht
            pass


def _sources_yaml(volume: Path, resolver: str) -> None:
    """Schreibt die Konfiguration, die den Ladeweg auswählt."""
    # **Dieselbe Quelle in zwei Rollen** — das ist seit T-37 der Normalfall und
    # nicht die Ausnahme: Ein Plugin, eine Datei, mehrere Rollen.
    (volume / "sources.yaml").write_text(
        f"""
resolvers: [{resolver}]
quotes:    [{resolver}]
etf_meta:  []
daily:     [yfinance]
fx:        [yfinance]

providers:
  {resolver}:
    path: {volume / "assets.yaml"}
""",
        encoding="utf-8",
    )


@pytest.fixture
def client(volume: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Die App auf einem frischen Volume — Lifespan inklusive.

    `TestClient` als Kontextmanager, damit der Lifespan wirklich läuft: Dort
    werden die Plugins geladen, und ohne ihn prüfte der Test eine App, die den
    Ladevorgang nie ausgeführt hat.
    """
    monkeypatch.setenv("DATABASE_PATH", str(volume / "stockinfo.db"))
    from app.config import get_settings

    get_settings.cache_clear()
    get_sources_config.cache_clear()
    from app.container import get_cached_quote_service

    get_cached_quote_service.cache_clear()
    with TestClient(app) as opened:
        yield opened
    get_settings.cache_clear()
    get_sources_config.cache_clear()
    get_cached_quote_service.cache_clear()


def test_der_entry_point_ist_wirklich_installiert() -> None:
    """Kein nachgestellter Ladeweg — die Gruppe steht im Environment.

    Ohne diesen Test bewiese der Rest nur, dass ein Monkeypatch funktioniert.
    Der Entry-Point ist in `plugin_api/pyproject.toml` angemeldet und mit
    `pip install -e plugin_api` registriert; hier wird nachgesehen, nicht
    behauptet.
    """
    from importlib.metadata import entry_points

    names = {point.name for point in entry_points(group=ENTRY_POINT_GROUP)}

    assert "yaml-file" in names, (
        "der Entry-Point fehlt — plugin_api neu installieren: "
        "pip install -e plugin_api"
    )


def test_beide_ladewege_landen_in_derselben_registry(volume: Path) -> None:
    """Datei und Entry-Point stehen gleichwertig neben den eingebauten Quellen."""
    register_loaded(load_all(volume).specs)

    known = specs_by_name()

    assert "yaml-file" in known, "aus dem installierten Paket"
    assert "local-file" in known, "aus dem Datenvolume"
    assert "openfigi" in known, "und die eingebauten sind weiterhin da"


@pytest.mark.parametrize(
    ("resolver", "load_path"),
    [("yaml-file", "Entry-Point"), ("local-file", "Datei im Volume")],
)
def test_ein_plugin_beantwortet_eine_echte_rest_anfrage(
    client: TestClient, volume: Path, resolver: str, load_path: str
) -> None:
    """**Der vertikale Lauf** — und er läuft zweimal, einmal je Ladeweg.

    Aufgenommen wird über den öffentlichen Endpunkt. Die Antwort trägt
    `ticker`, `mic` und den Namen; alle drei stehen **nur** in der CSV des
    Plugins. Käme irgendetwas davon aus einer eingebauten Quelle, stünde dort
    ein anderer Wert oder gar keiner — OpenFIGI kennt dieses Papier an der
    Vorgabebörse nicht, das ist der gemessene Anlass für die Handtabelle.

    Damit ist die Kette belegt: Registry lädt das Plugin, der Adapter übersetzt
    in die Sprache des Core, der Service baut die Antwort, und das
    Pydantic-Modell am REST-Rand gibt sie heraus.
    """
    _sources_yaml(volume, resolver)
    get_sources_config.cache_clear()
    from app.container import get_cached_quote_service

    get_cached_quote_service.cache_clear()

    answer = client.post("/instruments/intake", json={"identifier": "CA78012H5675"})

    assert answer.status_code in (200, 201), f"{load_path}: {answer.text}"
    body = answer.json()
    assert body["identity"]["ticker"] == "RY", load_path
    assert body["identity"]["mic"] == "XTSE", load_path
    assert body["name"] == "Royal Bank of Canada", load_path


def test_die_eingebauten_quellen_nehmen_denselben_weg(volume: Path) -> None:
    """`openfigi` ist seit T-23 selbst ein Plugin — kein verdrahteter Sonderfall.

    Das ist die Zusage „der erste Plugin-Autor ist die App selbst". Wäre sie
    nicht eingelöst, fiele es bei einem Vertragsproblem zuerst einem Fremden
    auf und nicht uns.
    """
    from app.config import Settings
    from app.plugin_adapters import ResolverAdapter, unwrap
    from app.sources_config import SourcesConfig
    from app.sources_registry import build_chain

    chain = build_chain(
        "resolvers", SourcesConfig(chains={"resolvers": ("openfigi",)}), Settings()
    )

    assert isinstance(chain[0], ResolverAdapter), "auch die eingebaute geht durch"
    assert type(unwrap(chain[0])).__name__ == "OpenFigiResolverPlugin"


def test_beide_namen_erscheinen_in_sources(client: TestClient, volume: Path) -> None:
    """Verify `#1` und `#2` verlangen **das Erscheinen in `GET /sources`**.

    Bis Runde 3 prüften beide REST-Fälle nur die Aufnahme. Dass ein Plugin
    antwortet, ist die eine Aussage; dass der Betreiber es **sieht**, ist die
    andere — und ohne sie könnte eine Quelle arbeiten, ohne dass jemand weiß,
    dass es sie gibt.

    Geprüft werden beide Ladewege im selben Lauf: `yaml-file` kommt aus dem
    installierten Paket, `local-file` aus der kopierten Datei im Volume.
    """
    # **Beide** in derselben Kette — sonst prüft der Test nur einen Ladeweg.
    _sources_yaml(volume, "local-file, yaml-file")
    get_sources_config.cache_clear()
    _restart_chains()

    answer = client.get("/sources")

    assert answer.status_code == 200, answer.text
    names = {entry["name"] for entry in answer.json()["sources"]}

    # **Ausschließlich in der HTTP-Antwort.** Bis Runde 4 stand hier ein
    # `oder in specs_by_name()` — damit wäre der Test grün geblieben, wenn der
    # Entry-Point im öffentlichen Endpunkt gefehlt hätte, also genau bei dem
    # Fehler, den seine Überschrift ausschließt.
    assert "local-file" in names, f"die Datei im Volume fehlt: {sorted(names)}"
    assert "yaml-file" in names, f"der Entry-Point fehlt: {sorted(names)}"


def test_eine_unbrauchbare_quelle_nennt_ihren_grund(client: TestClient, volume: Path) -> None:
    """`/sources` sagt **warum** — nicht nur `false`.

    Die Dokumentation versprach das seit Runde 3; der Grund kam nur nie an.
    Hier steht ein Name in der Kette, den es nicht gibt: Der Betreiber soll
    „unbekannter Name" lesen und nicht raten.
    """
    (volume / "sources.yaml").write_text(
        """
resolvers: [gibt-es-nicht]
quotes:    [prices-file-quote]
daily:     [yfinance]
fx:        [yfinance]
etf_meta:  []

providers:
  prices-file-quote:
    path: %s
"""
        % (volume / "closes.csv"),
        encoding="utf-8",
    )
    get_sources_config.cache_clear()
    _restart_chains()

    entries = client.get("/sources").json()["sources"]
    unusable = [entry for entry in entries if entry["name"] == "gibt-es-nicht"]

    assert unusable, "der konfigurierte Name fehlt in der Auskunft"
    assert unusable[0]["configured"] is False
    assert "keine bekannte Quelle" in unusable[0]["reason"], unusable[0]


def test_die_tagesreihe_erreicht_den_anbieter_auch_ohne_alias() -> None:
    """**Der Befund aus Runde 3, durch den echten Core-Verbraucher geprüft.**

    `DailyCloseSync` ist die Stelle, an der die App ihre Historie holt. Bis
    Runde 3 reichte sie nur das Symbol weiter, und `AAPL` — eine der fünf
    US-Börsen ohne Alias — ließ sich daraus nicht zurückrechnen: null
    Provider-Aufrufe, `None` als Ergebnis.

    Der Test führt deshalb **beide** Fälle durch denselben Weg: eine Börse mit
    Alias und eine ohne. Ein `hasattr` hätte beide grün gemeldet.
    """
    from app.plugin_adapters import DailyAdapter
    from app.plugins.yfinance_quotes import YFinancePlugin

    asked: list[str] = []

    class Binding:
        def fetch_daily_closes(self, symbol: str, start: str | None = None, **_: object):
            asked.append(symbol)
            return [{"date": "2026-01-03", "close": 1.0, "currency": "USD"}]

    adapter = DailyAdapter(YFinancePlugin(provider=Binding()), "XETR")

    without_alias = adapter.fetch_daily_closes(
        "AAPL", identity=ListedIdentity(ticker="AAPL", mic="XNAS")
    )
    with_alias = adapter.fetch_daily_closes(
            "EUNL.DE",
            identity=ListedIdentity(ticker="EUNL", mic="XETR"),
        )

    assert asked == ["AAPL", "EUNL.DE"], (
        "beide Börsen müssen den Anbieter erreichen — vorher war es keine"
    )
    assert without_alias and with_alias


def test_jede_eingebaute_quelle_spricht_in_jeder_rolle_den_vertrag() -> None:
    """**Der Wächter über die Zusage „Jede Quelle spricht den Vertrag".**

    `_build_one` adaptiert seit Runde 3 **jede** Quelle — der Adapter ruft
    also die Vertragsmethoden. Eine eingebaute Quelle, die noch die
    Core-Signaturen trägt, wird damit nicht etwa nicht adaptiert, sondern
    **falsch**: Der Adapter ruft `resolve()`, die Quelle hat nur
    `resolve_isin()`, und der `AttributeError` fliegt erst im Betrieb.

    Genau so lag `yahoo-search` bis T-35 in der Kette. `handles()` bekam ein
    `ResolveRequest` statt einer Zeichenkette und sagte trotzdem `True` — die
    Quelle nahm die Anfrage an und fiel danach um. Weil `CompositeResolver` in
    seiner Kaskade nichts abfängt, endete **jede** von OpenFIGI nicht
    auflösbare ISIN in einem `500`.

    Der Test prüft deshalb die Struktur, nicht einen Aufruf: Jede eingebaute
    Quelle muss in **jeder** Rolle, die sie führt, von der Vertragsklasse
    dieser Rolle abstammen. Das ist offline prüfbar und hätte den Fall
    gefunden, während ein Aufruftest ihn nur bei genau der richtigen ISIN
    gesehen hätte.
    """
    from stockinfo_plugin import (
        DailyCloseSource,
        FxSource,
        MetadataSource,
        QuoteSource,
        Resolver,
    )

    from app.config import Settings
    from app.plugin_adapters import unwrap
    from app.sources_registry import BUILTIN_SOURCES

    contracts = {
        "resolvers": Resolver,
        "etf_meta": MetadataSource,
        "quotes": QuoteSource,
        "daily": DailyCloseSource,
        "fx": FxSource,
    }
    settings = Settings()
    problems: list[str] = []

    for spec in BUILTIN_SOURCES:
        for role in sorted(spec.roles):
            source = unwrap(spec.build(role, {}, settings))
            expected = contracts[role]
            if not isinstance(source, expected):
                problems.append(
                    f"{spec.name!r} in der Rolle {role!r} ist ein "
                    f"{type(source).__name__} und kein {expected.__name__}"
                )

    assert not problems, "diese Quellen sprechen den Vertrag nicht:\n  " + "\n  ".join(
        problems
    )


# ─── Lebenszyklus: bauen, wiederverwenden, schließen ──────────────────────────


def _counting_source(counter: list[int]):
    """Ein Bauplan, der jede Konstruktion und jedes Schließen mitschreibt."""
    from stockinfo_plugin import QuoteSource

    class Counted(QuoteSource):
        api_version = 2
        name = "gezaehlt"
        cost = "free"

        def __init__(self, config=None) -> None:
            super().__init__(config)
            counter.append(1)
            self.closed = 0

        def handles(self, request) -> bool:
            return True

        def fetch(self, request):
            return None

        def close(self) -> None:
            self.closed += 1

    return Counted


@pytest.fixture
def counted_chain(tmp_path: Path):
    """Eine Kette aus genau einer mitzählenden Quelle."""
    from app.config import Settings
    from app.sources_config import load_sources_config
    from app.sources_registry import SourceSpec

    built: list[int] = []
    source_class = _counting_source(built)
    instances: list[object] = []

    def build(role, config, settings):
        source = source_class(config)
        instances.append(source)
        return source

    register_loaded(
        (SourceSpec("gezaehlt", frozenset({"quotes"}), build, loaded=True),)
    )
    (tmp_path / "sources.yaml").write_text("quotes: [gezaehlt]\n", encoding="utf-8")
    config = load_sources_config(tmp_path / "sources.yaml", Settings())
    return config, built, instances


def test_ein_lesezugriff_baut_keine_einzige_quelle(counted_chain) -> None:
    """**`GET /sources` ist eine Auskunft, kein Eingriff.**

    Bis Runde 3 rief der Endpunkt denselben Bauweg wie der Fachbetrieb und
    erzeugte für jede noch ungebaute Rolle Wegwerf-Instanzen — samt allem, was
    ein fremder Konstruktor tut: Datei öffnen, Verbindung aufbauen, Schlüssel
    prüfen. Ein Blick auf die Diagnoseseite hatte damit Seiteneffekte, und ein
    Monitoring, das sie im Minutentakt abruft, hätte sie im Minutentakt gehabt.

    Die zweite Hälfte ist Runde 5: Der ungebaute Zustand darf nicht
    `configured=true` behaupten. Er weiß es nicht — und sagt das jetzt.
    """
    from app.config import Settings
    from app.sources_registry import NOT_BUILT, describe_chain

    config, built, _ = counted_chain

    entries = describe_chain("quotes", config, Settings())

    assert built == [], "das Lesen hat eine Quelle konstruiert"
    assert [entry.name for entry in entries] == ["gezaehlt"]
    assert entries[0].configured is False, (
        "ungebaut heißt ungeprüft — vorher stand hier ein spekulatives true"
    )
    assert entries[0].reason == NOT_BUILT


def test_zweimal_bauen_liefert_dieselben_objekte(counted_chain) -> None:
    """Eine Kette wird **einmal** gebaut und danach wiederverwendet.

    Sonst entstünde bei jedem Request ein neuer Satz Quellen: neue
    Verbindungen, neue Dateihandles, ein wirkungsloser Circuit-Breaker — der
    zählt Fehlschläge pro Instanz, und eine frische Instanz hätte nie drei.
    """
    from app.config import Settings
    from app.sources_registry import build_chain

    config, built, _ = counted_chain

    first = build_chain("quotes", config, Settings())
    second = build_chain("quotes", config, Settings())

    assert built == [1], f"zweimal gebaut: {len(built)} Konstruktionen"
    assert [id(source) for source in first] == [id(source) for source in second]


def test_das_herunterfahren_schliesst_jede_quelle_genau_einmal(
    counted_chain,
) -> None:
    """`close()` steht seit T-27a im Vertrag — und wurde bis Runde 3 nie gerufen.

    **Genau einmal** ist die eigentliche Aussage: Dieselbe Quelle darf in
    mehreren Rollen stehen. Sie zweimal zu schließen wäre für ein Plugin, das
    eine Datei schließt, ein Fehler zweiter Ordnung — und einer, der erst beim
    Herunterfahren aufträte, wo ihn niemand mehr sieht.
    """
    from app.config import Settings
    from app.sources_registry import build_chain, close_all
    from app.plugin_adapters import unwrap

    config, _, instances = counted_chain
    build_chain("quotes", config, Settings())

    close_all()

    assert instances, "es wurde gar nichts gebaut"
    for source in instances:
        assert unwrap(source).closed == 1, "nicht oder mehrfach geschlossen"


def test_ein_gescheitertes_paket_kostet_nicht_die_gesunde_kette(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**Der Fall, für den die ganze Fehlertoleranz gebaut ist.**

    In `sources.yaml` steht ein Paket, das sich nicht installieren lässt.
    Daneben steht eine gesunde Kette aus einem Datei-Plugin. Erwartet wird:
    Der Start läuft durch, `/health` antwortet, `/sources` zeigt die gesunde
    Quelle — und der Betreiber sieht im Protokoll, was gefehlt hat.

    Bis Runde 5 endete das anders: Der fehlgeschlagene Installationslauf ließ
    den Kettennamen unbrauchbar werden, `build_chain` warf, und der Lifespan riss
    den ganzen Prozess mit. Wer ein Plugin eintrug, dessen Index gerade nicht
    erreichbar war, verlor seine Installation — statt dieses einen Plugins.

    Ohne Netz: `PIP_NO_INDEX` ist pips eigene Einstellung, kein Testhaken.
    """
    # `aus-dem-paket` **gäbe es nur**, wenn die Installation gelänge. Genau das
    # ist die Lage, die den Start bisher riss: Der Name steht in der Kette, die
    # Registry kennt ihn nicht, und der Bau warf.
    (volume / "sources.yaml").write_text(
        f"""
resolvers: [local-file]
quotes:    [aus-dem-paket, yaml-file]
etf_meta:  []
daily:     []
fx:        []

plugins:
  packages:
    - gibt-es-nicht==9.9.9

providers:
  local-file:
    path: {volume / "assets.yaml"}
  yaml-file:
    path: {volume / "assets.yaml"}
""",
        encoding="utf-8",
    )

    monkeypatch.setenv("PIP_NO_INDEX", "1")
    monkeypatch.setenv("DATABASE_PATH", str(volume / "stockinfo.db"))
    from app.config import get_settings
    from app.container import get_cached_quote_service

    get_settings.cache_clear()
    get_sources_config.cache_clear()
    get_cached_quote_service.cache_clear()

    try:
        with TestClient(app) as client:
            assert client.get("/health").status_code == 200, (
                "die App ist wegen eines fremden Pakets nicht hochgekommen"
            )
            sources = client.get("/sources").json()
    finally:
        get_settings.cache_clear()

    entries = {
        entry["name"]: entry
        for role in sources.values()
        if isinstance(role, list)
        for entry in role
    }

    assert "local-file" in entries, f"die gesunde Quelle fehlt: {sorted(entries)}"
    assert "yaml-file" in entries, "der gesunde Fallback fehlt"

    missing = entries.get("aus-dem-paket")
    assert missing is not None, (
        "der Name aus dem gescheiterten Paket wird verschwiegen — "
        f"gemeldet wurden: {sorted(entries)}"
    )
    assert missing["configured"] is False
    assert "keine bekannte Quelle" in missing["reason"], missing["reason"]


def test_ein_resolver_ohne_typdeklaration_darf_keine_gattung_liefern() -> None:
    """**Negative Gegenprobe zu Codex' Befund aus Runde 5.**

    `ResolverAdapter._translate` schaltete die Antwortprüfung mit
    ``and declared_types`` ausgerechnet bei der **leeren** Menge ab. Eine
    Quelle ohne jede Deklaration durfte damit `crypto` liefern — genau das
    Gegenteil dessen, was „nichts zugesagt" heißt.

    Der Mutant ist minimal falsch: Er deklariert eine Form, aber keine
    Gattung, und liefert eine. Alles andere an ihm stimmt.
    """

    class DeclaresNoTypes(Resolver):
        name = "ohne-typen"
        api_version = 2
        SUPPORTED_KINDS = frozenset({"pair"})
        SUPPORTED_TYPES = frozenset()

        def handles(self, request) -> bool:
            return True

        def resolve(self, request):
            return Resolved(
                identity=PairIdentity(base="BTC", quote_currency="EUR"),
                name="Bitcoin",
                instrument_type="crypto",
            )

    answer = ResolverAdapter(DeclaresNoTypes(), "XETR").resolve_symbol("BTC-EUR")

    assert isinstance(answer, Unavailable), (
        "eine nicht deklarierte Gattung ist ein Befund, kein stiller Treffer"
    )
    assert "crypto" in answer.error


def test_dieselbe_quelle_mit_deklarierter_gattung_kommt_durch() -> None:
    """Die Gegenprobe zum Mutanten — sonst prüfte er nur, dass irgendetwas bricht."""

    class DeclaresItsType(Resolver):
        name = "mit-typ"
        api_version = 2
        SUPPORTED_KINDS = frozenset({"pair"})
        SUPPORTED_TYPES = frozenset({"crypto"})

        def handles(self, request) -> bool:
            return True

        def resolve(self, request):
            return Resolved(
                identity=PairIdentity(base="BTC", quote_currency="EUR"),
                name="Bitcoin",
                instrument_type="crypto",
            )

    answer = ResolverAdapter(DeclaresItsType(), "XETR").resolve_symbol("BTC-EUR")

    assert answer.kind == "pair"
    assert answer.type == "crypto"


# ─── Wessen Ablehnung ist es? (T-31, Matrix #6) ───────────────────────────────


class _Declines(Resolver):
    """Eine Quelle, die ein Papier erkennt und nicht führt."""

    name = "lehnt-ab"
    api_version = 2
    SUPPORTED_KINDS = frozenset({"listed"})
    SUPPORTED_TYPES = frozenset({"stock"})

    def __init__(self, instrument_type: str) -> None:
        super().__init__(None)
        self._type = instrument_type

    def handles(self, request) -> bool:
        return True

    def resolve(self, request):
        return Unsupported(instrument_type=self._type)


def test_eine_gattung_aus_dem_katalog_bleibt_eine_frage_an_die_naechste_quelle() -> None:
    """**Ein Plugin spricht nur über sich selbst.**

    „Ich führe keine Anleihen" ist eine Aussage über *diese* Quelle. Würde der
    Host sie unverändert weiterreichen, läse der Benutzer „Anleihen werden
    nicht unterstützt" — über eine Gattung, die seit T-31 im Katalog steht und
    die OpenFIGI im selben Lauf liefern kann.

    Deshalb `NotResponsible`: Die Kette geht weiter, und bleibt sie leer, ist
    das ein 404 über *dieses Papier* und keine Grundsatzaussage über Anleihen.
    """
    answer = ResolverAdapter(_Declines("bond"), "XETR").resolve_symbol("DE0001102531")

    assert isinstance(answer, NotResponsible), (
        "die Ablehnung einer einzelnen Quelle wird zur Aussage der ganzen App"
    )
    assert "bond" in answer.reason


def test_eine_gattung_ausserhalb_des_katalogs_bleibt_eine_ablehnung() -> None:
    """Die Gegenprobe — sonst schwächte der Fall darüber jede Ablehnung ab.

    Ein Index steht in keinem Katalog dieser App, und daran ändert auch die
    nächste Quelle nichts. Diese Antwort muss durchkommen, sonst ist Matrix
    `#6` wieder dort, wo sie war: beim Zufallsbefund „kein Börsensuffix".
    """
    answer = ResolverAdapter(_Declines("index"), "XETR").resolve_symbol("^GDAXI")

    assert isinstance(answer, Unsupported)
    assert answer.instrument_type == "index"


def test_eine_nicht_deklarierte_gattung_erreicht_die_metadatenquelle_nicht() -> None:
    """**Codex `#4` aus Runde 5, als Beleg statt als Zusage.**

    Die Metadatenkaskade lief bis dahin an der Fähigkeitsdeklaration vorbei:
    `MetadataAdapter.fetch_etf` rief den Vorfilter gar nicht. Dass es fachlich
    nicht auffiel, lag an einer **zweiten** Prüfung im Service
    (`instrument_type == "etf"`) — eine Regel an zwei Orten, von denen nur
    eine die Zusage der Quelle liest. Fällt die eine weg, fragt die App eine
    Anleihe nach ihrer TER.

    Geprüft wird deshalb nicht das Ergebnis, sondern **ob überhaupt gefragt
    wurde**: Der Vorfilter soll die Anfrage sparen, nicht ihre Antwort
    verwerfen.
    """

    class CountingEtfSource(MetadataSource):
        name = "nur-etf"
        api_version = 2
        SUPPORTED_KINDS = frozenset({"listed"})
        SUPPORTED_TYPES = frozenset({"etf"})

        def __init__(self) -> None:
            super().__init__()
            self.asked = 0

        def fetch(self, request):
            self.asked += 1
            return []

    source = CountingEtfSource()
    adapter = MetadataAdapter(source, "XETR")
    listing = ListedIdentity(ticker="EUNL", mic="XETR", isin="IE00B4L5Y983")

    adapter.fetch_etf(
        "IE00B4L5Y983", "EUNL.DE", identity=listing, instrument_type="bond"
    )
    assert source.asked == 0, "eine Anleihe darf die ETF-Quelle nicht kosten"

    adapter.fetch_etf(
        "IE00B4L5Y983", "EUNL.DE", identity=listing, instrument_type="etf"
    )
    assert source.asked == 1, "die deklarierte Gattung wird sehr wohl gefragt"
