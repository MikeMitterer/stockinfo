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

from app.plugin_adapters import (
    DailyAdapter,
    FxAdapter,
    MetadataAdapter,
    QuoteAdapter,
    ResolverAdapter,
)
from app.plugin_guard import GuardedSource
from app.plugins.justetf_metadata import JustEtfMetadataPlugin
from app.plugins.openfigi_resolver import OpenFigiResolverPlugin
from app.plugins.yfinance_metadata import YFinanceMetadataPlugin
from app.plugins.yfinance_quotes import YFinancePlugin
from app.resolver import YFinanceResolver

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
    build: Callable[[str, dict, object], object]
    cost: str = "free"
    loaded: bool = False
    """Kam diese Quelle von außen — Entry-Point oder Plugin-Verzeichnis?

    Die Unterscheidung dient **einem** Zweck: Fremder Code wird gekapselt
    (`GuardedSource`), eigener nicht. Das ist keine Bevorzugung der eingebauten
    Quellen — sie nehmen denselben Bauweg, stehen in derselben Tabelle und
    erscheinen gleichwertig in `/sources`. Es ist die Grenze aus dem Ticket:
    „die eine Stelle, an der **fremdem** Code misstraut wird".

    Die eingebauten Quellen zusätzlich zu kapseln wäre nicht sicherer, sondern
    unehrlich: Ihre Ausnahmen sind Fehler **dieser** App, und sie zu
    `Unavailable` zu machen hieße, den eigenen Fehler als Anbieterausfall
    auszugeben.
    """

    needs: tuple[str, ...] = ()
    """Pflichtige Schlüssel im eigenen Abschnitt.

    **Leer heißt nicht „braucht nichts", sondern „arbeitet auch ohne".**
    OpenFIGI etwa nimmt anonym Anfragen an und sendet den Schlüssel nur, wenn
    er da ist; die Quelle deshalb abzuschalten wäre falsch. `is_configured()`
    fragt „kann ich arbeiten", nicht „ist alles gesetzt".
    """


def _openfigi(role: str, config: dict, settings) -> object:
    """OpenFIGI — der Schlüssel kommt aus der Datei **oder** aus den Einstellungen.

    **Der Rückfall ist der Befund aus Runde 1.** Ohne `sources.yaml` gibt es
    keinen Providerabschnitt, und die erste Fassung baute deshalb
    `OpenFigiClient(None)` — obwohl `OPENFIGI_API_KEY` gesetzt war und vorher
    gewirkt hatte. Ein Betreiber hätte sein Kontingent verloren, ohne etwas
    geändert zu haben.

    Die Datei gewinnt, wenn sie etwas sagt: Wer einen Abschnitt schreibt, meint
    ihn. Sagt sie nichts, gilt weiter, was schon galt.
    """
    # **Seit T-23 das Plugin, nicht mehr der Kern-Resolver direkt.** Die App
    # ist damit ihr eigener erster Plugin-Autor: Wo der Vertrag zwickt, fällt
    # es uns auf und nicht zuerst einem Fremden. Die Fachlogik ist dieselbe —
    # `OpenFigiResolverPlugin` delegiert an `app.resolver.OpenFigiResolver`.
    return OpenFigiResolverPlugin(
        {"api_key": config.get("api_key") or settings.openfigi_api_key},
        home_fallback=not settings.strict_exchange,
    )


def _yahoo_search(role: str, config: dict, settings) -> object:
    return YFinanceResolver(settings.default_exchange)


def _yfinance(role: str, config: dict, settings) -> object:
    """Dieselbe Quelle, je Rolle ein anderer Typ.

    **Die Rolle gehört in den Bauplan, nicht nur in die Rollenmenge.** yfinance
    beantwortet vier Fragen, und für `etf_meta` ist die Antwort eine andere
    Klasse als für `quotes`. Ohne diesen Parameter hätte die ETF-Kette einen
    `YFinanceProvider` bekommen — ein Objekt, das `is_responsible` gar nicht
    kennt, und der Fehler wäre erst beim ersten ETF-Abruf sichtbar geworden.
    """
    # Seit T-23 spricht die Kursrolle den Vertrag; `etf_meta` folgt in einem
    # eigenen Schritt, weil dort die Antwort eine andere Form hat (`Reading`
    # statt eines Datensatzes) und der Core-Enricher noch anders fragt.
    if role == "etf_meta":
        return YFinanceMetadataPlugin(config)
    return YFinancePlugin(config)


