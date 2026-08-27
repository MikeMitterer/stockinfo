"""Quellen kommen aus einer Datei, nicht aus der Verdrahtung (T-22).

Bis hierher stand die Kette als `if`-Kaskade in `app/container.py`. Diese Tests
prüfen die Zeilen der Verify-Matrix von T-22 — und zwar so, dass sie **rot
werden, wenn die Kaskade zurückkommt**: Sie stellen eine Konfiguration her und
verlangen, dass sich das Ergebnis danach richtet.
"""

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.container import _build_resolver, get_sources_config
from app.main import app
from app.sources_config import (
    DEFAULT_CHAINS,
    UnknownSourceError,
    load_sources_config,
)
from app.sources_registry import SourceSpec, build_chain, is_configured


def _write(path: Path, content: dict) -> Path:
    target = path / "sources.yaml"
    target.write_text(yaml.safe_dump(content), encoding="utf-8")
    return target


def test_eine_vertauschte_reihenfolge_gilt(tmp_path: Path) -> None:
    """`#1`: Die Datei bestimmt die Rangfolge, nicht der Quelltext.

    Der Kern des Tickets. Solange die Verdrahtung die Auswahl trifft, ist jede
    Konfigurationsdatei Zierde — dieser Test wäre dann rot.
    """
    config = load_sources_config(
        _write(tmp_path, {"resolvers": ["yahoo-search", "openfigi"]})
    )

    assert config.chain("resolvers") == ("yahoo-search", "openfigi")

    built = build_chain("resolvers", config.chain("resolvers"), config, "XETR", False)
    assert [type(source).__name__ for source in built] == [
        "YFinanceResolver",
        "OpenFigiResolver",
    ]


def test_ein_optionaler_schluessel_schaltet_nichts_ab(tmp_path: Path) -> None:
    """`#2`: OpenFIGI arbeitet anonym — ohne Key bleibt die Quelle aktiv.

    `is_configured()` fragt „kann ich arbeiten", nicht „ist alles gesetzt". Ein
    Wächter, der jeden fehlenden Schlüssel als Ausfall wertet, nähme dem
    Betreiber genau die Quelle, die auch ohne Anmeldung liefert.
    """
    config = load_sources_config(_write(tmp_path, {"resolvers": ["openfigi"]}))

    built = build_chain("resolvers", ("openfigi",), config, "XETR", False)

    assert [type(source).__name__ for source in built] == ["OpenFigiResolver"]


def test_ein_pflichtiger_schluessel_nimmt_die_quelle_aus_der_kette() -> None:
    """`#2b`: Fehlt ein **pflichtiger** Schlüssel, fällt die Quelle raus.

    Und zwar **ohne Fehler**: Eine unkonfigurierte Quelle ist ein
    Betriebszustand, kein Absturz. Der Betreiber sieht sie in `/sources` mit
    `configured: false` und weiß, woran es liegt.
    """
    paid = SourceSpec(
        "teuer", frozenset({"quotes"}), lambda *_: object(), needs=("api_key",)
    )

    assert is_configured(paid, {}) is False
    assert is_configured(paid, {"api_key": ""}) is False, "leer ist wie fehlend"
    assert is_configured(paid, {"api_key": "abc"}) is True


def test_ohne_datei_gelten_die_vorgaben(tmp_path: Path) -> None:
    """`#3`: Eine frische Installation ist der Normalfall, nicht der Fehlerfall."""
    config = load_sources_config(tmp_path / "gibt-es-nicht.yaml")

    assert config.path is None
    assert config.chain("resolvers") == DEFAULT_CHAINS["resolvers"]


def test_ein_tippfehler_nennt_den_namen_und_die_verfuegbaren(tmp_path: Path) -> None:
    """`#4`: „Unbekannte Quelle" allein lässt den Benutzer raten.

    Er muss wissen, **ob er sich vertippt hat oder ein Paket fehlt** — und
    dafür braucht er beides: seinen Namen und die Liste der bekannten.
    """
    config = load_sources_config(_write(tmp_path, {"resolvers": ["openfgi"]}))

    with pytest.raises(UnknownSourceError) as rejected:
        build_chain("resolvers", config.chain("resolvers"), config, "XETR", False)

    message = str(rejected.value)
    assert "openfgi" in message, "der eigene Tippfehler muss dastehen"
    assert "openfigi" in message, "und die richtige Schreibweise daneben"


def test_die_datei_traegt_verweise_statt_schluessel(tmp_path: Path) -> None:
    """`#5`: Diese Datei soll in ein Issue kopierbar sein.

    Das ist der praktische Grund für die Trennung von Umgebung und Datei: Wenn
    jemand in Kanada eine funktionierende Kette gefunden hat, ist sie das
    Artefakt, das er weitergibt — und es darf keinen Schlüssel enthalten.
    """
    written = _write(
        tmp_path,
        {"resolvers": ["openfigi"], "providers": {"openfigi": {"api_key": "${FIGI_X}"}}},
    )

    assert "${FIGI_X}" in written.read_text(encoding="utf-8")
    assert "geheim" not in written.read_text(encoding="utf-8")


