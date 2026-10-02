"""Generische Detailpersistenz; alle Aufrufer teilen die Repository-Session."""

import json
import sqlite3
import uuid

from sqlalchemy import delete, select, text, update
from sqlalchemy.dialects.sqlite import insert
from sqlmodel import Session, col

from app.detail_models import DetailDefinition
from app.details import CANONICAL, merge_value
from app.persistence.session import fetch_all
from app.persistence.tables import (
    DetailOverrideRecord,
    DetailValueRecord,
    InstrumentRecord,
    table_of,
)

SCHEMA = '''
CREATE TABLE IF NOT EXISTS detail_values (
    instrument_id INTEGER NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    field TEXT NOT NULL,
    source TEXT NOT NULL,
    value TEXT NOT NULL,
    currency TEXT,
    as_of TEXT,
    PRIMARY KEY (instrument_id, field, source)
);
CREATE TABLE IF NOT EXISTS detail_overrides (
    instrument_id INTEGER NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    field TEXT NOT NULL,
    value TEXT NOT NULL,
    currency TEXT,
    as_of TEXT,
    PRIMARY KEY (instrument_id, field)
);
'''


def create_schema(connection: sqlite3.Connection) -> None:
    """Legt die Detailtabellen und die Generationskennung an — Teil von `init_db`."""
    connection.executescript(SCHEMA)
    connection.execute("INSERT OR IGNORE INTO meta(key,value) VALUES ('details_generation_id',?)", (str(uuid.uuid4()),))


def migrate_legacy_values(session: Session) -> None:
    """Übernimmt alte Werte einmal verlustlos; alte Spalten bleiben nur Schemahülle.

    Schreibt über dieselben `put_provider` und `put_manual` wie das Repository.
    """
    if session.execute(text("SELECT 1 FROM meta WHERE key='details_migrated'")).first():
        return
    fund_currencies = {}
    columns = [col(InstrumentRecord.id), col(InstrumentRecord.source), col(InstrumentRecord.meta_fetched_at),
               *(col(getattr(InstrumentRecord, field)) for field in CANONICAL)]
    for row in fetch_all(session, select(*columns)):
        fund_currencies[row['id']] = row.get('fund_currency')
        for field in CANONICAL:
            value = row.get(field)
            if value is not None:
                if field == 'accumulating':
                    value = bool(value)
                put_provider(session, row['id'], field, {
                    'value': value, 'source': row.get('source') or 'legacy',
                    'currency': row.get('fund_currency') if field == 'fund_size' else None,
                    'as_of': row.get('meta_fetched_at'),
                })
    for row in fetch_all(session, text('SELECT * FROM instrument_overrides')):
        for field in CANONICAL:
            value = row.get(field)
            if field == 'accumulating' and value is not None:
                value = bool(value)
            currency = (row.get('fund_currency') or fund_currencies.get(row['instrument_id'])) if field == 'fund_size' else None
            put_manual(session, row['instrument_id'], field, value, currency, row['updated_at'])
    # Nach erfolgreicher Übernahme existiert nur eine schreibbare Wahrheit.
    session.execute(update(InstrumentRecord).values({field: None for field in CANONICAL}))
    session.execute(text('DELETE FROM instrument_overrides'))
    session.execute(text("INSERT INTO meta(key,value) VALUES ('details_migrated','1')"))


def sync_catalog(session: Session, definitions: list[DetailDefinition]) -> int:
    """Schema und monotonen Zähler atomar fortschreiben, auch bei Entfernung.

    Die Session muss mit `immediate=True` geöffnet sein: Zwei Prozesse sähen
    sonst denselben alten Stand und zählten beide von ihm aus weiter.
    """
    serialized = json.dumps([entry.model_dump() for entry in definitions], sort_keys=True)
    values = dict(session.execute(text("SELECT key,value FROM meta WHERE key IN ('details_schema','details_version')")).tuples().all())
    version = int(values.get('details_version', '0'))
    if serialized != values.get('details_schema'):
        version += 1
        session.execute(text('INSERT INTO meta(key,value) VALUES (:key,:value) ON CONFLICT(key) DO UPDATE SET value=excluded.value'),
            [{'key': 'details_schema', 'value': serialized}, {'key': 'details_version', 'value': str(version)}])
    return version


