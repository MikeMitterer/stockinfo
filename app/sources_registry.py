"""Welche Quellen es unter welchem Namen gibt — die eine Nachschlagestelle.

`sources.yaml` nennt Quellen beim **Namen**: `openfigi`, `yfinance`,
`justetf`. Irgendwo muss aus dem Namen ein Objekt werden, und das ist hier.

**Warum das nicht in `container.py` bleibt.** Dort stand bisher die
`if`-Kaskade: `strict_exchange` entschied über den Yahoo-Fallback, die
ETF-Rangfolge stand als Konstruktoraufruf da. Solange die Verdrahtung die
Auswahl trifft, ist jede Konfigurationsdatei Zierde — die Kaskade gewinnt.
Hier steht deshalb **nur**, wie eine Quelle heißt und wie man sie baut; **was**
gebaut wird, sagt die Konfiguration.

**Eingebaut heißt nicht bevorzugt.** yfinance und justETF stehen in derselben
Tabelle wie ein späteres Plugin und werden über denselben Weg gebaut. Eine
eingebaute Quelle, die an der Registry vorbei verdrahtet bleibt, wäre genau die
Sonderbehandlung, die T-23 danach wieder auseinandernehmen müsste.
"""

from collections.abc import Callable
from dataclasses import dataclass

import structlog

from app.providers.justetf_provider import JustEtfProvider
from app.providers.openfigi_provider import OpenFigiClient
from app.providers.yfinance_etf_provider import YFinanceEtfEnricher
from app.providers.yfinance_provider import YFinanceProvider
from app.resolver import OpenFigiResolver, YFinanceResolver

logger = structlog.get_logger()


@dataclass(frozen=True)
class SourceSpec:
    """Ein Bauplan: Name, Rollen, Kosten und wie die Quelle entsteht.

    `roles` ist eine Menge, weil eine Quelle mehrere beantworten darf —
    yfinance liefert Kurse, Tagesreihen, Wechselkurse **und** ETF-Metadaten.
    Genau diese Mehrfachrolle war der Grund, warum die fehlenden Protokolle
    `DailyCloseProvider` und `FxProvider` so lange unbemerkt blieben.
    """

    name: str
    roles: frozenset[str]
    build: Callable[[str, dict, str, bool], object]
    cost: str = "free"
    needs: tuple[str, ...] = ()
    """Pflichtige Schlüssel im eigenen Abschnitt.

    **Leer heißt nicht „braucht nichts", sondern „arbeitet auch ohne".**
    OpenFIGI etwa nimmt anonym Anfragen an und sendet den Schlüssel nur, wenn
    er da ist; die Quelle deshalb abzuschalten wäre falsch. `is_configured()`
    fragt „kann ich arbeiten", nicht „ist alles gesetzt".
    """


def _openfigi(role: str, config: dict, default_exchange: str, strict: bool) -> object:
    return OpenFigiResolver(
        OpenFigiClient(config.get("api_key")),
        default_exchange,
        home_fallback=not strict,
    )


def _yahoo_search(role: str, config: dict, default_exchange: str, strict: bool) -> object:
    return YFinanceResolver(default_exchange)


def _yfinance(role: str, config: dict, default_exchange: str, strict: bool) -> object:
    """Dieselbe Quelle, je Rolle ein anderer Typ.

    **Die Rolle gehört in den Bauplan, nicht nur in die Rollenmenge.** yfinance
    beantwortet vier Fragen, und für `etf_meta` ist die Antwort eine andere
    Klasse als für `quotes`. Ohne diesen Parameter hätte die ETF-Kette einen
    `YFinanceProvider` bekommen — ein Objekt, das `is_responsible` gar nicht
    kennt, und der Fehler wäre erst beim ersten ETF-Abruf sichtbar geworden.
    """
    return YFinanceEtfEnricher() if role == "etf_meta" else YFinanceProvider()


def _justetf(role: str, config: dict, default_exchange: str, strict: bool) -> object:
    return JustEtfProvider()


# Die eingebauten Quellen. Ein Plugin tritt ab T-23 über denselben Weg dazu —
# diese Tabelle ist dann nicht mehr die einzige Quelle von Namen, aber
# weiterhin ihre Form.
BUILTIN_SOURCES: tuple[SourceSpec, ...] = (
    SourceSpec("openfigi", frozenset({"resolvers"}), _openfigi),
    SourceSpec("yahoo-search", frozenset({"resolvers"}), _yahoo_search),
    SourceSpec("justetf", frozenset({"etf_meta"}), _justetf),
    SourceSpec(
        "yfinance",
        frozenset({"etf_meta", "quotes", "daily", "fx"}),
        _yfinance,
    ),
)


def specs_by_name() -> dict[str, SourceSpec]:
    """Alle bekannten Quellen, nach Namen."""
    return {spec.name: spec for spec in BUILTIN_SOURCES}


def is_configured(spec: SourceSpec, config: dict) -> bool:
    """Kann diese Quelle arbeiten?

    Der Ort für „API-Key vorhanden?", „Datei existiert?". Eine Quelle, die
    ``False`` meldet, wird gar nicht erst in die Kette aufgenommen — damit
    erübrigt sich jede Fallunterscheidung in der Verdrahtung.

    Ein fehlender Wert und ein leerer Wert gelten gleich: Ein
    `${FEHLT}`-Verweis wird zu ``None`` aufgelöst, ein leerer Umgebungseintrag
    zu ``""``. Beides heißt „nicht gesetzt", und beide als verschieden zu
    behandeln hieße, denselben Fehler zweimal erklären zu müssen.

    Args:
        spec: Der Bauplan der Quelle.
        config: Ihr eigener Abschnitt aus der Konfiguration.

    Returns:
        ``True``, wenn alle pflichtigen Schlüssel belegt sind.
    """
    return all(config.get(key) for key in spec.needs)


def build_chain(
    role: str,
    names: tuple[str, ...],
    config,
    default_exchange: str,
    strict: bool,
) -> list[object]:
    """Baut die Kette einer Rolle aus den konfigurierten Namen.

    Die Reihenfolge ist die der Konfiguration und wird **nicht** umsortiert:
    Sie ist die Rangfolge, und `cost` ist ausdrücklich Information statt
    Sortierregel. Bei Gleichstand — zwei Quellen ohne ausdrückliche Ordnung —
    entscheidet der Name, damit ein Fehlerbericht nachstellbar bleibt und das
    Ergebnis nicht an der Ladereihenfolge des Dateisystems hängt.

    Args:
        role: Die Rolle, für die gebaut wird.
        names: Die konfigurierten Namen in Rangfolge.
        config: Die gelesene `SourcesConfig`.
        default_exchange: Die eingestellte Vorzugsbörse.
        strict: Ob `strict_exchange` gilt.

    Returns:
        Die einsatzbereiten Quellen; nicht konfigurierte fehlen darin.

    Raises:
        UnknownSourceError: Ein Name steht in keiner Tabelle.
    """
    from app.sources_config import UnknownSourceError

    known = specs_by_name()
    built: list[object] = []
    for name in names:
        spec = known.get(name)
        if spec is None:
            raise UnknownSourceError(name, role, tuple(known))
        if role not in spec.roles:
            logger.warning("source_role_mismatch", source=name, role=role)
            continue
        section = config.config_for(name)
        if not is_configured(spec, section):
            logger.info("source_not_configured", source=name, role=role)
            continue
        built.append(spec.build(role, section, default_exchange, strict))
    return built
