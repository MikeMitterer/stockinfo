"""Legt eine Datenbank im Altformat an — für den Migrationsweg der Browserprüfung.

Das Schema kommt aus `tests/legacy_schema.py`, damit es nur eine Fassung des
Altformats gibt. Zwei Papiere lassen sich umziehen, eines nicht: Es hat keine
Börsenendung und erscheint in der Vorschau als abgelehnt.

Aufruf aus dem Projekt-Root:
    .venv/bin/python scripts/make_legacy_database.py <ziel.db>
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.legacy_schema import LEGACY_FIRST_SEEN, create_legacy_tables  # noqa: E402

INSTRUMENTS = [
    ("EUNL.DE", "IE00B4L5Y983", "iShares Core MSCI World UCITS ETF", "GER", "ETF", "EUR"),
    ("APC.DE", "US0378331005", "Apple Inc.", "GER", "EQUITY", "EUR"),
    ("XYZ", None, "Papier ohne Börsenendung", None, None, None),
]


def main(target: Path) -> None:
    """Schreibt die Altdatenbank nach `target`; eine vorhandene Datei bleibt stehen."""
    if target.exists():
        raise SystemExit(f"{target} gibt es schon — bitte einen leeren Pfad angeben")
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(target) as connection:
        create_legacy_tables(connection)
        connection.executemany(
            "INSERT INTO instruments (symbol, isin, name, exchange, type, currency, first_seen) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(*row, LEGACY_FIRST_SEEN) for row in INSTRUMENTS],
        )
        connection.executemany(
            "INSERT INTO quotes (instrument_id, price, quote_time, volume, currency, fetched_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [
                (1, 128.81, "2026-09-30T15:30:00+00:00", 1000, "EUR", "2026-09-30T16:00:00+00:00"),
                (2, 294.10, "2026-09-30T15:30:00+00:00", 500, "EUR", "2026-09-30T16:00:00+00:00"),
            ],
        )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Aufruf: make_legacy_database.py <ziel.db>")
    main(Path(sys.argv[1]))
