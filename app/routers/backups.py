"""Sicherung anlegen und listen.

Der Router hält nur HTTP fest. Was eine Sicherung ist und wann sie zur
laufenden Quellenlage passt, entscheidet `app/services/backup.py`.

**Ein `DELETE` gibt es nicht.** Die elfte Sicherung verdrängt die älteste, und
ein zweiter Löschweg wäre nur eine zweite Gelegenheit, die falsche Datei zu
treffen.
"""

from fastapi import APIRouter, Depends, status

from app.container import get_backup_service
from app.models import BackupEntry, BackupList
from app.services.backup import BackupInfo, BackupService

router = APIRouter(tags=["backups"])


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
    return BackupList(
        fingerprint=service.fingerprint,
        backups=[_entry(info) for info in service.list()],
    )


@router.post("/backups", response_model=BackupEntry, status_code=status.HTTP_201_CREATED)
def create_backup(service: BackupService = Depends(get_backup_service)) -> BackupEntry:
    """Legt eine Sicherung an — auf Knopfdruck, nie nach Zeitplan.

    Die elfte verdrängt die älteste.
    """
    return _entry(service.create())
