"""Sicherung der Datenbank — anlegen, beschreiben, listen.

Die Kompatibilität folgt den vom Plugin-Autor deklarierten Datenversionen.
Paketpins und Rollenketten bleiben Herkunftsinformation, keine Sperre.

**`VACUUM INTO` statt einer Dateikopie:** Im WAL-Modus liegen die jüngsten
Schreibvorgänge in der `-wal`-Datei; eine Kopie der `.db` allein ergibt einen
Stand, den es nie gab. `VACUUM INTO` erzeugt eine in sich stimmige Datei und
trägt `PRAGMA user_version` mit.
"""

import hashlib
import json
import os
import re
import shutil
import sqlite3
import tempfile
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import structlog

from app.db import SCHEMA_VERSION, get_connection
from app.data_versions import declared_versions, stored_versions, stamp_versions
from app.models import BackupReason, SourceDifference
from app.sources_config import ROLES, SourcesConfig

logger = structlog.get_logger()

BACKUP_DIRNAME = "backups"
KEEP_BACKUPS = 10
"""Wie viele Sicherungen liegen bleiben."""

FINGERPRINT_KEY = "sources_fingerprint"

PENDING_FILENAME = "restore-pending.json"
"""Die vorgemerkte Absicht. Liegt **neben** der Datenbank, nicht darin — sie
soll den Tausch überleben, der die Datenbank ersetzt."""

_NAME_PATTERN = re.compile(r"^stockinfo-\d{8}T\d{9}Z-[0-9a-f]{12}\.db$")
"""**Ein Name, kein Pfad.** Schrägstriche, `..` und absolute Pfade sind ein
Versuch, das Verzeichnis zu verlassen; geprüft wird vor jedem Dateizugriff."""


class BackupError(Exception):
    """Eine Ablehnung des Wiederherstellens.

    `params` und `reason` stehen **getrennt**: Ein unbekannter Name hat keine
    Passungsursache — dort trägt `params` den Namen und `reason` bleibt leer.
    Wo es eine Ursache gibt, wird sie **durchgereicht, nicht neu berechnet**:
    Sie ist dieselbe, die der Listeneintrag trägt.
    """

    NOT_FOUND = "backup_not_found"
    INCOMPATIBLE = "backup_incompatible"
    SCHEMA_TOO_NEW = "backup_schema_too_new"

    def __init__(
        self,
        code: str,
        message: str,
        *,
        params: dict[str, str] | None = None,
        reason: BackupReason | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.params = params or {}
        self.reason = reason


@dataclass(frozen=True)
class BackupInfo:
    """Eine Sicherung, so wie die Liste sie zeigt."""

    name: str
    created_at: str
    size: int
    fingerprint: str
    compatible: bool
    reason: BackupReason | None = None


def fingerprint_of(config: SourcesConfig) -> str:
    """Die Quellenkennung einer Konfiguration.

    **Gezählt wird, was konfiguriert ist — nicht, was gerade funktioniert.**
    Ginge ein abgelaufener API-Schlüssel ein, wäre eine gestrige Sicherung
    heute „fremd", obwohl sich an der Herkunft der Daten nichts geändert hat.
    Aus demselben Grund zählen weder Geheimnisse noch Dateiinhalte mit.

    Returns:
        Zwölf Hex-Zeichen — sechs wären 24 Bit und damit dünn für eine
        Prüfung, an der ein Bestand hängt.
    """
    parts = [f"{role}={','.join(config.chain(role))}" for role in ROLES]
    parts.append("packages=" + ",".join(sorted(config.packages)))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:12]


