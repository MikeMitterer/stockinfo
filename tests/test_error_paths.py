"""Was `404` und `502` an den Fehlerwegen bedeuten (T-44).

**Die Unterscheidung ist der ganze Ticketinhalt**, und sie lässt sich nur am
echten HTTP-Weg prüfen: Ob die App einen sauberen Nichttreffer von einer
Störung trennt, entscheidet sich in vier Schichten hintereinander — Plugin,
Adapter, Kaskade, Router. Ein Unit-Test in einer davon belegt für die anderen
drei nichts.

Geprüft wird deshalb je Route dasselbe Paar:

============ ================================================================
`404`        Die Kette ist **vollständig** durchgelaufen, jede Quelle hat
             geantwortet, keine führt die Sache. Das ist eine Auskunft.
`502`        Mindestens eine Quelle war gestört. Dann ist offen, ob es die
             Sache gibt — und ein `404` behauptete etwas, das die Kette gar
             nicht erhoben hat.
============ ================================================================

Dazu der gemischte Fall: **eine** gestörte Quelle neben einem sauberen
Nichttreffer ergibt `502`. Er ist der eigentliche Prüfstein, denn er
unterscheidet „irgendeine hat geantwortet" von „alle haben geantwortet".
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
    get_sources_config,
)
from app.main import app

_SERVICE_CACHES = (
    get_cached_quote_service,
    get_daily_history_service,
    get_fx_service,
)

SAMPLE = Path(__file__).resolve().parents[1] / "_tickets" / "T-37-single-file-sample.yaml"

# Eine Quelle, die **gestört** ist: Sie ist zuständig und kann nicht antworten.
# Das Gegenstück zu `answers-never` aus `test_yaml_profile`, das sauber
# „habe ich nicht" sagt — der Unterschied zwischen beiden ist das Thema.
_DISTURBED = '''
from stockinfo_plugin import DailyCloseSource, FxSource, Unavailable


class Disturbed(DailyCloseSource, FxSource):
    """Zustaendig, aber gestoert — in beiden Rollen."""

    name = "disturbed"
    api_version = 2
    SUPPORTED_KINDS = frozenset({"listed", "pair", "isin_only"})
    SUPPORTED_TYPES = frozenset({"stock", "etf", "etc", "fund", "crypto", "bond"})

    def handles(self, request) -> bool:
        return True

    def fetch_daily(self, request):
        return Unavailable("Netz weg")

    def fetch_rate(self, request):
        return Unavailable("Netz weg")


SOURCES = [Disturbed]
'''

# Eine Quelle, die sauber „habe ich nicht" sagt.
_SILENT = '''
from stockinfo_plugin import DailyCloseSource, FxSource, NotFound


class Silent(DailyCloseSource, FxSource):
    """Zustaendig, hat die Sache aber nicht — sauberer Nichttreffer."""

    name = "silent"
    api_version = 2
    SUPPORTED_KINDS = frozenset({"listed", "pair", "isin_only"})
    SUPPORTED_TYPES = frozenset({"stock", "etf", "etc", "fund", "crypto", "bond"})

    def handles(self, request) -> bool:
        return True

    def fetch_daily(self, request):
        return NotFound()

    def fetch_rate(self, request):
        return NotFound()


SOURCES = [Silent]
'''

_BOND = "DE0001102531"


@pytest.fixture
def volume(tmp_path: Path) -> Path:
    """Ein Volume mit beiden Prüfquellen — **vor** dem Start abgelegt."""
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    (plugins / "disturbed.py").write_text(_DISTURBED, encoding="utf-8")
    (plugins / "silent.py").write_text(_SILENT, encoding="utf-8")
    return tmp_path


@pytest.fixture
def client(volume: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("DATABASE_PATH", str(volume / "stockinfo.db"))
    for cache in (get_settings, get_sources_config, *_SERVICE_CACHES):
        cache.cache_clear()
    with TestClient(app) as opened:
        yield opened
    for cache in (get_settings, get_sources_config, *_SERVICE_CACHES):
        cache.cache_clear()


def _profile(volume: Path, chains: dict[str, list[str]]) -> None:
    """Schreibt eine Kette und baut sie neu — wie ein Neustart es täte.

    Die Ketten hängen an der **Identität** der Konfiguration; wird sie neu
    gelesen, baut die Registry neu. Ohne diesen Schritt misst jeder Test unten
    die Vorgabekette und damit das Netz.
    """
    lines = [f"{role}: [{', '.join(sources)}]" for role, sources in chains.items()]
    lines += ["", "providers:", "  yaml-file:", f"    path: {SAMPLE}"]
    (volume / "sources.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")

    for cache in _SERVICE_CACHES:
        cache.cache_clear()
    get_sources_config.cache_clear()


# ─── Die Tagesreihe ───────────────────────────────────────────────────────────


def test_ohne_reihe_und_ohne_stoerung_antwortet_die_route_mit_404(
    client: TestClient, volume: Path
) -> None:
    """Keine Quelle führt die Reihe — das ist eine Auskunft, kein Ausfall."""
    _profile(
        volume,
        {"resolvers": ["yaml-file"], "quotes": ["yaml-file"], "daily": ["silent"]},
    )

    response = client.get(f"/quote/{_BOND}/daily", params={"period": "1m"})

    assert response.status_code == 404, response.text
    assert response.json()["code"] == "daily_series_not_found"


def test_eine_stoerung_antwortet_mit_502(client: TestClient, volume: Path) -> None:
    """Die Gegenprobe: Gestört heißt weiterhin gestört."""
    _profile(
        volume,
        {"resolvers": ["yaml-file"], "quotes": ["yaml-file"], "daily": ["disturbed"]},
    )

    response = client.get(f"/quote/{_BOND}/daily", params={"period": "1m"})

    assert response.status_code == 502, response.text
    assert response.json()["code"] == "daily_source_unavailable"


def test_eine_stoerung_neben_einem_nichttreffer_bleibt_502(
    client: TestClient, volume: Path
) -> None:
    """**Der Prüfstein.** Eine der beiden Quellen war gestört.

    Vielleicht hätte gerade sie die Reihe gehabt. Ein `404` behauptete hier
    „gibt es nicht" auf einer Grundlage, die die Kette nicht erhoben hat.
    """
    _profile(
        volume,
        {
            "resolvers": ["yaml-file"],
            "quotes": ["yaml-file"],
            "daily": ["silent", "disturbed"],
        },
    )

    response = client.get(f"/quote/{_BOND}/daily", params={"period": "1m"})

    assert response.status_code == 502, response.text


# ─── Der Devisenkurs ──────────────────────────────────────────────────────────


def test_ein_nicht_gefuehrtes_paar_antwortet_mit_404(
    client: TestClient, volume: Path
) -> None:
    _profile(volume, {"fx": ["silent"]})

    response = client.get("/fx", params={"base": "CAD", "quote": "USD"})

    assert response.status_code == 404, response.text
    assert response.json()["code"] == "fx_pair_not_found"
    assert response.json()["params"] == {"base": "CAD", "quote": "USD"}


def test_eine_gestoerte_devisenquelle_antwortet_mit_502(
    client: TestClient, volume: Path
) -> None:
    _profile(volume, {"fx": ["disturbed"]})

    response = client.get("/fx", params={"base": "CAD", "quote": "USD"})

    assert response.status_code == 502, response.text
    assert response.json()["code"] == "fx_source_unavailable"


def test_eine_gestoerte_devisenquelle_neben_einem_nichttreffer_bleibt_502(
    client: TestClient, volume: Path
) -> None:
    _profile(volume, {"fx": ["silent", "disturbed"]})

    response = client.get("/fx", params={"base": "CAD", "quote": "USD"})

    assert response.status_code == 502, response.text


# ─── Die Kennung an der Eingangstür ───────────────────────────────────────────


def test_eine_unbrauchbare_isin_wird_mit_kennung_abgelehnt(client: TestClient) -> None:
    """`422` mit Kennung statt deutschem Fließtext.

    Das Dashboard erreicht diese Stelle nicht, weil es ISIN und Symbol selbst
    unterscheidet — ein anderer Client tut das nicht, und ihm nützt
    „Ungültiges ISIN-Format" nichts.
    """
    response = client.get("/quote/BTC-EUR")

    assert response.status_code == 422, response.text
    assert response.json()["detail"]["code"] == "invalid_isin_format"
    assert response.json()["detail"]["params"] == {"isin": "BTC-EUR"}


def test_ein_unbrauchbarer_waehrungscode_wird_mit_kennung_abgelehnt(
    client: TestClient,
) -> None:
    response = client.get("/fx", params={"base": "EURO", "quote": "USD"})

    assert response.status_code == 422, response.text
    assert response.json()["code"] == "invalid_currency_code"


# ─── Die Gegenprobe zur Prüfeinrichtung ───────────────────────────────────────


def test_das_profil_greift_wirklich(client: TestClient, volume: Path) -> None:
    """**Ohne diese Zeile beweist keine der obigen etwas.**

    Griffe `_profile` nicht, liefen alle Fälle gegen die Vorgabekette — und ein
    `404` oder `502` käme dann von irgendwoher. Diese Prüfung sagt, dass die
    geschriebene Kette wirklich die laufende ist.
    """
    _profile(volume, {"fx": ["silent"]})

    entries = client.get("/sources").json()["sources"]

    assert [entry["name"] for entry in entries if entry["role"] == "fx"] == ["silent"]
