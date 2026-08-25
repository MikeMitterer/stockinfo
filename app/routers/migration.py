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
    """Übersetzt einen Planeintrag in die REST-Form.

    **Vollständig**, seit Runde 30. Vorher fielen Name, Börse, Gattung und
    Währung hier heraus: Die Tabelle hielt sie, das REST-Modell kannte nur den
    Namen, und `_as_rejected` setzte nicht einmal den. Das UI in 2B hätte den
    Benutzer auffordern sollen, ein Papier neu zu erfassen, und ihm dazu nur
    ein Symbol nennen können.
    """
    return RejectedInstrument(
        symbol=rejection.symbol,
        isin=rejection.isin,
        name=rejection.name,
        exchange=rejection.exchange,
        type=rejection.type,
        currency=rejection.currency,
        reason=rejection.reason,
        quotes=rejection.quotes,
        daily_closes=rejection.daily_closes,
    )


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
    """
    gate = get_gate()
    if not gate.claim():
        raise HTTPException(
            status_code=409,
            detail="Es steht kein Umzug aus, oder er läuft bereits.",
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

    gate.release()
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
            "SELECT symbol, isin, name, exchange, type, currency, reason, "
            "quotes, daily_closes FROM migration_rejections ORDER BY symbol"
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
                exchange=row["exchange"],
                type=row["type"],
                currency=row["currency"],
                reason=row["reason"],
                quotes=row["quotes"],
                daily_closes=row["daily_closes"],
            )
            for row in rows
        ],
    )
