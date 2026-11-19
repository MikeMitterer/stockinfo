"""Der Pflichtablauf für den Identitäts-Umzug — vorrechnen, bestätigen, berichten.

Was der Umzug an der Datenbank tut, steht in `app.persistence.migration` und
`app.persistence.db`. Hier steht die Steuerung: wann er laufen darf, wie Riegel
und Umzug ineinandergreifen und was danach berichtet wird. Der Router
`routers/migration.py` übersetzt das nur in HTTP.
"""

from collections.abc import Mapping
from datetime import datetime, timezone

import structlog

from app.migration_guard import MigrationGate
from app.models import MigrationPreview, MigrationReport, RejectedInstrument
from app.persistence.db import preview_migration, run_migration, stored_rejections
from app.persistence.migration import MigrationPlan, Rejection

logger = structlog.get_logger()


class MigrationNotPendingError(Exception):
    """Es steht kein Umzug aus, oder Umzug beziehungsweise Betriebsstart laufen bereits."""


class StartupFailedError(Exception):
    """Der Umzug ist festgeschrieben, der Betrieb nicht angelaufen."""


# Die Felder eines Ablehnungseintrags — abgeleitet aus dem REST-Modell, nicht
# aufgezählt.
#
# Vorschau, Bestätigungsantwort und gespeicherter Bericht bauen dasselbe
# `RejectedInstrument`. Eine eigene Aufzählung daneben wäre eine zweite
# Wahrheit: Ein neues Feld im Modell hätte an ihr gefehlt. Der Bericht liest
# alle Spalten (`stored_rejections`); dass sie das Modell vollständig füllen,
# sichert der HTTP-Test mit nichtleeren Werten ab.
_REJECTION_FIELDS = tuple(RejectedInstrument.model_fields)


def _as_rejected(source: Rejection | Mapping[str, object]) -> RejectedInstrument:
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


def preview(database_path: str) -> MigrationPreview:
    """Rechnet vor, was der Umzug täte — **ohne** etwas zu ändern.

    Die Verbindung wird ausdrücklich **schreibgeschützt** geöffnet. Das ist
    keine Vorsicht, sondern die Zusage selbst: Würde hier auch nur eine Spalte
    angelegt, hätte Phase 1 die Datenbank angefasst, bevor der Benutzer die
    Liste gesehen hat.
    """
    return _preview(preview_migration(database_path))


def confirm(database_path: str, gate: MigrationGate) -> MigrationReport:
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

    **Das gilt auch für den Wiederholungsweg.** Ist der Umzug festgeschrieben
    und nur der Betriebsstart gescheitert, stößt eine weitere Bestätigung ihn
    erneut an — aber genau eine.

    Raises:
        MigrationNotPendingError: Kein Umzug steht aus, oder ein anderer
            Aufruf hält ihn oder den Betriebsstart gerade.
        StartupFailedError: Der Umzug ist festgeschrieben, der Betrieb läuft
            nicht an.
    """
    # Der Umzug ist längst durch; was fehlt, ist der Betrieb. Ein zweiter
    # Aufruf ist dann kein Fehler, sondern der Wiederholungsweg.
    #
    # **Gefragt wird durch den Anspruch hindurch, nicht davor.** Ein
    # vorgeschaltetes `if gate.startup_failed` wäre wieder das Loch aus Runde
    # 32: Zwischen der Frage und der Ausführung dürfte ein zweiter Aufrufer
    # dieselbe Antwort bekommen. `retry_release` beansprucht und führt in
    # einem Zug aus; wer nicht gewinnt, bekommt `None` und läuft unten in
    # den Anspruch.
    retried = gate.retry_release()
    if retried is not None:
        if retried:
            return stored_report(database_path)
        raise StartupFailedError

    if not gate.claim():
        raise MigrationNotPendingError

    stamp = datetime.now(timezone.utc).isoformat()
    try:
        plan = run_migration(database_path, rejected_at=stamp)
    except Exception:
        # Die Transaktion rollt zurück, der Bestand ist unverändert alt. Nur
        # der Anspruch geht zurück — freigegeben wurde nie etwas.
        gate.abandon()
        logger.exception("migration_failed")
        raise

    if not gate.release():
        # **Der Umzug ist festgeschrieben, der Betrieb nicht angelaufen.**
        # Zurückgerollt wird nichts; die Daten *sind* umgezogen.
        raise StartupFailedError

    logger.info("migration_confirmed", rejected=len(plan.rejected))
    return MigrationReport(
        completed=True,
        rejected=[_as_rejected(rejection) for rejection in plan.rejected],
    )


def stored_report(database_path: str) -> MigrationReport:
    """Was tatsächlich geschehen ist — aus dem Berichtsspeicher.

    Gelesen wird nicht aus dem Bestand: Die abgelehnten Zeilen sind dort nicht
    mehr, und genau deshalb gibt es den Speicher.

    Returns:
        Der Bericht; ``completed=False`` mit leerer Liste, wenn noch nie ein
        Umzug gelaufen ist — kein Fehler, nur nichts zu berichten.
    """
    rows = stored_rejections(database_path)
    if rows is None:
        return MigrationReport(completed=False, rejected=[])
    return MigrationReport(
        completed=True, rejected=[_as_rejected(row) for row in rows]
    )
