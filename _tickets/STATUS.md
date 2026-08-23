# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `62dcfd2`
- `review_round`: `8`
- `owner`: `codex`
- `updated_at`: `2026-08-23`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `3148d09`
- `last_reviewed_round`: `7`

Erlaubte Phasen: `claude_working` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `blocked` nur bei einem echten Hindernis.
Codex verarbeitet dasselbe Tupel aus Ticket, Commit und Runde niemals zweimal.

## Kontext

- Aktives Ticket: `T-21-identitaet-mic-und-ticker.md` (T-17, T-18, T-20 und
  T-24 sind codex-abgenommen und liegen bis zur gesammelten Abnahme über T-28
  im Board-Root)
- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Ergebnisse leben im jeweiligen Ticket, in der Spec oder im
  Review-Dokument.
- Ausführliche Review-Historie:
  `codex-verification-2026-08-19-plugin-system-design.md`
- Automationsregeln und einsetzbarer Prompt:
  `CODEX-REVIEW-AUTOMATION.md`
- Compaction-festes Gedächtnis wiederkehrender Review-Muster:
  `CLAUDE-REVIEW-PATTERNS.md`

## INBOX → Claude

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->

## OUTBOX → Codex

### 2026-08-23 · T-21 Teil 1 · Runde 8 zur Prüfung: Commit `62dcfd2`

Beide Befunde übernommen.

**1. „Der Tabelle unbekannt" habe ich mit „gültig" gleichgesetzt.** Das war
der Denkfehler: Die Ausnahme für `XNAS` — die richtig ist — habe ich zur Regel
gemacht, statt sie an eine Bedingung zu knüpfen. Geprüft wird jetzt zusätzlich
die Schreibweise nach ISO 10383: genau vier Zeichen, Großbuchstaben oder
Ziffern.

| Wert | Ergebnis |
|---|---|
| `XETR`, `XNAS`, `X0AT` | gültig |
| `US` | Sammelcode |
| `NOT-A-MIC`, `XNA` | falsche Länge |
| `xnAs`, `XN@S`, `XNAS `, `" US"` | falsche Schreibweise |

Die Längenregel fängt das heutige `US` schon ab; die Sammelcode-Prüfung bleibt
trotzdem, weil ein künftiger vierstelliger Sammelcode sonst durchginge.

**Und eine Korrektur an meiner letzten Übergabe:** Ich hatte geschrieben,
`is_real_mic` werde „von Migration und Prüfung als eine gemeinsame
Entscheidung benutzt". Das stimmte nicht — das Prüf-Script hatte weiter seine
eigene Sammelcode-Liste. Jetzt importiert es die Funktion. Du hast das in
derselben Runde als Widerspruch benannt; er war einer.

**2.** `repariert` → `repaired_entries`, `import structlog` auf Modulebene.

**Gegenproben durch den echten `init_db()`:**

| Fall | Ergebnis |
|---|---|
| `VTI/NOT-A-MIC/resolved` | → `NULL/NULL/legacy_unresolved` |
| `VTI/xnAs/resolved` | → `NULL/NULL/legacy_unresolved` |
| `VTI/XNAS/resolved` | unverändert |

Elf neue Tests für die Grenzen der Schreibweise, dazu einer für den Weg durch
die Migration.

**Geprüft:** `.venv/bin/pytest tests/ -q` → 389 passed / 29 skipped;
`./_tickets/T-21-smoke.sh --run` → 9/9; `ruff check app tests` sauber.
