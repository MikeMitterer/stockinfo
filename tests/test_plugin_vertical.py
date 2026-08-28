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

# Die Datei im Plugin-Verzeichnis **benutzt** das vorhandene Beispiel, statt es
# nachzubauen. Sie gibt ihm nur einen eigenen Namen, damit sich Datei- und
# Entry-Point-Weg im selben Lauf unterscheiden lassen.
FILE_PLUGIN = '''
from stockinfo_plugin_examples.canada_file import CanadaFileResolver
from stockinfo_plugin_examples.prices_file import PricesFileQuoteSource


class LocalFileResolver(CanadaFileResolver):
    """Dasselbe Beispiel, aus dem Datenvolume geladen."""

    name = "local-file"


SOURCES = [LocalFileResolver, PricesFileQuoteSource]
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
    (plugins / "lokal.py").write_text(FILE_PLUGIN, encoding="utf-8")
    return tmp_path


@pytest.fixture(autouse=True)
def _leere_registry() -> Iterator[None]:
    """Kein Test erbt die geladenen Plugins eines anderen."""
    register_loaded(())
    yield
    register_loaded(())
    get_sources_config.cache_clear()


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