def stamp_fingerprint(database_path: str | Path, fingerprint: str) -> None:
    """Schreibt die Kennung in die Datenbank — **nur, wenn noch keine dasteht**.

    Der Stempel sagt, unter welcher Quellenlage der Bestand entstanden ist. Ihn
    beim Start zu überschreiben löschte diese Auskunft: Ein eingespielter
    fremder Bestand sähe aus, als wäre er hier entstanden. Eine Abweichung wird
    **gemeldet, nicht geheilt**.
    """
    connection = get_connection(str(database_path))
    try:
        connection.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO NOTHING",
            (FINGERPRINT_KEY, fingerprint),
        )
        connection.commit()
    finally:
        connection.close()


def _read_stamp(database_file: Path) -> tuple[str | None, int]:
    """Kennung und Schemaversion **aus der Datei selbst**, nicht aus ihrem
    Manifest — das ist der Punkt der Übung."""
    connection = sqlite3.connect(f"file:{database_file}?mode=ro", uri=True)
    try:
        version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        try:
            row = connection.execute(
                "SELECT value FROM meta WHERE key = ?", (FINGERPRINT_KEY,)
            ).fetchone()
        except sqlite3.DatabaseError:
            return None, version  # älter als die `meta`-Tabelle, nicht kaputt
        return (row[0] if row else None), version
    finally:
        connection.close()


