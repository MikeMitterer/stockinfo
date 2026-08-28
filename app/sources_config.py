"""Welche Quelle wann greift — aus einer Datei statt aus der Verdrahtung.

Bis T-22 stand die Kette als `if`-Kaskade in `app/container.py`: Ob OpenFIGI
allein oder mit Yahoo-Fallback läuft, entschied `strict_exchange`; welche
ETF-Quelle vorn steht, stand als Konstruktoraufruf da. Mit zwei Quellen ist das
tragbar, mit vier nicht — und ein Plugin lässt sich so gar nicht eintragen.

**Zwei Orte, getrennt nach Lebenszyklus statt nach Technik.** Geheimnisse und
Schalter bleiben in der Umgebungskonfiguration: Keys, Ports, TTLs. Ketten und
Reihenfolge kommen in eine Datei im Daten-Volume, neben die Datenbank.

Der Grund ist praktisch: **Diese Datei kann ein Nutzer in ein Issue kopieren,
ohne einen Schlüssel zu leaken.** Wenn jemand in Kanada eine funktionierende
Kette gefunden hat, ist sie genau das Artefakt, das er weitergibt. Deshalb steht
dort `${OPENFIGI_API_KEY}` und nie der Schlüssel selbst.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import structlog
import yaml

logger = structlog.get_logger()

# `${NAME}` verweist auf eine Umgebungsvariable. Bewusst nur diese eine Form —
# eine Vorlagensprache in einer Konfigurationsdatei ist der Anfang einer
# zweiten Programmiersprache, die niemand dokumentiert.
_ENV_REFERENCE = re.compile(r"^\$\{([A-Z_][A-Z0-9_]*)\}$")

# Die Rollen, die eine Kette besetzen kann. Eine Rolle ist eine Frage an die
# Außenwelt — nicht eine Klasse: `quotes` beantwortet „was kostet das Papier
# gerade", unabhängig davon, wer sie beantwortet.
ROLES = ("resolvers", "etf_meta", "quotes", "daily", "fx")

# Was gilt, wenn keine Datei da ist. **Nicht abbrechen**: Eine frische
# Installation ohne `sources.yaml` ist der Normalfall, nicht der Fehlerfall,
# und die Vorgaben sind genau das, was die Kaskade vorher fest verdrahtet hatte.
DEFAULT_CHAINS: dict[str, tuple[str, ...]] = {
    "resolvers": ("openfigi", "yahoo-search"),
    "etf_meta": ("justetf", "yfinance"),
    "quotes": ("yfinance",),
    "daily": ("yfinance",),
    "fx": ("yfinance",),
}


@dataclass(frozen=True)
class SourcesConfig:
    """Die gelesene Quellen-Konfiguration.

    `chains` hält je Rolle die Namen in **Reihenfolge der Datei** — sie ist die
    Rangfolge und nicht sortierbar. `providers` hält je Quelle ihren eigenen
    Abschnitt, mit aufgelösten Umgebungsverweisen.

    `profile` ist der einfache Weg: ein Paketname statt vier von Hand
    geschriebener Ketten. Gelesen wird er hier, **geladen** wird er erst mit
    T-23 — der Lader für Pakete gehört zur Registry, nicht zur Konfiguration.
    """

    chains: dict[str, tuple[str, ...]] = field(default_factory=dict)
    providers: dict[str, dict] = field(default_factory=dict)
    environment: dict[str, str] = field(default_factory=dict)
    profile: str | None = None
    packages: tuple[str, ...] = ()
    """Beigesteuerte Pakete mit **fester Version**.

    Sie werden beim Start nach `data/plugin-env/<hash>` installiert und in den
    Suchpfad gehängt; danach findet die Registry ihre Entry-Points. Der Grund
    für das eigene Verzeichnis: Beim offiziellen Container liegt
    `site-packages` im Image und überlebt kein Update — `/data` schon.

    **Feste Versionen sind keine Förmlichkeit.** Der Ordnername ist eine
    Prüfsumme über diese Liste; ohne Version wäre derselbe Hash morgen ein
    anderes Paket, und niemand sähe es.
    """

    path: Path | None = None

    def chain(self, role: str) -> tuple[str, ...]:
        """Die Namen einer Rolle, in Rangfolge.

        Args:
            role: Eine der Rollen aus `ROLES`.

        Returns:
            Die konfigurierten Namen, oder die Vorgabe für diese Rolle.
        """
        return self.chains.get(role, DEFAULT_CHAINS.get(role, ()))

    def config_for(self, name: str) -> dict:
        """Der eigene Abschnitt einer Quelle — nie die ganze Konfiguration.

        Das ist die Vertragsgrenze aus `stockinfo_plugin.sources.Source`: Eine
        Quelle bekommt ihren Abschnitt, nicht die Einstellungen der App und
        nicht die Abschnitte der anderen.
        """
        return self.providers.get(name, {})


def environment_from(settings) -> dict[str, str]:
    """Woher ein `${NAME}`-Verweis seinen Wert nimmt.

    **Aus `Settings`, nicht aus `os.environ` allein.** Das ist der Kern des
    Befunds aus Runde 1: `Settings` ist die kanonische Umgebungskonfiguration
    der App — `pydantic-settings` liest dafür Umgebung **und** Projektdatei mit
    einer festgelegten Rangfolge. Löst die Quellen-Konfiguration nur gegen
    `os.environ` auf, gibt es zwei Auffassungen davon, was „die Umgebung" ist,
    und `${OPENFIGI_API_KEY}` bleibt leer, obwohl derselbe Schlüssel für den
    Rest der App gesetzt ist.

    Die Abbildung ist die von pydantic: Ein Feld `openfigi_api_key` entspricht
    dem Verweis `${OPENFIGI_API_KEY}`. Nachgelesen wird also **die
    Konfiguration**, nicht die Datei — diese Funktion öffnet nichts.

    Args:
        settings: Die geladenen Einstellungen.

    Returns:
        Die auflösbaren Namen mit ihren Werten.
    """
    values = {
        name.upper(): value
        for name, value in settings.model_dump().items()
        if isinstance(value, str) and value
    }
    # Ein echter Umgebungseintrag gewinnt — dieselbe Rangfolge, die pydantic
    # innerhalb von `Settings` anwendet. Namen ohne Feld (ein Plugin bringt
    # eigene mit) sind damit weiterhin auflösbar.
    return {**values, **os.environ}


def _resolve(value: object, env: dict[str, str]) -> object:
    """Ersetzt `${NAME}` durch den Umgebungswert — rekursiv.

    Fehlt die Variable, steht dort `None` und **nicht** der Verweis als Text.
    Sonst bekäme eine Quelle die Zeichenkette `"${OPENFIGI_API_KEY}"` als
    Schlüssel und schickte sie an die API — der Fehler käme dann von außen
    zurück, wo ihn niemand mehr zuordnet.
    """
    if isinstance(value, str):
        match = _ENV_REFERENCE.fullmatch(value.strip())
        return env.get(match.group(1)) if match else value
    if isinstance(value, dict):
        return {key: _resolve(inner, env) for key, inner in value.items()}
    if isinstance(value, list):
        return [_resolve(inner, env) for inner in value]
    return value


def default_chains(strict_exchange: bool) -> dict[str, tuple[str, ...]]:
    """Die Vorgaben — abhängig von `strict_exchange`.

    **Diese Einstellung darf nicht still ihre Wirkung verlieren.** Vor T-22
    schaltete sie zwei Dinge ab, die von der Vorgabebörse wegführen: die
    Heimatbörsen-Kaskade **und** den Yahoo-Fallback. Wer sie wählt, will diese
    Börse oder gar nichts — sonst kommt das Papier in fremder Währung herein,
    und genau das hatte er ausgeschlossen.

    Die Kette allein aus der Datei zu nehmen hätte den Fallback bei jedem
    bestehenden Betreiber mit `STRICT_EXCHANGE=true` wieder eingeschaltet, ohne
    dass er etwas geändert hätte. Deshalb formt die Einstellung die
    **Vorgaben**; eine vorhandene `sources.yaml` gewinnt weiterhin gegen sie —
    wer eine Kette hinschreibt, meint sie.

    Args:
        strict_exchange: Ob nur die Vorgabebörse gelten soll.

    Returns:
        Die Vorgabeketten je Rolle.
    """
    if not strict_exchange:
        return dict(DEFAULT_CHAINS)
    return {**DEFAULT_CHAINS, "resolvers": ("openfigi",)}


_PIN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(\[[A-Za-z0-9,._-]+\])?==[A-Za-z0-9][A-Za-z0-9.\-+!]*$")
"""Eine gewöhnliche Anforderung mit **fester** Version.

