"""Der Pflichtablauf für den Identitäts-Umzug — vorrechnen, bestätigen, berichten.

Drei Endpunkte für die drei Schritte, und sie sind die einzigen Fachwege, die
im Pending-Zustand offen bleiben. Warum es sie überhaupt gibt, steht in
`app/migration.py`: `init_db()` läuft im Lifespan, bevor die App den ersten
Request bedient — ein UI, das erst danach erreichbar wird, könnte niemanden
mehr warnen.

Router enthalten nur HTTP-Belange. Was der Umzug tut, steht in `app.migration`
und `app.db`.
"""

from datetime import datetime, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.db import get_connection, run_migration
from app.migration import MigrationPlan, Rejection, plan_migration
from app.migration_guard import MigrationGate
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


def _as_rejected(rejection: Rejection) -> RejectedInstrument:
    """Übersetzt einen Planeintrag in die REST-Form."""
    return RejectedInstrument(
        symbol=rejection.symbol,
        isin=rejection.isin,
        reason=rejection.reason,
        quotes=rejection.quotes,
        daily_closes=rejection.daily_closes,
    )


def _preview(plan: MigrationPlan) -> MigrationPreview:
    """Baut die Vorschau aus dem Plan."""
    return MigrationPreview(
        pending=plan.is_pending,
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

    `MigrationGate.confirm()` gewinnt genau ein Aufrufer; alle weiteren
    bekommen `409`. Ohne diese Verriegelung liefen zwei gleichzeitige
    Bestätigungen beide durch, und eine wiederholte gäbe den Betrieb ein
    zweites Mal frei.

    Der Scheduler wird hier **nicht** gestartet: Das entscheidet der Lifespan,
    der ihn beim Übergang in den Normalbetrieb übernimmt.
    """
    gate = get_gate()
    if not gate.confirm():
        raise HTTPException(
            status_code=409,
            detail="Es steht kein Umzug aus, oder er läuft bereits.",
        )

    stamp = datetime.now(timezone.utc).isoformat()
    try:
        plan = run_migration(settings.database_path, rejected_at=stamp)
    except Exception:
        # Der Umzug ist gescheitert und hat nichts geändert — die Transaktion
        # rollt zurück. Der Riegel muss zurück, sonst stünde der Dienst offen,
        # obwohl der Bestand unverändert alt ist.
        gate.block()
        logger.exception("migration_failed")
        raise

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
    connection = get_connection(settings.database_path)
    try:
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' "
            "AND name = 'migration_rejections'"
        ).fetchone()
        if exists is None:
            # Noch nie ein Umzug gelaufen. Kein Fehler — nur nichts zu
            # berichten.
            return MigrationReport(completed=False, rejected=[])

        rows = connection.execute(
            "SELECT symbol, isin, name, reason, quotes, daily_closes "
            "FROM migration_rejections ORDER BY symbol"
        ).fetchall()
    finally:
        connection.close()

    return MigrationReport(
        completed=True,
        rejected=[
            RejectedInstrument(
                symbol=row["symbol"],
                isin=row["isin"],
                name=row["name"],
                reason=row["reason"],
                quotes=row["quotes"],
                daily_closes=row["daily_closes"],
            )
            for row in rows
        ],
    )