class BackupService:
    """Legt Sicherungen an und listet sie."""

    def __init__(self, database_path: str, config: SourcesConfig) -> None:
        """
        Args:
            database_path: Pfad zur laufenden Datenbank.
            config: Dieselbe Instanz, aus der der Betrieb seine Ketten baut.
                Läse der Dienst die Datei erneut, beschriebe er eine
                Konfiguration, die gar nicht läuft.
        """
        self._database = Path(database_path)
        self._config = config
        # **Die ganze Folge Name → Kopie → Manifest → Rotation gehört zusammen.**
        # `_free_name()` prüft, ob ein Pfad frei ist; zwischen dieser Prüfung
        # und dem `VACUUM INTO` liegt bei parallelen Aufrufen genug Zeit, dass
        # ein zweiter Handler denselben Namen wählt. `VACUUM INTO` kann nicht
        # in eine bereits befüllte Zieldatei schreiben.
        #
        # Die Rotation gehört mit hinein: Sie zählt Dateien und löscht die
        # ältesten. Läuft sie, während nebenan eine neue entsteht, zählt sie
        # einen Stand, den es gleich nicht mehr gibt.
        self._lock = threading.Lock()

    @property
    def database_path(self) -> Path:
        return self._database

    @property
    def directory(self) -> Path:
        """Abgeleitet aus dem Datenbankpfad, nicht zusätzlich eingestellt."""
        return self._database.parent / BACKUP_DIRNAME

    @property
    def fingerprint(self) -> str:
        """Die Kennung der **laufenden** Konfiguration."""
        return fingerprint_of(self._config)

    def create(self, *, reason: str = "manual", protect: str = "") -> BackupInfo:
        """Legt eine Sicherung an und räumt die älteste weg, wenn nötig.

        Serialisiert: Gleichzeitige Aufrufe bekommen der Reihe nach je eine
        eigene Sicherung, statt sich gegenseitig die Datei wegzuschreiben.

        Args:
            reason: `manual` oder `pre-restore`. Steht im Manifest, damit
                erkennbar bleibt, welche Sicherung ein Wiederherstellen
                begleitet hat.
            protect: Eine Sicherung, die die Rotation **nicht** wegräumen darf.
                Beim Einlösen ist das die Datei, die gleich eingespielt wird —
                bei zehn vorhandenen oft die älteste, die die Sicherheitskopie
                sonst genau dann löschte, wenn sie gebraucht wird.
        """
        with self._lock:
            return self._create_locked(reason, protect)

    def _create_locked(self, reason: str, protect: str = "") -> BackupInfo:
        self.directory.mkdir(parents=True, exist_ok=True)
        fingerprint = self.fingerprint
        created_at, target = self._free_name(datetime.now(timezone.utc), fingerprint)

        connection = get_connection(str(self._database))
        try:
            connection.execute("VACUUM INTO ?", (str(target),))
        finally:
            connection.close()

        stamp_versions(target, self._config)
        _write_atomic(
            target.with_suffix(".json"),
            json.dumps(
                {
                    "created_at": created_at.isoformat().replace("+00:00", "Z"),
                    "schema_version": SCHEMA_VERSION,
                    "data_versions": stored_versions(target),
                    "sources_fingerprint": _read_stamp(target)[0] or fingerprint,
                    "sources": {role: list(self._config.chain(role)) for role in ROLES},
                    "packages": list(self._config.packages),
                    "reason": reason,
                },
                indent=2,
            ),
        )
        logger.info("backup_created", name=target.name, reason=reason)
        self._rotate(protect)
        return self._info(target)

    def _free_name(self, moment: datetime, fingerprint: str) -> tuple[datetime, Path]:
        """Ein Zeitpunkt, unter dem noch keine Sicherung liegt.

        **Millisekunden, kein Zierrat.** Zwei Sicherungen kurz nacheinander
        trügen bei Sekundenauflösung denselben Namen, und `VACUUM INTO`
        schreibt in keine bestehende Datei — es bräche mit „output file already
        exists" ab. Bei Gleichstand rückt der Stempel um eine Millisekunde vor.
        """
        while True:
            stamp = f"{moment:%Y%m%dT%H%M%S}{moment.microsecond // 1000:03d}Z"
            target = self.directory / f"stockinfo-{stamp}-{fingerprint}.db"
            if not target.exists():
                return moment, target
            moment += timedelta(milliseconds=1)

    def _rotate(self, protect: str = "") -> None:
        """Lässt die zehn jüngsten liegen — die elfte verdrängt die älteste.

        **Es gibt keinen zweiten Löschweg.** Ein `DELETE` wäre nur eine zweite
        Gelegenheit, die falsche Datei zu treffen.

        `protect` nimmt eine Datei aus dem Rennen: Wer gerade eingespielt wird,
        wird nicht weggeräumt, auch wenn er der älteste ist. Verdrängt wird
        dann der nächstältere, sodass am Ende weiterhin zehn liegen.
        """
        files = [
            path
            for path in sorted(self.directory.glob("stockinfo-*.db"))
            if path.name != protect
        ]
        for stale in files[: max(0, len(files) + (1 if protect else 0) - KEEP_BACKUPS)]:
            stale.unlink(missing_ok=True)
            stale.with_suffix(".json").unlink(missing_ok=True)
            logger.info("backup_rotated_out", name=stale.name)

    def list(self) -> list[BackupInfo]:
        """Alle Sicherungen, jüngste zuerst — **auch die unpassenden**, mit
        ihrem Grund. Eine auszublenden hieße, jemanden nach einer Datei suchen
        zu lassen, die er im Verzeichnis liegen sieht."""
        if not self.directory.is_dir():
            return []
        return [
            self._info(path)
            for path in sorted(self.directory.glob("stockinfo-*.db"), reverse=True)
        ]

    def _info(self, path: Path) -> BackupInfo:
        stamped, version = _read_stamp(path)
        manifest = _read_manifest(path)
        fingerprint = stamped or str(manifest.get("sources_fingerprint", ""))
        reason = self._judge(fingerprint, version, stamped, manifest, stored_versions(path))
        return BackupInfo(
            name=path.name,
            created_at=str(manifest.get("created_at", "")),
            size=path.stat().st_size,
            fingerprint=fingerprint,
            compatible=reason is None,
            reason=reason,
        )

    def _judge(
        self, fingerprint: str, version: int, stamped: str | None, manifest: dict, data_versions: dict[str, int]
    ) -> BackupReason | None:
        """Warum die Sicherung nicht passt — oder ``None``, wenn sie passt.

        Technische Lesbarkeit und Integrität werden separat geprüft. Fachliche
        Inkompatibilität entsteht ausschließlich durch data_version.
        """
        if version > SCHEMA_VERSION:
            return BackupReason(
                code="backup_schema_too_new",
                params={"version": str(version), "app": str(SCHEMA_VERSION)},
            )
        declared = manifest.get("sources_fingerprint")
        if stamped and declared and stamped != declared:
            return BackupReason(code="backup_fingerprint_mismatch")
        differences = [
            SourceDifference(field=name, theirs=[str(data_versions.get(name, 1))], ours=[str(value)])
            for name, value in declared_versions(self._config).items()
            if data_versions.get(name, 1) != value
        ]
        if differences:
            return BackupReason(code="backup_data_version_differ", differences=differences)
        return None

    def request_restore(self, name: str, *, force: bool = False) -> BackupInfo:
        """Prüft eine Sicherung und hinterlegt die Absicht.

        **An der laufenden Datenbank ändert sich hier nichts.** Sie trägt offene
        Verbindungen und den Scheduler; getauscht wird beim nächsten Start.

        Raises:
            BackupError: Unbekannter Name, neueres Schema, oder fremde
                Quellenlage ohne `force`.
        """
        info = self.check(name, force=force)
        _write_atomic(
            self._database.parent / PENDING_FILENAME,
            json.dumps({"backup": info.name, "force": force}, indent=2),
        )
        logger.info("restore_requested", name=info.name, force=force)
        return info

    def check(self, name: str, *, force: bool) -> BackupInfo:
        """Die gemeinsame Prüfung von REST-Aufruf und Einlösen beim Start.

        **Zweimal aufgerufen, mit Absicht.** Zwischen Klick und Neustart kann
        sich die Konfiguration ändern oder die Datei verschwinden; eine Prüfung
        nur vorne wäre ein Versprechen auf einen Zustand, den beim Tausch
        niemand nachsieht.

        Ein neueres Schema hebt auch `force` nicht auf: Dort geht es nicht um
        Erlaubnis, sondern darum, dass die App die Datei nicht lesen kann.
        """
        path = self.resolve(name)
        info = self._info(path)
        _, version = _read_stamp(path)
        if version > SCHEMA_VERSION and info.reason is not None:
            raise BackupError(
                BackupError.SCHEMA_TOO_NEW,
                f"Sicherung {name} trägt Schema {version}",
                params={"name": name},
                reason=info.reason,
            )
        if not info.compatible and not force and info.reason is not None:
            raise BackupError(
                BackupError.INCOMPATIBLE,
                f"Sicherung {name} hat eine inkompatible Plugin-Datenversion",
                params={"name": name},
                reason=info.reason,
            )
        return info

    def resolve(self, name: str) -> Path:
        """Vom Namen zur Datei — mit der Musterprüfung **vor** dem Zugriff."""
        if not _NAME_PATTERN.match(name):
            raise BackupError(
                BackupError.NOT_FOUND,
                f"{name} ist kein Sicherungsname",
                params={"name": name},
            )
        path = self.directory / name
        if not path.is_file():
            raise BackupError(
                BackupError.NOT_FOUND,
                f"Sicherung {name} gibt es nicht",
                params={"name": name},
            )
        return path


