"""Generische Detailpersistenz; alle Aufrufer teilen die Repository-Transaktion."""

import json
import sqlite3
import uuid

from app.detail_models import DetailDefinition
from app.details import CANONICAL, merge_value

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


def initialize(connection: sqlite3.Connection) -> None:
    """Übernimmt alte Werte einmal verlustlos; alte Spalten bleiben nur Schemahülle."""
    connection.executescript(SCHEMA)
    connection.execute("INSERT OR IGNORE INTO meta(key,value) VALUES ('details_generation_id',?)", (str(uuid.uuid4()),))
    if connection.execute("SELECT 1 FROM meta WHERE key='details_migrated'").fetchone():
        return
    for stored in connection.execute('SELECT * FROM instruments').fetchall():
        row = dict(stored)
        for field in CANONICAL:
            value = row.get(field)
            if value is not None:
                if field == 'accumulating':
                    value = bool(value)
                put_provider(connection, row['id'], field, {
                    'value': value, 'source': row.get('source') or 'legacy',
                    'currency': row.get('fund_currency') if field == 'fund_size' else None,
                    'as_of': row.get('meta_fetched_at'),
                })
    for stored in connection.execute('SELECT * FROM instrument_overrides').fetchall():
        row = dict(stored)
        for field in CANONICAL:
            value = row.get(field)
            if field == 'accumulating' and value is not None:
                value = bool(value)
            put_manual(connection, row['instrument_id'], field, value, None, row['updated_at'])
    # Nach erfolgreicher Übernahme existiert nur eine schreibbare Wahrheit.
    columns = {row[1] for row in connection.execute('PRAGMA table_info(instruments)')}
    retained = set(CANONICAL) & columns
    if retained:
        connection.execute('UPDATE instruments SET ' + ', '.join(f'{field}=NULL' for field in sorted(retained)))
    connection.execute('DELETE FROM instrument_overrides')
    connection.execute("INSERT INTO meta(key,value) VALUES ('details_migrated','1')")


def sync_catalog(connection: sqlite3.Connection, definitions: list[DetailDefinition]) -> int:
    """Schema und monotonen Zähler atomar fortschreiben, auch bei Entfernung."""
    serialized = json.dumps([entry.model_dump() for entry in definitions], sort_keys=True)
    connection.execute('BEGIN IMMEDIATE')
    values = dict(connection.execute("SELECT key,value FROM meta WHERE key IN ('details_schema','details_version')"))
    version = int(values.get('details_version', '0'))
    if serialized != values.get('details_schema'):
        version += 1
        connection.executemany('INSERT INTO meta(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',
            [('details_schema', serialized), ('details_version', str(version))])
    return version


def catalog(connection: sqlite3.Connection) -> list[DetailDefinition]:
    """Das validierte Profilschema der laufenden Instanz."""
    row = connection.execute("SELECT value FROM meta WHERE key='details_schema'").fetchone()
    return [DetailDefinition.model_validate(value) for value in json.loads(row[0])] if row else []


def put_provider(connection, instrument_id: int, field: str, entry: dict) -> None:
    """Speichert einen Quellenwert einschließlich expliziter Leerstelle."""
    connection.execute('''INSERT INTO detail_values(instrument_id,field,source,value,currency,as_of)
        VALUES (?,?,?,?,?,?) ON CONFLICT(instrument_id,field,source) DO UPDATE SET
        value=excluded.value,currency=excluded.currency,as_of=excluded.as_of''',
        (instrument_id, field, entry.get('source') or 'legacy', json.dumps(entry.get('value')),
         entry.get('currency'), entry.get('as_of')))


def put_manual(connection, instrument_id: int, field: str, value, currency, as_of) -> None:
    """Null entfernt nur die manuelle Eingabe, niemals den Quellenwert."""
    if value is None:
        connection.execute('DELETE FROM detail_overrides WHERE instrument_id=? AND field=?', (instrument_id, field))
    else:
        connection.execute('''INSERT INTO detail_overrides(instrument_id,field,value,currency,as_of)
            VALUES (?,?,?,?,?) ON CONFLICT(instrument_id,field) DO UPDATE SET
            value=excluded.value,currency=excluded.currency,as_of=excluded.as_of''',
            (instrument_id, field, json.dumps(value), currency, as_of))


def read(connection, row: dict, *, effective: bool = False) -> dict:
    """Projiziert Quelle, Eingabe und wirksamen Wert aus demselben Speicher."""
    definitions = catalog(connection)
    by_name = {definition.name: definition for definition in definitions}
    providers: dict[str, list[dict]] = {}
    for stored in connection.execute('SELECT * FROM detail_values WHERE instrument_id=?', (row['id'],)):
        entry = dict(stored)
        entry['value'] = json.loads(entry['value'])
        providers.setdefault(entry['field'], []).append(entry)
    manual = {}
    for stored in connection.execute('SELECT * FROM detail_overrides WHERE instrument_id=?', (row['id'],)):
        entry = dict(stored)
        entry['value'] = json.loads(entry['value'])
        manual[entry['field']] = entry
    applicable = {definition.name for definition in definitions if definition.applies(row.get('type'), row.get('kind'))}
    details = {}
    result = dict(row)
    result['manual_fields'], result['shadowed_fields'] = [], []
    for field in set(CANONICAL) | applicable | set(providers) | set(manual):
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