def _justetf(role: str, config: dict, settings) -> object:
    return JustEtfMetadataPlugin(config)


# Die eingebauten Quellen. Ein Plugin tritt ab T-23 über denselben Weg dazu —
# diese Tabelle ist dann nicht mehr die einzige Quelle von Namen, aber
# weiterhin ihre Form.
BUILTIN_SOURCES: tuple[SourceSpec, ...] = (
    SourceSpec(
        "openfigi",
        frozenset({"resolvers"}),
        _openfigi,
    ),
    SourceSpec("yahoo-search", frozenset({"resolvers"}), _yahoo_search),
    SourceSpec(
        "justetf",
        frozenset({"etf_meta"}),
        _justetf,
    ),
    SourceSpec(
        "yfinance",
        frozenset({"etf_meta", "quotes", "daily", "fx"}),
        _yfinance,
    ),
)


# Was beim Start geladen wurde. **Ein Modulzustand, und zwar mit Absicht:**
# `describe_chain` läuft bei jeder `/sources`-Anfrage, und Plugins bei jedem
# Aufruf neu zu importieren wäre nicht nur langsam — es hieße, dass sich die
# Antwort der App ändert, während sie läuft. Geladen wird beim Start, einmal.
_LOADED: dict[str, SourceSpec] = {}

_LAST_REASON: dict[str, str] = {}
"""Der zuletzt gemeldete Grund je Quelle — damit `/sources` ihn nennen kann."""

_SNAPSHOT: dict[str, list['ChainEntry']] = {}
_BUILT: dict[str, list[object]] = {}




def register_loaded(specs: tuple[SourceSpec, ...]) -> None:
    """Übernimmt die beim Start geladenen Quellen in die Registry.

    Args:
        specs: Was `app.plugin_loader.load_all` gefunden hat.
    """
    _LOADED.clear()
    _LOADED.update({spec.name: spec for spec in specs})
    # **Die Momentaufnahme wird ungültig, sobald sich die Registry ändert.**
    # Sie zeigte sonst Ketten aus Quellen, die es nicht mehr gibt — und das
    # wäre wieder die zweite Wahrheit, gegen die es sie gibt.
    _SNAPSHOT.clear()
    _BUILT.clear()
    _LAST_REASON.clear()


def specs_by_name() -> dict[str, SourceSpec]:
    """Alle bekannten Quellen, nach Namen — eingebaute **und** geladene.

    Die eingebauten stehen zuerst und lassen sich von einem Plugin **nicht**
    verdrängen: Wer `yfinance` überschreiben könnte, könnte die Kurse der App
    still umleiten, und der Betreiber sähe in `/sources` weiterhin den
    vertrauten Namen. Ein Plugin, das so heißen will, bekommt stattdessen eine
    Meldung beim Laden.

    Dass eingebaute Quellen **denselben** Bauweg nehmen wie geladene, ist die
    eigentliche Zusage von T-23: Eine eingebaute Quelle, die an der Registry
    vorbei verdrahtet bliebe, wäre genau die Sonderbehandlung, die das Ticket
    auflösen soll.
    """
    known = {spec.name: spec for spec in BUILTIN_SOURCES}
    for name, spec in _LOADED.items():
        if name in known:
            logger.warning("plugin_name_is_builtin", source=name)
            continue
        known[name] = spec
    return known


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