def apply_pending(database_path: str, config: SourcesConfig) -> str | None:
    """Löst eine vorgemerkte Wiederherstellung ein — **vor** der ersten Verbindung.

    1. Absicht lesen; ohne sie passiert nichts.
    2. Erneut prüfen — die Prüfung beim REST-Aufruf ist keine dauerhafte Zusage.
    3. **Jetzt** den aktuellen Stand sichern. Zwischen Klick und Neustart wird
       weitergeschrieben; eine Sicherung vom Klick fehlten genau diese Zeilen.
    4. Über eine temporäre Zieldatei und atomaren Austausch tauschen; die
       Sicherung wird kopiert, nicht verbraucht.
    5. `-wal`/`-shm` entfernen — sie gehören zur alten Datei. Bliebe eines
       liegen, läse SQLite den neuen Bestand mit dem Journal des vorigen.
    6. Erst danach die Absicht löschen.

    Ein Fehler bricht den Start **nicht** ab und lässt die Absicht liegen: Die
    Datenbank ist unangetastet, und der Wunsch verschwindet nicht spurlos.
    """
    database = Path(database_path)
    pending = database.parent / PENDING_FILENAME
    if not pending.is_file():
        return None

    intent = _read_intent(pending)
    if intent.get("failed"):
        # **Kein zweiter Versuch.** Ein gescheiterter Tausch scheitert beim
        # nächsten Start aus demselben Grund erneut; ihn stumm zu wiederholen
        # hieße, bei jedem Start dieselbe Sicherheitskopie anzulegen. Der
        # Zustand bleibt stehen, bis jemand eine neue Anforderung stellt.
        return None

    service = BackupService(database_path, config)
    name = str(intent.get("backup", ""))
    force = bool(intent.get("force", False))
    temporary = database.with_name(database.name + ".incoming")
    try:
        source = service.resolve(service.check(name, force=force).name)

        if database.is_file():
            service.create(reason="pre-restore", protect=source.name)

        shutil.copy2(source, temporary)
        os.replace(temporary, database)
        for suffix in ("-wal", "-shm"):
            database.with_name(database.name + suffix).unlink(missing_ok=True)
    except Exception as exc:  # noqa: BLE001 — ein Start bricht daran nicht ab
        logger.error("restore_failed", name=name, error=str(exc))
        temporary.unlink(missing_ok=True)
        _write_atomic(
            pending,
            json.dumps({**intent, "failed": f"{type(exc).__name__}: {exc}"}, indent=2),
        )
        return None

    pending.unlink(missing_ok=True)
    logger.info("restore_applied", name=name, force=force)
    return name


