"""Der Pflichtablauf für den Identitäts-Umzug — vorrechnen, bestätigen, berichten.

Drei Endpunkte für die drei Schritte, und sie sind die einzigen Fachwege, die
im Pending-Zustand offen bleiben. Warum es sie überhaupt gibt, steht in
`app/persistence/migration.py`: `init_db()` läuft im Lifespan, bevor die App den ersten
Request bedient — ein UI, das erst danach erreichbar wird, könnte niemanden
mehr warnen.

Router enthalten nur HTTP-Belange. Die Steuerung des Umzugs steht in
`app.services.migration`, der Riegel in `app.migration_guard`.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.migration_guard import REASON_STARTUP_FAILED, get_gate
from app.models import MigrationPreview, MigrationReport
from app.services import migration
from app.services.migration import MigrationNotPendingError, StartupFailedError

router = APIRouter(tags=["migration"])

SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/migration", response_model=MigrationPreview)
def migration_preview(settings: SettingsDep) -> MigrationPreview:
    """Rechnet vor, was der Umzug täte — **ohne** etwas zu ändern."""
    return migration.preview(settings.database_path)


@router.post("/migration/confirm", response_model=MigrationReport)
def migration_confirm(settings: SettingsDep) -> MigrationReport:
    """Führt den Umzug aus — auf ausdrückliche Bestätigung, **genau einmal**.

    Ein zweiter, gleichzeitiger Aufruf bekommt `409`; ebenso einer, der nichts
    mehr vorfindet. Ist der Umzug festgeschrieben, aber der Betrieb nicht
    angelaufen, antwortet der Weg mit `503` statt `200`: Eine erfolgreiche
    Bestätigung hieße, der Dienst sei bereit — und das ist er nicht.
    """
    try:
        return migration.confirm(settings.database_path, get_gate())
    except StartupFailedError as exc:
        raise HTTPException(status_code=503, detail=REASON_STARTUP_FAILED) from exc
    except MigrationNotPendingError as exc:
        raise HTTPException(
            status_code=409,
            detail="Es steht kein Umzug aus, oder Umzug beziehungsweise "
            "Betriebsstart laufen bereits.",
        ) from exc


@router.get("/migration/report", response_model=MigrationReport)
def migration_report(settings: SettingsDep) -> MigrationReport:
    """Was tatsächlich geschehen ist — auch lange danach noch."""
    return migration.stored_report(settings.database_path)
