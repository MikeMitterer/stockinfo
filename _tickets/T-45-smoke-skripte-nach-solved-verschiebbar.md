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

### Auflösung

_(offen)_