@dataclass(frozen=True)
class ChainEntry:
    """Was aus einem konfigurierten Namen wird — die **eine** Entscheidung.

    `usable` ist genau die Bedingung, unter der `build_chain` die Quelle
    tatsächlich baut: bekannt **und** in dieser Rolle zulässig **und**
    einsatzbereit. Ein Leseweg, der nur `is_configured()` meldet, sagt
    `configured: true` für eine Quelle, die aus der Kette fällt, weil sie in
    der falschen Rolle steht — genau der Befund aus Runde 1.
    """

    name: str
    role: str
    position: int
    known: bool
    role_ok: bool
    configured: bool
    cost: str
    reason: str = ""
    """Warum diese Quelle **nicht** arbeitet — leer, wenn sie es tut.

    Ohne ihn nennt `/sources` nur ein `false`, und der Betreiber rät: fehlender
    Schlüssel? falsche Rolle? Konstruktor kaputt? Die Dokumentation versprach
    seit Runde 3 „einschließlich der Quellen, die nicht arbeiten können und
    **warum**" — der Grund kam nur nie an.
    """

    @property
    def usable(self) -> bool:
        return self.known and self.role_ok and self.configured


# Was zuletzt **wirklich gebaut** wurde, je Rolle. `/sources` liest hier und
# baut nicht neu.
#
# **Der Unterschied ist nicht theoretisch.** Eine Quelle, deren erste
# Konstruktion gelingt und deren zweite wirft, blieb in der laufenden Kette,
# während der Leseweg sie als unbrauchbar meldete — zwei Wahrheiten, und die
# Diagnose war die falsche. Dazu erzeugte jedes `GET /sources` neue Instanzen
# samt ihrer Seiteneffekte.
def close_all() -> None:
    """Schließt alle gebauten Quellen — beim Herunterfahren.

    `Source.close()` steht seit T-27a im Vertrag und wurde bis Runde 3 **nie
    gerufen**: eine öffentliche Zusage ohne Einlösung. Eine Quelle mit offener
    Datei oder Verbindung hätte sie bis zum Prozessende gehalten.

    Fehler beim Schließen werden gemeldet, nicht geworfen: Beim
    Herunterfahren ist ein Stacktrace das Letzte, was jemandem hilft.
    """
    for role, sources in _BUILT.items():
        for source in sources:
            close = getattr(source, "close", None)
            if not callable(close):
                continue
            try:
                close()
            except Exception as error:  # noqa: BLE001 — fremder Code
                logger.warning(
                    "source_close_failed",
                    role=role,
                    source=getattr(source, "name", type(source).__name__),
                    error=f"{type(error).__name__}: {error}",
                )
    _BUILT.clear()
    _SNAPSHOT.clear()


def describe_chain(role: str, config, settings=None) -> list[ChainEntry]:
    """Was mit jedem konfigurierten Namen dieser Rolle geschieht.

    **Die gemeinsame Quelle für Laufzeit und Diagnose.** `build_chain` baut
    daraus die Objekte, `/sources` zeigt sie an — beide sehen dieselben
    Entscheidungen. Zwei getrennte Auswertungen hätten sich beim ersten
    Sonderfall unterschieden, und ausgerechnet die Diagnose hätte dann das
    Falsche gemeldet.

    Args:
        role: Die Rolle.
        config: Die gelesene `SourcesConfig`.

    Returns:
        Je konfiguriertem Namen ein Eintrag, in Rangfolge.
    """
    if role in _SNAPSHOT:
        # Die laufende Kette. Neu zu bauen hieße, einen **anderen** Zustand zu
        # zeigen als den, der gerade arbeitet — und bei jedem GET Instanzen zu
        # erzeugen, die sofort weggeworfen werden.
        return _SNAPSHOT[role]
    return [entry for entry, _ in _evaluate(role, config, settings)]


