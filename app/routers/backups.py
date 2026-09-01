"""Sicherung anlegen und listen.

Der Router hält nur HTTP fest. Was eine Sicherung ist und wann sie zur
laufenden Quellenlage passt, entscheidet `app/services/backup.py`.

**Ein `DELETE` gibt es nicht.** Die elfte Sicherung verdrängt die älteste, und
ein zweiter Löschweg wäre nur eine zweite Gelegenheit, die falsche Datei zu
treffen.
"""

from fastapi import APIRouter, Depends, Query, status

from app.container import get_backup_service
from app.models import BackupEntry, BackupList, ErrorDetail, RestoreAccepted
from app.services.backup import BackupInfo, BackupService, restore_state

router = APIRouter(tags=["backups"])

RESTORE_ERRORS: dict[int | str, dict[str, object]] = {
    404: {"model": ErrorDetail, "description": "`backup_not_found`"},
    409: {
        "model": ErrorDetail,
        "description": (
            "`backup_incompatible` — andere Quellenlage; `params.difference` "
            "nennt die abweichenden Rollen mit beiden Ketten. `force=true` "
            "übergeht es"
        ),
    },
    422: {
        "model": ErrorDetail,
        "description": (
            "`backup_schema_too_new` — **auch `force` hebt das nicht auf**: "
            "Eine ältere App kann eine neuere Datenbank nicht lesen"
        ),
    },
}
"""Die drei Ausgänge — deklariert, nicht nur gelebt."""


def _entry(info: BackupInfo) -> BackupEntry:
    return BackupEntry(
        name=info.name,
        created_at=info.created_at,
        size=info.size,
        fingerprint=info.fingerprint,
        compatible=info.compatible,
        reason=info.reason,
    )


@router.get("/backups", response_model=BackupList)
def list_backups(service: BackupService = Depends(get_backup_service)) -> BackupList:
    """Welche Sicherungen es gibt — und ob sie zur laufenden Lage passen.

    Gelistet wird **auch**, was nicht passt: Eine unpassende auszublenden
    hieße, jemanden nach einer Datei suchen zu lassen, die er im Verzeichnis
    liegen sieht.
    """
    pending, error = restore_state(str(service.database_path))
    return BackupList(
        fingerprint=service.fingerprint,
        pending_restore=pending,
        restore_error=error,
        backups=[_entry(info) for info in service.list()],
    )


@router.post("/backups", response_model=BackupEntry, status_code=status.HTTP_201_CREATED)
def create_backup(service: BackupService = Depends(get_backup_service)) -> BackupEntry:
    """Legt eine Sicherung an — auf Knopfdruck, nie nach Zeitplan.

    Die elfte verdrängt die älteste.
    """
    return _entry(service.create())


@router.post(
    "/backups/{name}/restore",
    response_model=RestoreAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    responses=RESTORE_ERRORS,
)
def restore_backup(
    name: str,
    force: bool = Query(
        default=False,
        description="Abweichende Quellenkennung übergehen; ein neueres Schema nicht",
    ),
    service: BackupService = Depends(get_backup_service),
) -> RestoreAccepted:
    """Merkt eine Sicherung zum Einspielen vor — **`202`, nicht `200`**.

    An der laufenden Datenbank ändert sich nichts; getauscht wird beim nächsten
    Start. Bis dahin steht der ausstehende Neustart in `GET /backups`, damit die
    Ansage nicht nur einmal in einer HTTP-Antwort stand.
    """
    info = service.request_restore(name, force=force)
    return RestoreAccepted(
        backup=_entry(info),
        # „Neustart" steht hier ausdrücklich — „beim nächsten Start" liest sich
        # wie etwas, das von selbst passiert.
        detail=(
            f"{info.name} ist zum Einspielen vorgemerkt. Die Wiederherstellung "
            "verlangt einen Neustart der App; bis dahin läuft der bisherige "
            "Bestand unverändert weiter."
        ),
    )
