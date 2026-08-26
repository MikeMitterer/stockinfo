"""Der Pflichtablauf für den Identitäts-Umzug — vorrechnen, bestätigen, berichten.

Drei Endpunkte für die drei Schritte, und sie sind die einzigen Fachwege, die
im Pending-Zustand offen bleiben. Warum es sie überhaupt gibt, steht in
`app/migration.py`: `init_db()` läuft im Lifespan, bevor die App den ersten
Request bedient — ein UI, das erst danach erreichbar wird, könnte niemanden
mehr warnen.

Router enthalten nur HTTP-Belange. Was der Umzug tut, steht in `app.migration`
und `app.db`.
"""

import sqlite3
from datetime import datetime, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.db import get_connection, run_migration
from app.migration import MigrationPlan, Rejection, plan_migration
from app.migration_guard import REASON_STARTUP_FAILED, MigrationGate
from app.models import MigrationPreview, MigrationReport, RejectedInstrument

logger = structlog.get_logger()

router = APIRouter(tags=["migration"])

SettingsDep = Annotated[Settings, Depends(get_settings)]

# Der Riegel als Modulzustand.
#
# **Eine** Quelle, wie der Entwurf verlangt: Guard-Middleware, `/ready`,
# `/operational` und die Bestätigung fragen dieselbe Instanz. Sie über die
# Dependency-Injection zu reichen wäre die formal sauberere Form — sie ist
# aber Zustand der laufenden Instanz, nicht Konfiguration, und ein zweiter
# Wert wäre genau das Loch, das der Entwurf schließen will.
_gate = MigrationGate()


def get_gate() -> MigrationGate:
    """Der eine Riegel dieser Instanz.

    Returns:
        Die gemeinsame `MigrationGate`.
    """
    return _gate


# Die Felder eines Ablehnungseintrags — **eine** Liste, drei Verbraucher.
#
# Vorschau, Bestätigungsantwort und gespeicherter Bericht bauen dasselbe
# `RejectedInstrument`. Bis Runde 31 taten sie das aus **zwei** neunstelligen
# Aufzählungen, und genau deshalb mussten Name, Börse, Gattung und Währung an
# beiden Stellen einzeln nachgetragen werden. Zwei Serialisierungsregeln für
# dasselbe Ding sind eine zweite Wahrheit; die nächste Eigenschaft hätte
# wieder an einer davon gefehlt.
#
# Die **SQL-Auswahl** bleibt getrennt — sie hängt an der Tabelle, nicht am
# Vertrag. Dass sie vollständig ist, sichert der HTTP-Test mit nichtleeren
# Werten ab, nicht diese Liste.
_REJECTION_FIELDS = (
    "symbol",
    "isin",
    "name",
    "exchange",
    "type",
    "currency",
    "reason",
    "quotes",
    "daily_closes",
)


def _as_rejected(source: Rejection | sqlite3.Row) -> RejectedInstrument:
    """Übersetzt einen Planeintrag **oder** eine Berichtszeile in die REST-Form.

    Beide tragen dieselben Feldnamen — der Plan als Attribute, die Zeile als
    Spalten. Ein Mapper für beide heißt: Eine neue Eigenschaft wird an genau
    einer Stelle verdrahtet.

    Args:
        source: Ein `Rejection` aus dem Plan oder eine Zeile aus
            `migration_rejections`.

    Returns:
        Der REST-Eintrag.
    """
    if isinstance(source, Rejection):
        values = {field: getattr(source, field) for field in _REJECTION_FIELDS}
    else:
        values = {field: source[field] for field in _REJECTION_FIELDS}
    return RejectedInstrument(**values)


def _preview(plan: MigrationPlan) -> MigrationPreview:
    """Baut die Vorschau aus dem Plan."""
    return MigrationPreview(
        pending=plan.needs_migration,
        migrating=len(plan.migrated),
        unchanged=plan.unchanged,
        rejected=[_as_rejected(rejection) for rejection in plan.rejected],
        lost_quotes=plan.lost_quotes,
        lost_daily_closes=plan.lost_daily_closes,
    )


@router.get("/migration", response_model=MigrationPreview)
def migration_preview(settings: SettingsDep) -> MigrationPreview:
    """Rechnet vor, was der Umzug täte — **ohne** etwas zu ändern.

    Die Verbindung wird ausdrücklich **schreibgeschützt** geöffnet. Das ist
    keine Vorsicht, sondern die Zusage selbst: Würde hier auch nur eine Spalte
    angelegt, hätte Phase 1 die Datenbank angefasst, bevor der Benutzer die
    Liste gesehen hat.
    """
    connection = get_connection(settings.database_path)
    try:
        return _preview(plan_migration(connection))
    finally:
        connection.close()


