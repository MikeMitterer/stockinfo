"""Woher Quellen kommen, die niemand einkompiliert hat.

Die App soll weltweit funktionieren, lässt sich hier aber nur für wenige Märkte
prüfen — die Auflösung eines kanadischen Papiers hat allein drei Anläufe
gebraucht. Wer vor Ort sitzt, findet so etwas in Minuten. Also muss die Lösung
von außen kommen können, ohne dass jemand dieses Repository anfasst.

Zwei Wege, eine Registry:

* **Entry-Point** ``stockinfo.sources`` für Beigesteuertes — versioniert,
  installierbar, teilbar. Der Python-Standard; pytest und Airflow machen es so.
* **Verzeichnis** ``data/plugins/*.py`` zum Ausprobieren und für lokale
  Anpassungen. Ein Modul exportiert ``SOURCES = [MeineQuelle]``.

Geladen wird **beim Start**. Nachladen im Betrieb kostet Zustandsverwaltung für
einen Gewinn, den man selten spürt; Home Assistant hält es bei Custom
Components genauso.

**Ein Fehler in einem Plugin darf die App nicht am Starten hindern.** Das ist
die Regel, an der sich hier alles ausrichtet: Ein Modul, das beim Import wirft,
eine Klasse mit falscher `api_version`, ein doppelter Name — jeder dieser Fälle
wird **gemeldet und übersprungen**. Wer eine Quelle kaputt macht, verliert diese
Quelle, nicht seine Installation.
"""

from __future__ import annotations

import importlib.util
from collections.abc import Iterable
from dataclasses import dataclass
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

import structlog

from stockinfo_plugin.sources import (
    DailyCloseSource,
    FxSource,
    MetadataSource,
    QuoteSource,
    Resolver,
    Source,
)
from stockinfo_plugin.types import API_VERSION

from app.sources_registry import SourceSpec

logger = structlog.get_logger()

ENTRY_POINT_GROUP = "stockinfo.sources"
"""Die Entry-Point-Gruppe, unter der ein Paket seine Quellen anmeldet."""

PLUGIN_DIRNAME = "plugins"
"""Unterverzeichnis im Datenverzeichnis für einzelne Plugin-Dateien."""

MODULE_EXPORT = "SOURCES"
"""Der Name, unter dem eine Plugin-Datei ihre Klassen bereitstellt."""

# Rolle im Vertrag → Rolle in `sources.yaml`. Die App kennt fünf Ketten, das
# Plugin-Paket fünf Protokolle; die Namen unterscheiden sich, weil die App aus
# der Sicht des Betreibers benennt („etf_meta") und der Vertrag aus der Sicht
# des Autors („MetadataSource").
ROLE_FOR_PROTOCOL: tuple[tuple[type, str], ...] = (
    (Resolver, "resolvers"),
    (MetadataSource, "etf_meta"),
    (QuoteSource, "quotes"),
    (DailyCloseSource, "daily"),
    (FxSource, "fx"),
)


@dataclass(frozen=True)
class LoadProblem:
    """Was beim Laden schiefging — benannt, nicht verschwiegen.

    Attributes:
        origin: Woher der Versuch kam (Entry-Point-Name oder Dateipfad).
        reason: Ein Satz für einen Menschen, der das Plugin **nicht** gebaut hat.
    """

    origin: str
    reason: str


@dataclass(frozen=True)
class LoadResult:
    """Das Ergebnis eines Ladelaufs.

    `problems` ist ausdrücklich Teil des Ergebnisses und nicht nur eine
    Protokollzeile: Wer wissen will, warum seine Quelle fehlt, soll es an einer
    Stelle nachlesen können — und `GET /sources` kann sie später anzeigen.
    """

    specs: tuple[SourceSpec, ...] = ()
    problems: tuple[LoadProblem, ...] = ()


def roles_of(source_class: type) -> frozenset[str]:
    """Welche Ketten diese Klasse bedienen kann.

    Abgeleitet aus den Protokollen, die sie erbt — **nicht** aus einer
    Deklaration. Eine Quelle, die `QuoteSource` erbt, kann Kurse; das noch
    einmal hinzuschreiben wäre eine zweite Wahrheit, die beim ersten Umbau
    auseinanderläuft.
    """
    return frozenset(
        role
        for protocol, role in ROLE_FOR_PROTOCOL
        if issubclass(source_class, protocol)
    )


