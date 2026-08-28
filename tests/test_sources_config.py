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

from app.plugin_adapters import unwrap
from app.config import Settings
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
        _write(tmp_path, {"resolvers": ["yahoo-search", "openfigi"]}), Settings()
    )

    assert config.chain("resolvers") == ("yahoo-search", "openfigi")

    built = build_chain("resolvers", config, Settings())
    assert [type(unwrap(source)).__name__ for source in built] == [
        "YFinanceResolver",
        "OpenFigiResolverPlugin",
    ]


def test_ein_optionaler_schluessel_schaltet_nichts_ab(tmp_path: Path) -> None:
    """`#2`: OpenFIGI arbeitet anonym — ohne Key bleibt die Quelle aktiv.

    `is_configured()` fragt „kann ich arbeiten", nicht „ist alles gesetzt". Ein
    Wächter, der jeden fehlenden Schlüssel als Ausfall wertet, nähme dem
    Betreiber genau die Quelle, die auch ohne Anmeldung liefert.
    """
    config = load_sources_config(_write(tmp_path, {"resolvers": ["openfigi"]}), Settings())

    built = build_chain("resolvers", config, Settings())

    assert [type(unwrap(source)).__name__ for source in built] == ["OpenFigiResolverPlugin"]


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
    config = load_sources_config(tmp_path / "gibt-es-nicht.yaml", Settings())

    assert config.path is None
    assert config.chain("resolvers") == DEFAULT_CHAINS["resolvers"]


def test_ein_tippfehler_nennt_den_namen_und_die_verfuegbaren(tmp_path: Path) -> None:
    """`#4`: „Unbekannte Quelle" allein lässt den Benutzer raten.

    Er muss wissen, **ob er sich vertippt hat oder ein Paket fehlt** — und
    dafür braucht er beides: seinen Namen und die Liste der bekannten.
    """
    config = load_sources_config(_write(tmp_path, {"resolvers": ["openfgi"]}), Settings())

    with pytest.raises(UnknownSourceError) as rejected:
        build_chain("resolvers", config, Settings())

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
        _write(tmp_path, {"providers": {"openfigi": {"api_key": "${FIGI_X}"}}}), Settings()
    )

    assert config.config_for("openfigi") == {"api_key": "geheim"}


def test_ein_fehlender_verweis_wird_none_und_nicht_text(tmp_path: Path) -> None:
    """Die Gegenrichtung — sonst reist der Platzhalter als Schlüssel weiter."""
    config = load_sources_config(
        _write(tmp_path, {"providers": {"openfigi": {"api_key": "${GIBT_ES_NICHT}"}}}), Settings()
    )

    assert config.config_for("openfigi")["api_key"] is None


def test_dieselbe_quelle_baut_je_rolle_einen_anderen_typ(tmp_path: Path) -> None:
    """yfinance beantwortet vier Fragen — mit zwei verschiedenen Klassen.

    Für `etf_meta` ist die Antwort ein `YFinanceMetadataPlugin`, für `quotes`
    ein `YFinancePlugin`. Ein Bauplan, der die Rolle nicht kennt, hätte der
    ETF-Kette ein Objekt ohne `fetch` gegeben — und der Fehler wäre erst beim
    ersten ETF-Abruf aufgefallen.
    """
    config = load_sources_config(
        _write(tmp_path, {"etf_meta": ["yfinance"], "quotes": ["yfinance"]}), Settings()
    )

    etf = build_chain("etf_meta", config, Settings())
    quotes = build_chain("quotes", config, Settings())

    assert type(unwrap(etf[0])).__name__ == "YFinanceMetadataPlugin"
    assert type(unwrap(quotes[0])).__name__ == "YFinancePlugin"


def test_eine_rolle_nimmt_keine_fremde_quelle_auf(tmp_path: Path) -> None:
    """`justetf` in der Kurskette ist ein Konfigurationsfehler, kein Absturz.

    Die Quelle wird übersprungen und protokolliert. Sie zu bauen hieße, ein
    Objekt in eine Kette zu setzen, dessen Vertrag dort nicht gilt.
    """
    config = load_sources_config(_write(tmp_path, {"quotes": ["justetf"]}), Settings())

    assert build_chain("quotes", config, Settings()) == []