Kein `>=`, kein nackter Name, keine Git-URL, keine pip-Option. Der Ordnername
der Umgebung ist eine Prüfsumme über diese Liste — ohne feste Version wäre
derselbe Hash morgen ein anderes Paket, und niemand sähe es. Eine URL oder ein
`--index-url` hier wäre zudem ein Weg, dem Installer Anweisungen unterzuschieben.
"""


def _packages_from(raw: dict) -> tuple[str, ...]:
    """Die Paketliste aus `plugins.packages` — und nur von dort.

    **Ein Parserpfad, der dokumentierte.** Runde 4 las ein undokumentiertes
    Top-Level-Feld `packages`; wer das Design befolgte, bekam eine leere Liste
    und keinen Hinweis.

    Was nicht der Form `name==version` entspricht, wird **abgewiesen und
    benannt** — nicht stillschweigend an pip weitergereicht.
    """
    section = raw.get("plugins") or {}
    if not isinstance(section, dict):
        logger.warning("plugins_section_invalid", got=type(section).__name__)
        return ()

    entries = section.get("packages") or ()
    if isinstance(entries, str) or not isinstance(entries, (list, tuple)):
        logger.warning("plugins_packages_invalid", got=type(entries).__name__)
        return ()

    taugliche = []
    for entry in entries:
        text = str(entry).strip()
        if _PIN.fullmatch(text):
            taugliche.append(text)
        else:
            logger.warning("plugin_package_rejected", entry=text)
    return tuple(taugliche)


def load_sources_config(path: str | Path, settings) -> SourcesConfig:
    """Liest `sources.yaml` — oder liefert die Vorgaben.

    Args:
        path: Pfad der Datei, üblicherweise neben der Datenbank.
        settings: Die geladenen Einstellungen — sie formen die Vorgaben über
            `strict_exchange` und lösen die `${NAME}`-Verweise auf.

    Returns:
        Die gelesene Konfiguration; bei fehlender Datei eine mit den Vorgaben.

    Raises:
        yaml.YAMLError: Die Datei ist kein gültiges YAML. Das ist bewusst **kein**
            stiller Rückfall auf die Vorgaben: Wer eine Datei hinlegt, will,
            dass sie gilt — sie zu ignorieren wäre die schlimmere Überraschung.
    """
    defaults = default_chains(settings.strict_exchange)
    env = environment_from(settings)
    source = Path(path)
    if not source.is_file():
        logger.info(
            "sources_config_default",
            path=str(source),
            strict=settings.strict_exchange,
        )
        return SourcesConfig(chains=defaults, environment=env, path=None)

    raw = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    chains = {
        role: tuple(raw[role]) for role in ROLES if isinstance(raw.get(role), list)
    }
    providers = {
        name: _resolve(section, env) if isinstance(section, dict) else {}
        for name, section in (raw.get("providers") or {}).items()
    }
    logger.info(
        "sources_config_loaded",
        path=str(source),
        roles=sorted(chains),
        providers=sorted(providers),
        profile=raw.get("profile"),
    )
    return SourcesConfig(
        chains={**defaults, **chains},
        providers=providers,
        environment=env,
        profile=raw.get("profile"),
        packages=_packages_from(raw),
        path=source,
    )