def _evaluate(role: str, config, settings=None) -> list[tuple[ChainEntry, object | None]]:
    """Was mit jedem Namen geschieht — **einmal** ausgewertet, zweifach gelesen.

    `build_chain` nimmt die Objekte, `describe_chain` die Beschreibungen. Das
    war schon vorher die Zusage; sie stimmte nur nicht mehr: Seit die
    Konstruktion und `configuration_problem()` am Bau-Rand geprüft werden,
    konnte eine Quelle dort **verworfen** werden, während `/sources` sie
    weiterhin als `configured: true` und `usable: true` meldete.

    Zwei Auswertungen unterscheiden sich beim ersten Sonderfall, und
    ausgerechnet die Diagnose meldet dann das Falsche — genau der Befund aus
    T-22 Runde 1, hier eine Ebene später noch einmal.

    Args:
        role: Die Rolle.
        config: Die gelesene `SourcesConfig`.
        settings: Die Einstellungen. **Ohne sie wird nicht gebaut** — dann
            beschreibt der Eintrag nur, was sich ohne Konstruktion sagen lässt.
            Der Leseweg reicht sie herein; ein Aufrufer, der es nicht tut,
            bekommt die schwächere, aber ehrliche Auskunft.
    """
    known = specs_by_name()
    result: list[tuple[ChainEntry, object | None]] = []

    for position, name in enumerate(config.chain(role), start=1):
        spec = known.get(name)
        role_ok = spec is not None and role in spec.roles
        configured = spec is not None and is_configured(spec, config.config_for(name))
        reason = ""
        if spec is None:
            reason = "unbekannter Name"
        elif not role_ok:
            reason = f"kennt die Rolle '{role}' nicht"
        elif not configured:
            reason = "Pflichtangaben fehlen"

        source = None
        if spec is not None and role_ok and configured and settings is not None:
            source = _build_one(spec, role, config.config_for(name), settings)
            if source is None:
                # Konstruktion gescheitert oder Selbstauskunft negativ. Beides
                # heißt für den Betreiber dasselbe: Diese Quelle arbeitet
                # nicht — und `/sources` sagt es jetzt auch, samt Grund.
                configured = False
                reason = _LAST_REASON.get(spec.name, "nicht einsatzbereit")

        result.append(
            (
                ChainEntry(
                    name=name,
                    role=role,
                    position=position,
                    known=spec is not None,
                    role_ok=role_ok,
                    configured=configured,
                    cost=spec.cost if spec else "unknown",
                    reason=reason,
                ),
                source,
            )
        )
    return result


def build_chain(role: str, config, settings) -> list[object]:
    """Baut die Kette einer Rolle aus den konfigurierten Namen.

    Die Reihenfolge ist die der Konfiguration und wird **nicht** umsortiert:
    Sie ist die Rangfolge, und `cost` ist ausdrücklich Information statt
    Sortierregel.

    Args:
        role: Die Rolle, für die gebaut wird.
        config: Die gelesene `SourcesConfig`.
        settings: Die Einstellungen — die Quellen holen sich daraus, was sie
            brauchen.

    Returns:
        Die einsatzbereiten Quellen; nicht konfigurierte fehlen darin.

    Raises:
        UnknownSourceError: Ein Name steht in keiner Tabelle.
    """
    from app.sources_config import UnknownSourceError

    known = specs_by_name()
    bewertet = _evaluate(role, config, settings)

    # **Die Momentaufnahme steht, bevor irgendetwas werfen kann.** Ein
    # unbekannter Name in der Kette bricht den Bau ab — und ohne diese Zeile
    # zeigte `/sources` danach die **vorige** Kette, also gerade nicht den
    # Zustand, der den Betreiber interessiert. Der Fall, für den er die
    # Auskunft aufruft, wäre der einzige, in dem sie ihn anlügt.
    _SNAPSHOT[role] = [entry for entry, _ in bewertet]

    built: list[object] = []
    for entry, source in bewertet:
        if not entry.known:
            raise UnknownSourceError(entry.name, role, tuple(known))
        if not entry.role_ok:
            logger.warning("source_role_mismatch", source=entry.name, role=role)
            continue
        if source is None:
            logger.info("source_not_usable", source=entry.name, role=role)
            continue
        built.append(source)

    _BUILT[role] = built
    return built