def test_der_leseweg_zeigt_die_laufende_kette(tmp_path: Path, monkeypatch) -> None:
    """`#1`/`#2` über HTTP — und zwar **denselben Stand**, den die Dienste haben.

    Der Endpunkt liest bewusst `get_sources_config()`, nicht die Datei von
    jetzt. Läse er sie bei jedem Request neu, meldete er nach einer Änderung
    ohne Neustart eine Kette, die gar nicht läuft — und die Diagnose wäre
    ausgerechnet dann falsch, wenn man sie braucht.

    Der Test setzt deshalb die Einstellungen des **Prozesses** und leert den
    Cache; ein `dependency_overrides` griffe hier nicht, und das ist keine
    Testschwäche, sondern die Eigenschaft, um die es geht.

    **Nachgeschärft nach Runde 2 — die erste Fassung war wertlos.** Sie schrieb
    eine Datei, leerte den Cache und rief den Endpunkt auf. Damit prüfte sie
    nur, dass er *irgendwie* zur Datei passt: Läse er sie bei jedem Request
    frisch, wäre sie genauso grün gewesen. Der Gegenpfad braucht **zwei
    Stände in einem Prozess** — erst die Laufzeit bauen, dann die Datei ändern
    und verlangen, dass beide beim alten bleiben.
    """
    _write(tmp_path, {"resolvers": ["yahoo-search", "openfigi"]})
    monkeypatch.setattr(
        "app.container.get_settings",
        lambda: Settings(database_path=str(tmp_path / "stockinfo.db")),
    )
    get_sources_config.cache_clear()

    # Die Laufzeit entsteht — wie beim Start der App, aus Stand A.
    runtime = _build_resolver()
    assert [type(unwrap(inner)).__name__ for inner in runtime._resolvers] == [
        "YFinanceResolver",
        "OpenFigiResolverPlugin",
    ]

    # Jetzt ändert jemand die Datei, ohne neu zu starten. Die laufenden Dienste
    # bemerken das nicht — sie halten Stand A in der Hand.
    _write(tmp_path, {"resolvers": ["openfigi"]})

    body = TestClient(app).get("/sources").json()
    get_sources_config.cache_clear()

    resolvers = [row for row in body["sources"] if row["role"] == "resolvers"]
    assert [row["name"] for row in resolvers] == ["yahoo-search", "openfigi"], (
        "der Endpunkt meldet Stand B, während die Dienste auf A laufen"
    )
    assert all(row["configured"] for row in resolvers)
    assert body["config_path"].endswith("sources.yaml")

    # Und die Gegenrichtung derselben Aussage: Die gebaute Kette hat sich durch
    # die Dateiänderung nicht bewegt. Ohne diese Zeile bliebe offen, ob der
    # Endpunkt bei A geblieben ist, weil die Laufzeit es ist — oder ob beide
    # unabhängig voneinander irren.
    assert [type(unwrap(inner)).__name__ for inner in runtime._resolvers] == [
        "YFinanceResolver",
        "OpenFigiResolverPlugin",
    ]


def test_eine_quelle_in_falscher_rolle_gilt_nicht_als_einsatzbereit(
    tmp_path: Path, monkeypatch
) -> None:
    """**Befund 2 aus Runde 1**, zweiter Teil.

    `quotes: [justetf]` meldete `configured: true`, obwohl `build_chain` die
    Quelle wegen der falschen Rolle verwirft und **keine** Kursquelle baut. Der
    Leseweg sagte damit „einsatzbereit" über etwas, das gar nicht in der Kette
    steht — die Diagnose widersprach der Laufzeit.

    Beide entscheiden jetzt über `describe_chain`; `configured` ist die
    vollständige Bedingung `usable`, nicht nur `is_configured()`.
    """
    _write(tmp_path, {"quotes": ["justetf"]})
    monkeypatch.setattr(
        "app.container.get_settings",
        lambda: Settings(database_path=str(tmp_path / "stockinfo.db")),
    )
    get_sources_config.cache_clear()

    body = TestClient(app).get("/sources").json()
    get_sources_config.cache_clear()

    quotes = [row for row in body["sources"] if row["role"] == "quotes"]
    assert [row["name"] for row in quotes] == ["justetf"]
    assert quotes[0]["configured"] is False, (
        "eine Quelle in der falschen Rolle ist nicht einsatzbereit"
    )


def test_ein_bestehender_key_ueberlebt_ohne_datei(tmp_path: Path, monkeypatch) -> None:
    """**Befund 1 aus Runde 1.** Ohne `sources.yaml` ging der Key verloren.

    `Settings.openfigi_api_key` war gesetzt, die erste Fassung baute trotzdem
    `OpenFigiClient(None)` — ein Betreiber hätte sein Kontingent verloren, ohne
    etwas geändert zu haben. Gemessen war: `settings_key='expected-key'`, aber
    `resolver._client._api_key is None`.
    """
    monkeypatch.setattr(
        "app.container.get_settings",
        lambda: Settings(
            database_path=str(tmp_path / "stockinfo.db"),
            openfigi_api_key="expected-key",
        ),
    )
    get_sources_config.cache_clear()

    resolver = _build_resolver()
    get_sources_config.cache_clear()

    assert unwrap(resolver._resolvers[0]).api_key == "expected-key"


def test_die_datei_gewinnt_gegen_den_key_aus_den_einstellungen(
    tmp_path: Path, monkeypatch
) -> None:
    """Die Gegenrichtung — sonst wäre der Rückfall eine Übersteuerung.

    Wer einen Providerabschnitt schreibt, meint ihn. Ein Rückfall, der die
    Datei überstimmt, machte die Konfiguration wirkungslos.
    """
    _write(tmp_path, {"providers": {"openfigi": {"api_key": "aus-der-datei"}}})
    monkeypatch.setattr(
        "app.container.get_settings",
        lambda: Settings(
            database_path=str(tmp_path / "stockinfo.db"),
            openfigi_api_key="aus-den-einstellungen",
        ),
    )
    get_sources_config.cache_clear()

    resolver = _build_resolver()
    get_sources_config.cache_clear()

    assert unwrap(resolver._resolvers[0]).api_key == "aus-der-datei"


def test_ein_verweis_findet_den_wert_aus_den_einstellungen(tmp_path: Path) -> None:
    """`${NAME}` löst gegen dieselbe Quelle auf wie `Settings`.

    Nur gegen `os.environ` aufzulösen wäre eine **zweite** Auffassung davon,
    was „die Umgebung" ist: `pydantic-settings` liest zusätzlich die
    Projektkonfiguration, und der Verweis bliebe dann leer, obwohl derselbe
    Schlüssel für den Rest der App gesetzt ist.
    """
    config = load_sources_config(
        _write(tmp_path, {"providers": {"openfigi": {"api_key": "${OPENFIGI_API_KEY}"}}}),
        Settings(openfigi_api_key="aus-den-einstellungen"),
    )

    assert config.config_for("openfigi") == {"api_key": "aus-den-einstellungen"}


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

    assert [type(unwrap(inner)).__name__ for inner in resolver._resolvers] == [
        "YFinanceResolver",
        "OpenFigiResolverPlugin",
    ]
