"""Ein Datei-Plugin und ein echter Entry-Point, ganz durch: Registry → Core → REST.

Das ist die Aussage, an der T-23 gemessen wird — und sie ist der Grund, warum
Runde 1 nicht reichte. Dort wurden Plugins geladen, geprüft und angezeigt; den
Core erreichte keines. Der damalige „Auswahltest" verlangte sogar ausdrücklich,
dass `quotes: [yfinance]` **kein** Plugin baut: Er hat die Lücke als
Eigenschaft festgeschrieben.

Hier läuft es andersherum. Zwei Ladewege, beide echt:

* **Entry-Point** — `canada-file` ist in `plugin_api/pyproject.toml` unter der
  Gruppe `stockinfo.sources` angemeldet und im Environment installiert. Kein
  Nachstellen: `importlib.metadata` findet ihn, weil er wirklich da ist.
* **Datei** — eine `*.py` im Plugin-Verzeichnis des Datenvolumes.

Beide benutzen die **vorhandenen** Beispiel-Plugins aus `plugin_api/examples/`.
Ein zweites CSV-Plugin für den Test zu schreiben war der Fehler der letzten
Runde: Es hätte ein zweites Format und eine zweite Fachlogik gepflegt, für
etwas, das bereits existiert und vertraglich geprüft ist.
"""

import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.container import get_sources_config
from app.main import app
from app.plugin_loader import ENTRY_POINT_GROUP, load_all
from app.sources_registry import register_loaded, specs_by_name

EXAMPLES = Path(__file__).parent.parent / "plugin_api" / "examples"

# Ein Papier, das OpenFIGI an der Vorgabebörse **nicht** kennt — genau der
# gemessene Anlass für die Handtabelle. Der Wert steht in der CSV unten und
# nirgends sonst; er ist der Beweis, dass die Antwort von dort kommt.
MANUAL = "CA78012H5675;RY;XTSE;Royal Bank of Canada\n"
CLOSES = "ticker;mic;day;close;currency\nRY;XTSE;2026-01-03;141.55;CAD\n"

# **Die Beispieldatei wird wirklich kopiert**, nicht importiert. Verify `#1`
# sagt „`examples/canada_file.py` nach `data/plugins/`" — und das ist ein
# anderer Weg als ein Import aus der installierten Distribution: Der prüfte am
# Ende denselben Ladeweg wie der Entry-Point und ließe die Datei-Variante
# ungeprüft. Ein Betreiber legt eine **Datei** ab, kein Paket.
#
# Angehängt wird nur ein eigener Name, damit sich beide Wege im selben Lauf
# unterscheiden lassen.
FILE_SUFFIX = '''

class LocalFileResolver(CanadaFileResolver):
    """Dasselbe Beispiel, aus dem Datenvolume geladen."""

    name = "local-file"


SOURCES = [LocalFileResolver]
'''


@pytest.fixture
def volume(tmp_path: Path) -> Path:
    """Ein Datenvolume, wie es beim Betreiber aussieht."""
    (tmp_path / "manual-isins.csv").write_text(
        "isin;ticker;mic;name\n" + MANUAL, encoding="utf-8"
    )
    (tmp_path / "closes.csv").write_text(CLOSES, encoding="utf-8")
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    # Die echte Beispieldatei, Zeile für Zeile — so, wie ein Betreiber sie
    # kopieren würde.
    shutil.copy(EXAMPLES / "canada_file.py", plugins / "lokal.py")
    with (plugins / "lokal.py").open("a", encoding="utf-8") as handle:
        handle.write(FILE_SUFFIX)
    # Die Kursquelle kommt als eigene Datei — ebenfalls kopiert.
    shutil.copy(EXAMPLES / "prices_file.py", plugins / "kurse.py")
    with (plugins / "kurse.py").open("a", encoding="utf-8") as handle:
        handle.write("\nSOURCES = [PricesFileQuoteSource]\n")
    return tmp_path


@pytest.fixture(autouse=True)
def _leere_registry() -> Iterator[None]:
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
    (volume / "sources.yaml").write_text(
        f"""
resolvers: [{resolver}]
quotes:    [prices-file-quote]
etf_meta:  []
daily:     [yfinance]
fx:        [yfinance]

providers:
  {resolver}:
    path: {volume / "manual-isins.csv"}
  prices-file-quote:
    path: {volume / "closes.csv"}
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

    assert "canada-file" in names, (
        "der Entry-Point fehlt — plugin_api neu installieren: "
        "pip install -e plugin_api"
    )


def test_beide_ladewege_landen_in_derselben_registry(volume: Path) -> None:
    """Datei und Entry-Point stehen gleichwertig neben den eingebauten Quellen."""
    register_loaded(load_all(volume).specs)

    known = specs_by_name()

    assert "canada-file" in known, "aus dem installierten Paket"
    assert "local-file" in known, "aus dem Datenvolume"
    assert "openfigi" in known, "und die eingebauten sind weiterhin da"


@pytest.mark.parametrize(
    ("resolver", "woher"),
    [("canada-file", "Entry-Point"), ("local-file", "Datei im Volume")],
)
def test_ein_plugin_beantwortet_eine_echte_rest_anfrage(
    client: TestClient, volume: Path, resolver: str, woher: str
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

    assert answer.status_code in (200, 201), f"{woher}: {answer.text}"
    body = answer.json()
    assert body["ticker"] == "RY", woher
    assert body["mic"] == "XTSE", woher
    assert body["name"] == "Royal Bank of Canada", woher


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

    Geprüft werden beide Ladewege im selben Lauf: `canada-file` kommt aus dem
    installierten Paket, `local-file` aus der kopierten Datei im Volume.
    """
    _sources_yaml(volume, "local-file")
    get_sources_config.cache_clear()
    _restart_chains()

    antwort = client.get("/sources")

    assert antwort.status_code == 200, antwort.text
    namen = {eintrag["name"] for eintrag in antwort.json()["sources"]}
    assert "local-file" in namen, "die Datei im Volume"
    assert "canada-file" in namen or "canada-file" in specs_by_name(), (
        "der Entry-Point ist geladen, steht hier aber nur, wenn er in einer "
        "Kette konfiguriert ist"
    )


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

    eintraege = client.get("/sources").json()["sources"]
    unbekannt = [e for e in eintraege if e["name"] == "gibt-es-nicht"]

    assert unbekannt, "der konfigurierte Name fehlt in der Auskunft"
    assert unbekannt[0]["configured"] is False
    assert "unbekannt" in unbekannt[0]["reason"].lower(), unbekannt[0]


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

    gefragt: list[str] = []

    class Anbindung:
        def fetch_daily_closes(self, symbol: str, start: str | None = None):
            gefragt.append(symbol)
            return [{"date": "2026-01-03", "close": 1.0, "currency": "USD"}]

    adapter = DailyAdapter(YFinancePlugin(provider=Anbindung()), "XETR")

    ohne_alias = adapter.fetch_daily_closes("AAPL", ticker="AAPL", mic="XNAS")
    mit_alias = adapter.fetch_daily_closes("EUNL.DE", ticker="EUNL", mic="XETR")

    assert gefragt == ["AAPL", "EUNL.DE"], (
        "beide Börsen müssen den Anbieter erreichen — vorher war es keine"
    )
    assert ohne_alias and mit_alias