@router.post("/migration/confirm", response_model=MigrationReport)
def migration_confirm(settings: SettingsDep) -> MigrationReport:
    """Führt den Umzug aus — auf ausdrückliche Bestätigung, **genau einmal**.

    **Anspruch und Freigabe sind getrennt**, und das ist der Kern. Bis Runde
    30 stand hier ein `confirm()`, das den Riegel öffnete und den Scheduler
    startete, *bevor* der Umzug begann: Während er lief, meldete `/ready`
    schon `ok`, normale Requests durften auf den alten Bestand, und der
    Scheduler schrieb hinein.

    Jetzt nimmt `claim()` den Umzug an sich, ohne etwas freizugeben; die
    Fachwege bleiben gesperrt, bis der Commit durch ist. Erst dann `release()`.
    Scheitert der Umzug, gibt `abandon()` nur den Anspruch zurück — der Riegel
    bleibt zu, und ein neuer Versuch ist möglich.

    Ein zweiter, gleichzeitiger Aufruf bekommt `409`; ebenso einer, der nichts
    mehr vorfindet.

    **Das gilt auch für den Wiederholungsweg.** Ist der Umzug festgeschrieben
    und nur der Betriebsstart gescheitert, stößt eine weitere Bestätigung ihn
    erneut an — aber genau eine. Die übrigen bekommen `409`, solange der
    Versuch läuft.
    """
    gate = get_gate()

    # Der Umzug ist längst durch; was fehlt, ist der Betrieb. Ein zweiter
    # Aufruf ist dann kein Fehler, sondern der Wiederholungsweg.
    #
    # **Gefragt wird durch den Anspruch hindurch, nicht davor.** Ein
    # vorgeschaltetes `if gate.startup_failed` wäre wieder das Loch aus Runde
    # 32: Zwischen der Frage und der Ausführung dürfte ein zweiter Aufrufer
    # dieselbe Antwort bekommen. `retry_release` beansprucht und führt in
    # einem Zug aus; wer nicht gewinnt, bekommt `None` und läuft unten in
    # den `409`.
    retried = gate.retry_release()
    if retried is not None:
        if retried:
            return _stored_report(settings.database_path)
        raise HTTPException(status_code=503, detail=REASON_STARTUP_FAILED)

    if not gate.claim():
        raise HTTPException(
            status_code=409,
            detail="Es steht kein Umzug aus, oder Umzug beziehungsweise "
            "Betriebsstart laufen bereits.",
        )

    stamp = datetime.now(timezone.utc).isoformat()
    try:
        plan = run_migration(settings.database_path, rejected_at=stamp)
    except Exception:
        # Die Transaktion rollt zurück, der Bestand ist unverändert alt. Nur
        # der Anspruch geht zurück — freigegeben wurde nie etwas.
        gate.abandon()
        logger.exception("migration_failed")
        raise

    if not gate.release():
        # **Der Umzug ist festgeschrieben, der Betrieb nicht angelaufen.**
        # Beides gehört gesagt: `503` statt `200`, denn eine erfolgreiche
        # Bestätigung hieße, der Dienst sei bereit — und das ist er nicht.
        # Zurückgerollt wird nichts; die Daten *sind* umgezogen.
        raise HTTPException(status_code=503, detail=REASON_STARTUP_FAILED)

    logger.info("migration_confirmed", rejected=len(plan.rejected))
    return MigrationReport(
        completed=True,
        rejected=[_as_rejected(rejection) for rejection in plan.rejected],
    )


@router.get("/migration/report", response_model=MigrationReport)
def migration_report(settings: SettingsDep) -> MigrationReport:
    """Was tatsächlich geschehen ist — auch lange danach noch.

    Gelesen wird aus dem Berichtsspeicher, nicht aus dem Bestand: Die
    abgelehnten Zeilen sind dort nicht mehr, und genau deshalb gibt es den
    Speicher.
    """
    return _stored_report(settings.database_path)


def _stored_report(database_path: str) -> MigrationReport:
    """Liest den gespeicherten Bericht.

    Args:
        database_path: Pfad zur SQLite-Datei.

    Returns:
        Der Bericht; ``completed=False`` mit leerer Liste, wenn noch nie ein
        Umzug gelaufen ist — kein Fehler, nur nichts zu berichten.
    """
    connection = get_connection(database_path)
    try:
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' "
            "AND name = 'migration_rejections'"
        ).fetchone()
        if exists is None:
            return MigrationReport(completed=False, rejected=[])

        rows = connection.execute(
            "SELECT " + ", ".join(_REJECTION_FIELDS) + " FROM migration_rejections "
            "ORDER BY symbol"
        ).fetchall()
    finally:
        connection.close()

    return MigrationReport(
        completed=True, rejected=[_as_rejected(row) for row in rows]
    )