# Welche Rolle über welchen Adapter in die Sprache des Core kommt. Rollen ohne
# Eintrag sprechen sie noch direkt — der Übergang ist absichtlich sichtbar.
ROLE_ADAPTERS = {
    "resolvers": ResolverAdapter,
    "quotes": QuoteAdapter,
    "daily": DailyAdapter,
    "fx": FxAdapter,
    "etf_meta": MetadataAdapter,
}
"""Alle fünf Rollen — **vollständig, und das war der Befund aus Runde 2.**

Zwei zu haben und `contract=True` trotzdem zu setzen hieß: Der Core bekam für
`daily` und `fx` das nackte Plugin und rief darauf Methoden, die es nicht hat.
Eine Tabelle mit Lücken ist gefährlicher als gar keine — sie sieht vollständig
aus.
"""


def _build_one(spec: SourceSpec, role: str, config: dict, settings) -> object | None:
    """Baut **eine** Quelle — gekapselt, adaptiert, und mit Diagnose geprüft.

    Die Reihenfolge ist der Punkt:

    1. **Bauen, und zwar geschützt.** Ein Konstruktor, der wirft, darf nicht
       den Start umwerfen. In Runde 1 stand die Kapsel erst *danach* — ein
       Plugin mit fehlerhaftem ``__init__`` riss deshalb die ganze Kette mit,
       obwohl `GuardedSource` genau dafür gebaut war.
    2. **Diagnose fragen.** Eine Quelle, die selbst sagt, dass sie nicht
       arbeiten kann, gehört nicht in die Kette. `SourceSpec.needs` ist bei
       geladenen Quellen leer, also hätte `is_configured` sie durchgelassen;
       `configuration_problem()` ist die Auskunft, die der Vertrag dafür
       vorsieht.
    3. **Kapseln**, wenn sie fremd ist.
    4. **Adaptieren**, wenn sie den Vertrag spricht und die Rolle einen Adapter
       hat.

    Returns:
        Die einsatzbereite Quelle, oder ``None`` — dann steht der Grund im
        Protokoll und die Kette geht ohne sie weiter.
    """
    try:
        source = spec.build(role, config, settings)
    except Exception as error:  # noqa: BLE001 — fremder Code, jeder Fehler zählt
        _LAST_REASON[spec.name] = f"Konstruktor: {type(error).__name__}: {error}"
        logger.warning(
            "source_construction_failed",
            source=spec.name,
            role=role,
            error=f"{type(error).__name__}: {error}",
        )
        return None

    problem = _diagnosis(spec, source)
    if problem:
        _LAST_REASON[spec.name] = problem
        logger.warning("source_not_operational", source=spec.name, reason=problem)
        return None

    _LAST_REASON.pop(spec.name, None)

    if spec.loaded:
        source = GuardedSource(source)
    # **Jede** Quelle spricht den Vertrag; jede Rolle hat ihren Adapter. Bis
    # Runde 3 stand hier ein Übergangsfeld `contract_roles` — es beschrieb, wer
    # schon umgestellt war. Ein Übergang, der bleibt, ist keiner mehr: Er wird
    # zur zweiten Wahrheit, die beim nächsten Umbau niemand mitpflegt.
    adapter = ROLE_ADAPTERS[role]
    return adapter(source, settings.default_exchange)


def _diagnosis(spec: SourceSpec, source: object) -> str:
    """Was die Quelle selbst über ihre Arbeitsfähigkeit sagt.

    Auch das Fragen ist gekapselt: Eine Diagnose, die wirft, ist selbst ein
    Grund, die Quelle nicht zu nehmen — aber kein Grund, die App zu beenden.
    """
    ask = getattr(source, "configuration_problem", None)
    if not callable(ask):
        return ""
    try:
        return str(ask() or "")
    except Exception as error:  # noqa: BLE001 — fremder Code, jeder Fehler zählt
        return f"configuration_problem() wirft: {type(error).__name__}: {error}"
