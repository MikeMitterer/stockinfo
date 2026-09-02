"""Inventar der Verify-Matrizen aller offenen Tickets.

Kein `grep` auf geratene Zeichen: Die Tabellen werden gelesen, die Spalte `AI`
wird ueber die Kopfzeile bestimmt, und nur die Datenzeilen darunter zaehlen.
Legenden- und Fliesstextzeilen fallen damit heraus — genau der Fehler, der
eine Textsuche hier unbrauchbar macht.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

MARKS = ("✅", "◑", "⚠️", "➖")


def split_row(line: str) -> list[str]:
    """Zerlegt eine Markdown-Tabellenzeile in ihre Zellen."""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def marks_of(path: Path) -> tuple[dict[str, int], list[str]]:
    """Zaehlt die Marken der AI-Spalte und sammelt die offenen Zeilen."""
    tally = dict.fromkeys(MARKS, 0)
    open_rows: list[str] = []
    ai_index: int | None = None

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|"):
            ai_index = None
            continue

        cells = split_row(line)
        if "AI" in cells and "Human" in cells:
            ai_index = cells.index("AI")
            continue
        if ai_index is None or ai_index >= len(cells):
            continue
        if set(cells[0]) <= {"-", ":"}:  # Trennzeile
            continue

        cell = cells[ai_index]
        for mark in MARKS:
            if mark in cell:
                tally[mark] += 1
                if mark != "✅":
                    number = cells[0].strip("* ")
                    open_rows.append(f"#{number} {mark}")
                break

    return tally, open_rows


def status_of(path: Path) -> str:
    """Liest die Statusangabe aus Kopftabelle oder Kopfzeilen."""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^\*\*Status:\*\*\s*(.+)$", text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    match = re.search(r"^\| *[A-Z][^|]*\| *([^|]+?) *\|[^|]*\|", text, re.MULTILINE)
    return match.group(1).strip() if match else "?"


def main() -> None:
    tickets = sorted(Path("_tickets").glob("T-*.md"))
    for path in tickets:
        tally, open_rows = marks_of(path)
        total = sum(tally.values())
        if total == 0:
            print(f"{path.name:55} KEINE MATRIX          {status_of(path)[:28]}")
            continue
        done = tally["✅"]
        flag = "DURCH" if done == total else "offen"
        rest = ", ".join(open_rows[:6])
        print(f"{path.name:55} {flag} {done:2}/{total:<2} {status_of(path)[:20]:22}{rest}")


if __name__ == "__main__":
    sys.exit(main())
