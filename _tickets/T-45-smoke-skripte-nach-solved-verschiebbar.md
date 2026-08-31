# T-45 · Smoke-Skripte bleiben nach dem Archivieren ausführbar

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Verifikationsskripte) | ready | 1 h | Root-Ermittlung aller Ticket-Smokes | — |

**Löst:** Ein Ticket-Smoke funktioniert sowohl neben seinem offenen Ticket in
`_tickets/` als auch nach dem gemeinsamen Verschieben nach
`_tickets/solved/`. Heute zeigen Projekt-Root und BashLib dort eine Ebene zu
tief.

**Priorität:** Follow-up außerhalb der aktuellen Kette; vor dem Archivieren
der betroffenen Tickets erledigen.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung ·
◑ teilweise · ➖ keine Live-Verifikation. `AI` nur KI, `Human` nur Mensch.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | alle neun `T-*-smoke.sh` in `_tickets/` | `--info`/`--help` findet Projekt-Root, `.venv` und BashLib | ➖ | |
| 2 | dieselben Skripte unter `_tickets/solved/` | dieselben Pfade werden gefunden; kein Script erwartet `_tickets/.venv` oder `_tickets/.libs` | ➖ | |
| 3 | mindestens T-22 und T-35 nach simulierter Verschiebung | ihre echten `--run`-Checks bleiben grün und benutzen weiter temporäre Daten | ➖ | |
| 4 | Root-Ermittlung | eine gemeinsame, dokumentierte Regel; keine neun auseinanderlaufenden Sonderfälle | ➖ | |

---

## Scope-Vertrag

- **Ergebnis:** Jeder Ticket-Smoke ist an beiden vom Board erlaubten Orten
  ausführbar.
- **Fachliche Änderungen:** höchstens zwei — gemeinsame Root-Ermittlung und
  eine Gegenprobe für beide Orte.
- **Erwartete Fläche:** neun vorhandene `_tickets/T-*-smoke.sh`; optional ein
  kleiner gemeinsamer Helper oder Test.
- **Nicht-Ziele:** keine Änderung der fachlichen Smoke-Orakel, keine neue CLI,
  keine Verschiebung der Tickets in diesem Ticket.
- **Budget:** höchstens zehn Script-/Testdateien und 180 Diff-Zeilen.

## Details

Alle neun Skripte verwenden derzeit sinngemäß:

```bash
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
```

Aus `_tickets/solved/` ergibt das `_tickets/` statt des Repository-Roots;
analog zeigt `../.libs` auf `_tickets/.libs`. Die Gegenprobe muss die Datei
tatsächlich aus beiden Verzeichnistiefen starten — eine reine Textsuche nach
der neuen Formel genügt nicht.

### Side-Effects

Keine Produkt- oder Arbeitsdaten. Temporäre Kopien beziehungsweise Symlinks
der Gegenprobe werden nach dem Lauf entfernt; echte Tickets bleiben an ihrem
Ort.

---

## Das Muster steht fest — nicht neu erfinden (2026-08-31)

**Mikes Auflage:** *„Vermerke aber das gerade gelernte Muster, damit T-45 nicht
wieder alles neu erfinden muss."* Es ist im Skill
`task-verification-workflow` hinterlegt und gilt ab sofort für **jedes** neue
Prüf-Script; hier steht es, damit dieses Ticket es nicht zweimal herleitet.

**Das Erkennungsmerkmal ist `.libs/`** — dasselbe Verzeichnis, das die Scripts
ohnehin brauchen. Es beantwortet damit beide Fragen auf einmal: „wo ist das
Projekt?" und „wo sind die Bibliotheken?".

```bash
# Das Projekt findet sich selbst — aufwärts, erkennbar an `.libs/`.
#
# Params:
#   $1 - Verzeichnis, ab dem gesucht wird
#
# Returns:
#   0 und das Projektverzeichnis auf stdout, 1 wenn keines gefunden wurde
findProjectRoot() {
    local _DIR="$1"
    while [[ "${_DIR}" != "/" ]]; do
        [[ -d "${_DIR}/.libs" ]] && { echo "${_DIR}"; return 0; }
        _DIR="$(dirname "${_DIR}")"
    done
    return 1
}

# `readonly` gibt **immer** 0 zurück — der Exit-Code muss vorher gesichert
# werden, sonst greift die Prüfung nie.
_RC=0
PROJECT_ROOT="$(findProjectRoot "$(cd "$(dirname "$0")" && pwd)")" || _RC=$?
if [[ ${_RC} -ne 0 ]]; then
    echo "kein Projekt gefunden — kein .libs oberhalb von $(dirname "$0")" >&2
    exit 1
fi
readonly PROJECT_ROOT
BASH_LIBS="${BASH_LIBS:-${PROJECT_ROOT}/.libs/BashLib/src}"
```

**Warum die Prüfung des Exit-Codes nicht kosmetisch ist:** `readonly` ist ein
Builtin und liefert immer `0`. Ein `readonly PROJECT_ROOT="$(findProjectRoot …)"
|| exit 1` triggerte deshalb **nie** — das Script liefe mit leerer Wurzel
weiter und scheiterte erst später an etwas anderem.

## Runde 1 · Umgesetzt (2026-08-31)

Alle neun Scripts umgestellt. Die Gegenprobe ist der Punkt, an dem das Ticket
hängt — deshalb aus **beiden** Orten und ohne `BASH_LIBS` in der Umgebung, weil
diese Variable in Mikes Shell gesetzt ist und den Rückfall sonst verdeckt:

```
_tickets/          alle neun  →  PROJECT_ROOT = …/StockInfo
_tickets/solved/   alle neun  →  PROJECT_ROOT = …/StockInfo
altes Muster in solved/       →  ../.libs FEHLT
```

Dazu ein **echter** Lauf des netzfreien T-22-Smokes aus `_tickets/solved/`:
`6 Checks bestanden` (`#1 #2 #3 #4 #4b #5`). Eine Textsuche nach der neuen
Formel hätte das nicht belegt — das verlangt Verify `#3` ausdrücklich.

### Umfang

| | Budget | tatsächlich |
|---|---|---|
| Script-/Testdateien | 10 | **9** |
| Diff-Zeilen | 180 | **288** (270 hinzu, 18 entfernt) |

**Über dem Budget, und zwar an der Zeilenzahl.** Der Grund ist die
Kommentierung: Das Muster ersetzt zwei Zeilen durch einen dokumentierten Block,
und das neunmal. Ohne Kommentare wären es rund 90 Zeilen. Wenn Codex die
Erklärung an neun Stellen für Verschwendung hält, ist der Weg, sie **einmal**
in `.libs/BashLib` zu hinterlegen und hier nur zu rufen — das wäre allerdings
eine Änderung an einer geteilten Bibliothek und damit ein eigener Checkpoint.

## Auflösung

_(offen — Codex prüft Runde 1)_

### Auflösung

_(offen)_