def restore_state(database_path: str) -> tuple[str | None, str]:
    """Was von einem angeforderten Wiederherstellen übrig ist.

    **Beides zugleich gibt es nicht.** Nach einem Fehler folgt kein Versuch
    mehr; `pending_restore` wäre eine Ankündigung, die niemand einlöst. Der
    Name wandert in den Grund.

    Returns:
        Den Namen **oder** — nach einem gescheiterten Tausch — `None` und den
        Grund. Ein unlesbarer Eintrag ergibt `None`, nicht den Text `"None"`.
    """
    intent = _read_intent(Path(database_path).parent / PENDING_FILENAME)
    name = intent.get("backup")
    name = name if isinstance(name, str) and name else None
    failed = str(intent.get("failed") or "")
    if failed:
        return None, f"{name}: {failed}" if name else failed
    return name, ""


def stamped_fingerprint(database_path: str | Path) -> str | None:
    """Die Kennung, unter der die **vorhandene** Datenbank entstanden ist."""
    path = Path(database_path)
    if not path.is_file():
        return None
    try:
        return _read_stamp(path)[0]
    except sqlite3.DatabaseError:
        return None


def _read_intent(pending: Path) -> dict:
    """Die hinterlegte Absicht — oder eine leere, wenn keine lesbar ist."""
    if not pending.is_file():
        return {}
    try:
        loaded = json.loads(pending.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _read_manifest(database_file: Path) -> dict:
    """Das Manifest neben einer Sicherung — oder eine leere Auskunft. Eine
    fehlende macht die Sicherung nicht unbrauchbar: Die Kennung steht auch in
    der Datenbank."""
    try:
        loaded = json.loads(database_file.with_suffix(".json").read_text("utf-8"))
    except (OSError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _write_atomic(target: Path, content: str) -> None:
    """Schreibt eine Datei so, dass sie nie halb dasteht.

    Ein abgebrochener Schreibvorgang hinterließe sonst ein Manifest, das
    niemand lesen kann — und die Sicherung daneben wäre nicht mehr erklärbar.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
