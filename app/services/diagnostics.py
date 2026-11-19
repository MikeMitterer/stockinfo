"""Die Selbstauskunft der Instanz: Börsenkatalog und Quellenlage.

Beides beantwortet der Dienst aus seiner **laufenden** Konfiguration, ohne
Live-Abfrage. Der Router `routers/dashboard.py` übersetzt die Antworten nur
in HTTP; die Entscheidungen — welche Börse welche Quelle trägt, ob der Bestand
aus einer anderen Quellenlage stammt — fallen hier.
"""

from app.config import Settings
from app.exchange_catalog import catalog_annotations, prepare_catalog
from app.exchanges import EXCHANGES, preference_kind
from app.models import ExchangeEntry, ExchangesResponse, SourceEntry, SourcesResponse
from app.persistence.data_versions import declared_versions
from app.services.backup import fingerprint_of, stamped_fingerprint
from app.sources_config import ROLES, SourcesConfig
from app.sources_registry import describe_chain, specs_by_name


def exchange_overview(config: SourcesConfig, settings: Settings) -> ExchangesResponse:
    """Aktiver Börsenkatalog und deklarierte Unterstützung je Börse."""
    prepare_catalog(specs_by_name(), config)
    annotations, unspecified = catalog_annotations([
        entry for role in ROLES for entry in describe_chain(role, config)
    ])
    return ExchangesResponse(
        unspecified_support=unspecified,
        default_exchange=settings.default_exchange,
        default_exchange_kind=preference_kind(settings.default_exchange) or "unknown",
        catalog=[
            ExchangeEntry(
                mic=mic,
                alias=definition.alias,
                name=definition.name,
                region=definition.region,
                currency=definition.currency,
                **annotations[mic],
            )
            for mic, definition in EXCHANGES.items()
        ],
    )


def source_overview(config: SourcesConfig, settings: Settings) -> SourcesResponse:
    """Welche Quellen in welcher Reihenfolge greifen — und welche ausfallen.

    Gelistet wird **auch**, was nicht einsatzbereit ist. Eine Quelle
    stillschweigend wegzulassen hieße, dem Betreiber die Erklärung für ihr
    Fehlen vorzuenthalten — und die ist der eigentliche Zweck dieser Auskunft.
    """
    versions = declared_versions(config)
    entries = [
        SourceEntry(
            name=entry.name,
            data_version=versions.get(entry.name, 1),
            role=entry.role,
            position=entry.position,
            configured=entry.usable,
            reason=entry.reason,
            cost=entry.cost,
        )
        for role in ROLES
        for entry in describe_chain(role, config, settings)
    ]
    return SourcesResponse(
        config_path=str(config.path) if config.path else None,
        profile=config.profile,
        provenance_warning=provenance_warning(config, settings),
        sources=entries,
    )


def provenance_warning(config: SourcesConfig, settings: Settings) -> str:
    """Stammt der Bestand aus einer anderen Quellenlage als der laufenden?

    **Gemeldet, nicht geheilt.** Die Datenbank trägt die Kennung, unter der sie
    entstanden ist; nach einem erzwungenen Wiederherstellen weicht sie von der
    laufenden Konfiguration ab. Die Papiere darin können dann in einer Form
    vorliegen, die die laufende Kette nicht bedient — und das fiele sonst erst
    beim nächsten Kursabruf auf, papierweise.

    Die Auskunft kommt aus dem vorhandenen Stempel und der laufenden
    Konfiguration; ein eigener Vermerk daneben wäre eine zweite Wissensquelle,
    die beim ersten Nachtrag von der ersten abwiche.
    """
    stamped = stamped_fingerprint(settings.database_path)
    running = fingerprint_of(config)
    if not stamped or stamped == running:
        return ""
    return (
        f"Der Bestand stammt aus der Quellenlage {stamped}, die Instanz läuft "
        f"unter {running}."
    )
