"""Die Verdrahtung folgt der Konfiguration — und `strict_exchange` bleibt scharf.

**Was sich mit T-22 geändert hat.** Vorher entschied eine `if`-Kaskade in
`_build_resolver`, ob OpenFIGI allein oder mit Yahoo-Fallback läuft; der
Rückgabetyp war je nach Einstellung ein anderer (`OpenFigiResolver` gegen
`CompositeResolver`). Jetzt ist er **immer** ein `CompositeResolver` — auch mit
einer einzigen Quelle —, und wer in der Kette steht, sagt die Konfiguration.

Die beiden Tests dieser Datei sind deshalb umgeschrieben. Sie prüfen nicht mehr
den Typ, sondern **wer in der Kette steht** — das ist die Aussage, um die es
geht, und sie überlebt den nächsten Umbau der Verdrahtung.
"""

from pathlib import Path

import pytest
import yaml

from stockinfo_plugin import NotFound, QuoteSource

from app.config import Settings
from app.container import _build_resolver, get_sources_config
from app.plugin_adapters import unwrap
from app.resolver import CompositeResolver
from app.sources_config import default_chains
from app.sources_registry import SourceSpec, register_loaded


def _wire(monkeypatch, tmp_path: Path, strict: bool) -> CompositeResolver:
    """Baut den Resolver so, wie die App ihn beim Start baut."""
    monkeypatch.setattr(
        "app.container.get_settings",
        lambda: Settings(
            database_path=str(tmp_path / "stockinfo.db"), strict_exchange=strict
        ),
    )
    get_sources_config.cache_clear()
    resolver = _build_resolver()
    get_sources_config.cache_clear()
    return resolver


def _names(resolver: CompositeResolver) -> list[str]:
    """Die Klassennamen der Kette — **unter** Adapter und Kapsel.

    Seit T-23 trägt eine gebaute Quelle bis zu zwei Schichten. Ohne `unwrap`
    stünde hier `ResolverAdapter` und der Test sagte nichts mehr darüber, wen
    die Konfiguration ausgewählt hat — also über genau das, was er prüft.
    """
    return [type(unwrap(inner)).__name__ for inner in resolver._resolvers]


def test_strict_hat_keinen_yahoo_fallback(monkeypatch, tmp_path: Path) -> None:
    """`strict_exchange` darf seine Wirkung nicht still verlieren.

    Die Einstellung schaltet ab, was von der Vorgabebörse wegführt. Hätte T-22
    die Kette **allein** aus der Datei genommen, wäre der Yahoo-Fallback bei
    jedem bestehenden Betreiber mit `STRICT_EXCHANGE=true` wieder aktiv
    geworden — ohne dass er etwas geändert hätte, und mit genau der
    Überraschung in fremder Währung, die er ausgeschlossen hatte.

    Deshalb formt die Einstellung die **Vorgaben**. Eine vorhandene
    `sources.yaml` gewinnt weiterhin: Wer eine Kette hinschreibt, meint sie.
    """
    resolver = _wire(monkeypatch, tmp_path, strict=True)

    assert _names(resolver) == ["OpenFigiResolverPlugin"]


def test_nicht_strict_hat_den_fallback(monkeypatch, tmp_path: Path) -> None:
    """Die Gegenrichtung — ohne die Einstellung bleibt die Kaskade."""
    resolver = _wire(monkeypatch, tmp_path, strict=False)

    assert _names(resolver) == ["OpenFigiResolverPlugin", "YahooSearchResolverPlugin"]


def test_eine_datei_gewinnt_gegen_strict(monkeypatch, tmp_path: Path) -> None:
    """Die Grenze der Regel, ausgeschrieben.

    `strict_exchange` formt die Vorgaben, nicht die Datei. Ein Betreiber, der
    beides setzt, hat sich ausdrücklich entschieden — ihn zu überstimmen hieße,
    eine Konfigurationsdatei zu haben, die nicht gilt.
    """
    (tmp_path / "sources.yaml").write_text(
        yaml.safe_dump({"resolvers": ["openfigi", "yahoo-search"]}), encoding="utf-8"
    )

    resolver = _wire(monkeypatch, tmp_path, strict=True)

    assert _names(resolver) == ["OpenFigiResolverPlugin", "YahooSearchResolverPlugin"]


