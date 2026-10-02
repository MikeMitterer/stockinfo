"""Das Datenbankschema **vor** T-21 — an einer Stelle, für alle Tests.

Drei Testdateien legten sich diese Tabellen bis Übergabe 2B je selbst an, und
die drei Kopien waren nicht gleich: In zweien fehlten `quotes.volume` und
`quotes.currency`. Damit war das Fixture keine Alt-Datenbank, sondern eine, die
es nie gegeben hat — der echte Bestand trägt beide Spalten.

**Aufgefallen ist es nicht in den Tests, sondern im Browser.** Der ganze
Umzugsablauf lief grün durch; erst die Oberfläche zeigte danach „Instrumente
konnten nicht geladen werden", und dahinter stand ein `500` mit
`no such column: q.currency`. Ein Fixture, das weniger Spalten hat als die
Wirklichkeit, prüft eine Migration, die niemand fahren wird.

Nachgesehen wurde mit `PRAGMA table_info(quotes)` auf `data/stockinfo.db`:
``id, instrument_id, price, quote_time, volume, currency, fetched_at``.

Dasselbe galt für `instruments` und `daily_closes`: `provider`, `ter`,
`replication`, `fund_size` und `meta_fetched_at` stehen seit dem ersten
Schema (`e5947bf`), `daily_closes.currency` seit dessen erster Fassung
(`8fd0738`). Ohne sie bildeten die SQLModel-Modelle eine umgezogene
Datenbank nicht ab, die es so nie gab (T-91).

Was hier bewusst **nicht** steht: `ticker`, `mic` und `listing_id`. Genau ihr
Fehlen macht diese Datenbank zu einer, die den Umzug braucht.
"""

import sqlite3

LEGACY_SCHEMA = """
    CREATE TABLE instruments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        isin TEXT UNIQUE, symbol TEXT NOT NULL,
        exchange TEXT, name TEXT, type TEXT, currency TEXT,
        provider TEXT, ter REAL, replication TEXT, fund_size REAL,
        first_seen TEXT NOT NULL, meta_fetched_at TEXT
    );
    CREATE TABLE quotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        instrument_id INTEGER NOT NULL REFERENCES instruments(id),
        price REAL NOT NULL, quote_time TEXT NOT NULL,
        volume INTEGER, currency TEXT,
        fetched_at TEXT NOT NULL, UNIQUE (instrument_id, quote_time)
    );
    CREATE TABLE daily_closes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        instrument_id INTEGER NOT NULL REFERENCES instruments(id),
        date TEXT NOT NULL, close REAL NOT NULL, currency TEXT,
        UNIQUE (instrument_id, date)
    );
"""

#: Der Zeitpunkt, den jede Alt-Zeile als `first_seen` trägt.
LEGACY_FIRST_SEEN = "2026-01-01T00:00:00+00:00"


def create_legacy_tables(connection: sqlite3.Connection) -> None:
    """Legt die drei Tabellen im Stand vor T-21 an.

    Args:
        connection: Offene Verbindung zu einer **leeren** Datenbank.
    """
    connection.executescript(LEGACY_SCHEMA)