def spec_from_class(source_class: type) -> SourceSpec:
    """Macht aus einer Plugin-Klasse einen Bauplan für die Registry.

    Der Bauplan sieht danach aus wie jeder eingebaute: Name, Rollen, `cost`,
    eine Bauanweisung. Genau das ist der Punkt — eine geladene Quelle ist in der
    Registry nichts Besonderes.
    """

    def build(role: str, config: dict, settings: object) -> object:
        # Das Plugin bekommt **nur** seinen eigenen Abschnitt. Nicht die
        # Einstellungen, nicht die Datenbank, nicht andere Quellen. Das ist
        # eine Vertrags-, keine Sicherheitsgrenze — fremder Python-Code kann
        # ohnehin alles lesen —, aber es sagt, worauf er sich verlassen darf.
        return source_class(config)

    return SourceSpec(
        name=source_class.name,
        roles=roles_of(source_class),
        build=build,
        cost=getattr(source_class, "cost", "free"),
        loaded=True,
    )


def _check(source_class: Any, origin: str) -> LoadProblem | None:
    """Taugt das, was da geladen wurde, als Quelle?

    Vier Fragen, und jede hat schon einmal jemandem den Start gekostet: Ist es
    überhaupt eine `Source`? Trägt sie einen Namen? Passt die Vertragsversion?
    Bedient sie wenigstens eine Rolle?
    """
    if not isinstance(source_class, type) or not issubclass(source_class, Source):
        return LoadProblem(origin, f"{source_class!r} ist keine Source-Unterklasse")
    if not getattr(source_class, "name", ""):
        return LoadProblem(origin, f"{source_class.__name__} hat keinen name")
    # **Die eigene Deklaration, nicht die geerbte.** `api_version` hat auf
    # `Source` einen Vorgabewert, und `getattr` hätte ihn zurückgegeben — die
    # Prüfung hätte damit jedes Plugin durchgelassen, auch das gegen den alten
    # Vertrag gebaute. Ein Blick in `__dict__` der konkreten Klasse, keine
    # Suche entlang der MRO: Sonst deklarierte eine gemeinsame Basisklasse für
    # alle ihre Ableitungen mit, und die Vererbung wäre zurück.
    if "api_version" not in source_class.__dict__:
        return LoadProblem(
            origin,
            f"{source_class.name} deklariert keine api_version. Jede Quelle "
            f"nennt die Vertragsversion selbst, gegen die sie gebaut ist "
            f"(diese App spricht {API_VERSION})",
        )
    version = source_class.__dict__["api_version"]
    if version != API_VERSION:
        return LoadProblem(
            origin,
            f"{source_class.name}: api_version {version!r}, diese App spricht "
            f"{API_VERSION} — das Plugin wurde gegen einen anderen Vertrag gebaut",
        )
    if not roles_of(source_class):
        return LoadProblem(
            origin,
            f"{source_class.name} erbt keine der fünf Rollen "
            "(Resolver, MetadataSource, QuoteSource, DailyCloseSource, FxSource)",
        )
    return None


def _collect(candidates: Iterable[tuple[Any, str]]) -> LoadResult:
    """Prüft Kandidaten und sammelt Baupläne wie Beanstandungen."""
    specs: list[SourceSpec] = []
    problems: list[LoadProblem] = []
    for candidate, origin in candidates:
        problem = _check(candidate, origin)
        if problem is not None:
            problems.append(problem)
            continue
        specs.append(spec_from_class(candidate))
    return LoadResult(tuple(specs), tuple(problems))


def load_entry_point_sources() -> LoadResult:
    """Quellen aus installierten Paketen.

    Ein Paket meldet sie in seiner `pyproject.toml` an::

        [project.entry-points."stockinfo.sources"]
        canada = "meinplugin:CanadaFileResolver"

    Ein Entry-Point, dessen Import wirft, wird gemeldet und übersprungen — er
    darf den Start nicht verhindern und auch die übrigen Punkte nicht mitreißen.
    """
    candidates = []
    problems = []
    for point in entry_points(group=ENTRY_POINT_GROUP):
        try:
            candidates.append((point.load(), f"entry-point {point.name}"))
        except Exception as error:  # noqa: BLE001 — fremder Code, jeder Fehler zählt
            problems.append(
                LoadProblem(
                    f"entry-point {point.name}",
                    f"Import fehlgeschlagen: {type(error).__name__}: {error}",
                )
            )
    result = _collect(candidates)
    return LoadResult(result.specs, (*problems, *result.problems))