def test_die_vorgaben_unterscheiden_sich_nur_an_den_resolvern() -> None:
    """Die Einstellung betrifft die Auflösung, nicht Kurse oder Metadaten.

    Ohne diese Zeile könnte `default_chains` beim nächsten Umbau still auch die
    Kursquelle beschneiden — und ein Betreiber stünde ohne Kurse da, weil er
    eine Börse festgelegt hat.
    """
    strict = default_chains(True)
    loose = default_chains(False)

    assert strict["resolvers"] != loose["resolvers"]
    assert {role: chain for role, chain in strict.items() if role != "resolvers"} == {
        role: chain for role, chain in loose.items() if role != "resolvers"
    }


# ─── Die Kaskaden erreichen ihre Verbraucher ──────────────────────────────────


class _Placeholder(QuoteSource):
    """Eine Quelle, die nur da sein muss — gefragt wird sie hier nicht.

    Die Wurzel entscheidet, **wer** in einer Kette landet; ob eine Quelle
    antwortet, ist die Frage der Kaskadentests und der vertikalen Orakel.
    """

    api_version = 2
    SUPPORTED_KINDS = frozenset({"listed"})
    SUPPORTED_TYPES = frozenset({"stock"})

    def __init__(self, name: str) -> None:
        self.name = name

    def handles(self, request) -> bool:
        return True

    def fetch_quote(self, request):
        return NotFound()


def _wire_chains(monkeypatch, tmp_path: Path, chains: dict[str, list[str]]) -> None:
    """Schreibt eine `sources.yaml` und stellt die Einstellungen darauf ein.

    Die Datei liegt **neben der Datenbank**: Genau dort sucht `sources_path`
    sie. Ein `DATA_DIR` daneben zu setzen sähe richtig aus und ginge an der
    gelesenen Stelle vorbei — der Test läse dann die Vorgabekette und bewiese
    nichts.

    Die beiden zusätzlichen Namen kommen über `register_loaded`, den Weg, den
    auch ein echtes Plugin nimmt: Eingebaut gibt es für `quotes` nur eine
    einzige Quelle, und mit einer lässt sich eine Kette nicht messen.
    """
    (tmp_path / "sources.yaml").write_text(
        yaml.safe_dump({**chains, "providers": {}}), encoding="utf-8"
    )
    monkeypatch.setattr(
        "app.container.get_settings",
        lambda: Settings(database_path=str(tmp_path / "stockinfo.db")),
    )
    register_loaded(
        tuple(
            SourceSpec(name, frozenset({"quotes"}), _placeholder_factory(name))
            for name in ("first-source", "second-source")
        )
    )
    get_sources_config.cache_clear()


def _placeholder_factory(name: str):
    return lambda role, config, settings: _Placeholder(name)


def test_alle_konfigurierten_kursquellen_erreichen_den_dienst(
    monkeypatch, tmp_path: Path
) -> None:
    """**Die Zusage des Tickets, an der Wurzel gemessen.**

    Ein Test, der nur den Typ des Ergebnisses prüft, sagt über die Verdrahtung
    nichts — geprüft wird deshalb, **wer** in der Kette steht und in welcher
    Reihenfolge.
    """
    from app.container import _market_chain

    _wire_chains(
        monkeypatch,
        tmp_path,
        {
            "resolvers": ["openfigi"],
            "etf_meta": [],
            "quotes": ["first-source", "second-source"],
            "daily": ["yfinance"],
            "fx": ["yfinance"],
        },
    )
    try:
        chain = _market_chain("quotes")
    finally:
        get_sources_config.cache_clear()
        register_loaded(())

    assert [unwrap(source).name for source in chain] == [
        "first-source",
        "second-source",
    ], "die Wurzel gibt nicht die konfigurierte Kette weiter"


def test_eine_leere_kette_bleibt_ein_startfehler(monkeypatch, tmp_path: Path) -> None:
    """Ohne Quelle kann die App ihre Hauptaufgabe nicht erfüllen — und sagt das.

    Ein eingebauter Ersatz würde die Konfiguration hinter dem Rücken des
    Betreibers überstimmen.
    """
    from app.container import _market_chain

    _wire_chains(
        monkeypatch,
        tmp_path,
        {
            "resolvers": ["openfigi"],
            "etf_meta": [],
            "quotes": [],
            "daily": ["yfinance"],
            "fx": ["yfinance"],
        },
    )
    try:
        with pytest.raises(RuntimeError, match="quotes"):
            _market_chain("quotes")
    finally:
        get_sources_config.cache_clear()
        register_loaded(())