def catalog(session: Session) -> list[DetailDefinition]:
    """Das validierte Profilschema der laufenden Instanz."""
    row = session.execute(text("SELECT value FROM meta WHERE key='details_schema'")).first()
    return [DetailDefinition.model_validate(value) for value in json.loads(row[0])] if row else []


def put_provider(session: Session, instrument_id: int, field: str, entry: dict) -> None:
    """Speichert einen Quellenwert einschließlich expliziter Leerstelle."""
    statement = insert(DetailValueRecord).values(
        instrument_id=instrument_id, field=field, source=entry.get('source') or 'legacy',
        value=json.dumps(entry.get('value')), currency=entry.get('currency'), as_of=entry.get('as_of'))
    session.execute(statement.on_conflict_do_update(
        index_elements=['instrument_id', 'field', 'source'],
        set_={'value': statement.excluded.value, 'currency': statement.excluded.currency,
              'as_of': statement.excluded.as_of}))


def put_manual(session: Session, instrument_id: int, field: str, value, currency, as_of) -> None:  # noqa: ANN001
    """Null entfernt nur die manuelle Eingabe, niemals den Quellenwert."""
    if value is None:
        session.execute(delete(DetailOverrideRecord).where(
            col(DetailOverrideRecord.instrument_id) == instrument_id, col(DetailOverrideRecord.field) == field))
        return
    statement = insert(DetailOverrideRecord).values(
        instrument_id=instrument_id, field=field, value=json.dumps(value), currency=currency, as_of=as_of)
    session.execute(statement.on_conflict_do_update(
        index_elements=['instrument_id', 'field'],
        set_={'value': statement.excluded.value, 'currency': statement.excluded.currency,
              'as_of': statement.excluded.as_of}))


def read(session: Session, row: dict, *, effective: bool = False) -> dict:
    """Projiziert Quelle, Eingabe und wirksamen Wert aus demselben Speicher."""
    definitions = catalog(session)
    by_name = {definition.name: definition for definition in definitions}
    providers: dict[str, list[dict]] = {}
    for entry in fetch_all(session, select(table_of(DetailValueRecord)).where(col(DetailValueRecord.instrument_id) == row['id'])):
        entry['value'] = json.loads(entry['value'])
        providers.setdefault(entry['field'], []).append(entry)
    manual = {}
    for entry in fetch_all(session, select(table_of(DetailOverrideRecord)).where(col(DetailOverrideRecord.instrument_id) == row['id'])):
        entry['value'] = json.loads(entry['value'])
        manual[entry['field']] = entry
    applicable = {definition.name for definition in definitions if definition.applies(row.get('type'), row.get('kind'))}
    details = {}
    result = dict(row)
    result['manual_fields'], result['shadowed_fields'] = [], []
    for field in sorted(set(CANONICAL) | applicable | set(providers) | set(manual)):
        definition = by_name.get(field)
        sources = definition.sources if definition else []
        candidates = providers.get(field, [])
        candidates.sort(key=lambda entry: sources.index(entry['source']) if entry['source'] in sources else len(sources))
        provider = next((entry for entry in candidates if entry['value'] is not None), None)
        unit = definition.unit if definition else CANONICAL.get(field, (None, None))[1]
        value = merge_value(provider, manual.get(field), unit)
        if field in applicable:
            details[field] = value.model_dump()
        if field in CANONICAL:
            result[field] = value.value if effective else provider['value'] if provider else None
            result[f'manual_{field}'] = value.manual_value
            if value.origin == 'manual':
                result['manual_fields'].append(field)
            if value.shadowed:
                result['shadowed_fields'].append(field)
    result['details'] = details
    return result