def load_directory_sources(directory: Path) -> LoadResult:
    """Quellen aus einzelnen Dateien in ``data/plugins/``.

    Jede ``*.py`` wird geladen und nach `SOURCES` gefragt — einer Liste von
    Klassen. Unterverzeichnisse und Dateien mit führendem ``_`` bleiben außen
    vor, damit Hilfsmodule und Editor-Reste nicht als Plugin gelten.

    Ein fehlendes Verzeichnis ist **kein** Fehler: Die meisten Installationen
    haben keine eigenen Plugins, und eine Warnung bei jedem Start wäre nach dem
    dritten Mal Rauschen.
    """
    if not directory.is_dir():
        return LoadResult()

    candidates = []
    problems = []
    for path in sorted(directory.glob("*.py")):
        if path.name.startswith("_"):
            continue
        origin = str(path)
        try:
            module = _import_file(path)
        except Exception as error:  # noqa: BLE001 — fremder Code, jeder Fehler zählt
            problems.append(
                LoadProblem(
                    origin, f"Import fehlgeschlagen: {type(error).__name__}: {error}"
                )
            )
            continue
        exported = getattr(module, MODULE_EXPORT, None)
        if exported is None:
            problems.append(
                LoadProblem(origin, f"kein {MODULE_EXPORT} — die Datei exportiert nichts")
            )
            continue
        if not isinstance(exported, (list, tuple)):
            problems.append(
                LoadProblem(origin, f"{MODULE_EXPORT} ist {type(exported).__name__}, "
                                    "erwartet wird eine Liste von Klassen")
            )
            continue
        candidates.extend((item, origin) for item in exported)

    result = _collect(candidates)
    return LoadResult(result.specs, (*problems, *result.problems))


def _import_file(path: Path) -> Any:
    """Lädt eine einzelne Datei als Modul.

    Der Modulname wird mit ``stockinfo_plugins.`` vorangestellt, damit eine
    Plugin-Datei namens ``json.py`` nicht das Standardmodul verdrängt — der
    Fehler wäre danach an einer ganz anderen Stelle aufgetaucht.
    """
    module_name = f"stockinfo_plugins.{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"{path} lässt sich nicht als Modul laden")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_all(data_dir: Path | str = "data") -> LoadResult:
    """Beide Ladewege, ein Ergebnis — und doppelte Namen fallen hier auf.

    Die Reihenfolge ist Absicht: Entry-Points zuerst, danach das Verzeichnis.
    Wer eine installierte Quelle lokal ersetzen will, legt eine Datei mit
    demselben Namen ab — **das wird gemeldet**, aber die Datei gewinnt. Sie ist
    die spezifischere Angabe: Wer sie hinlegt, hat es getan, um genau das zu
    erreichen.

    Args:
        data_dir: Das Datenverzeichnis; ``plugins/`` darin wird gelesen.

    Returns:
        Alle Baupläne und alle Beanstandungen.
    """
    from_points = load_entry_point_sources()
    from_files = load_directory_sources(Path(data_dir) / PLUGIN_DIRNAME)

    by_name: dict[str, SourceSpec] = {}
    problems = [*from_points.problems, *from_files.problems]
    for spec in (*from_points.specs, *from_files.specs):
        if spec.name in by_name:
            problems.append(
                LoadProblem(
                    spec.name,
                    f"{spec.name} wurde mehrfach geladen — die zuletzt gelesene "
                    "Fassung gilt (Dateien schlagen Entry-Points)",
                )
            )
        by_name[spec.name] = spec

    for problem in problems:
        logger.warning("plugin_load_problem", origin=problem.origin, reason=problem.reason)
    if by_name:
        logger.info("plugins_loaded", names=sorted(by_name))

    return LoadResult(tuple(by_name.values()), tuple(problems))