def test_ein_verweis_wird_aus_der_umgebung_aufgeloest(
    tmp_path: Path, monkeypatch
) -> None:
    """Und beim Lesen steht der Wert da, nicht der Verweis.

    Ohne die Auflösung bekäme die Quelle die Zeichenkette `"${FIGI_X}"` als
    Schlüssel und schickte sie an die API — der Fehler käme von außen zurück,
    wo ihn niemand mehr zuordnet.
    """
    monkeypatch.setenv("FIGI_X", "geheim")
    config = load_sources_config(
        _write(tmp_path, {"providers": {"openfigi": {"api_key": "${FIGI_X}"}}})
    )

    assert config.config_for("openfigi") == {"api_key": "geheim"}


def test_ein_fehlender_verweis_wird_none_und_nicht_text(tmp_path: Path) -> None:
    """Die Gegenrichtung — sonst reist der Platzhalter als Schlüssel weiter."""
    config = load_sources_config(
        _write(tmp_path, {"providers": {"openfigi": {"api_key": "${GIBT_ES_NICHT}"}}})
    )

    assert config.config_for("openfigi")["api_key"] is None


def test_dieselbe_quelle_baut_je_rolle_einen_anderen_typ(tmp_path: Path) -> None:
    """yfinance beantwortet vier Fragen — mit zwei verschiedenen Klassen.

    Für `etf_meta` ist die Antwort ein `YFinanceEtfEnricher`, für `quotes` ein
    `YFinanceProvider`. Ein Bauplan, der die Rolle nicht kennt, hätte der
    ETF-Kette ein Objekt ohne `is_responsible` gegeben — und der Fehler wäre
    erst beim ersten ETF-Abruf aufgefallen.
    """
    config = load_sources_config(tmp_path / "keine.yaml")

    etf = build_chain("etf_meta", ("yfinance",), config, "XETR", False)
    quotes = build_chain("quotes", ("yfinance",), config, "XETR", False)

    assert type(etf[0]).__name__ == "YFinanceEtfEnricher"
    assert type(quotes[0]).__name__ == "YFinanceProvider"


def test_eine_rolle_nimmt_keine_fremde_quelle_auf(tmp_path: Path) -> None:
    """`justetf` in der Kurskette ist ein Konfigurationsfehler, kein Absturz.

    Die Quelle wird übersprungen und protokolliert. Sie zu bauen hieße, ein
    Objekt in eine Kette zu setzen, dessen Vertrag dort nicht gilt.
    """
    config = load_sources_config(tmp_path / "keine.yaml")

    assert build_chain("quotes", ("justetf",), config, "XETR", False) == []


def test_der_leseweg_zeigt_die_kette(tmp_path: Path, monkeypatch) -> None:
    """`#1`/`#2` über HTTP: Was der Betreiber tatsächlich zu sehen bekommt.

    Ohne diesen Weg müsste er die Kette aus dem Log oder dem Quelltext
    erschließen — genau der Zustand, den T-22 abschafft.
    """
    _write(tmp_path, {"resolvers": ["yahoo-search", "openfigi"]})
    (tmp_path / "stockinfo.db").touch()
    app.dependency_overrides[get_settings] = lambda: Settings(
        database_path=str(tmp_path / "stockinfo.db")
    )
    get_sources_config.cache_clear()

    body = TestClient(app).get("/sources").json()

    app.dependency_overrides.clear()
    get_sources_config.cache_clear()

    resolvers = [row for row in body["sources"] if row["role"] == "resolvers"]
    assert [row["name"] for row in resolvers] == ["yahoo-search", "openfigi"]
    assert all(row["configured"] for row in resolvers)
    assert body["config_path"].endswith("sources.yaml")


def test_die_verdrahtung_liest_die_konfiguration(tmp_path: Path, monkeypatch) -> None:
    """Die Gegenprobe zur Kaskade: `_chain` folgt der Datei.

    Solange irgendwo noch ein `if strict_exchange` über die Kette entscheidet,
    ist dieser Test rot — und genau das soll er.

    **Zwei Korrekturen, beide von einem Mutanten erzwungen.** Die erste Fassung
    trug nur `yahoo-search` ein — eine umgedrehte Einerliste ist dieselbe
    Liste, der Mutant blieb unsichtbar. Und sie rief `_chain()` statt
    `_build_resolver()`, also eine Ebene **unter** der Verdrahtung: Ein Fehler
    genau dort, wo die Kette zum Resolver wird, wäre durchgegangen. Geprüft
    wird jetzt das Objekt, das die App tatsächlich benutzt.
    """
    _write(tmp_path, {"resolvers": ["yahoo-search", "openfigi"]})
    monkeypatch.setattr(
        "app.container.get_settings",
        lambda: Settings(database_path=str(tmp_path / "stockinfo.db")),
    )
    get_sources_config.cache_clear()

    resolver = _build_resolver()
    get_sources_config.cache_clear()

    assert [type(inner).__name__ for inner in resolver._resolvers] == [
        "YFinanceResolver",
        "OpenFigiResolver",
    ]
