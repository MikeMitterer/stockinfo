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

import yaml

from app.config import Settings
from app.container import _build_resolver, get_sources_config
from app.plugin_adapters import unwrap
from app.resolver import CompositeResolver
from app.sources_config import default_chains


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

    assert _names(resolver) == ["OpenFigiResolverPlugin", "YFinanceResolver"]


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

    assert _names(resolver) == ["OpenFigiResolverPlugin", "YFinanceResolver"]


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
