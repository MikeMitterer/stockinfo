# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `claude_working`
- `ticket`: `T-20-dreiwertiges-quellen-ergebnis.md`
- `handoff_commit`: `—`
- `review_round`: `1`
- `owner`: `claude`
- `updated_at`: `2026-08-22`
- `last_reviewed_ticket`: `T-18-aufloesung-erreicht-mehr-maerkte.md`
- `last_reviewed_commit`: `69e18c1`
- `last_reviewed_round`: `2`

Erlaubte Phasen: `claude_working` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `blocked` nur bei einem echten Hindernis.
Codex verarbeitet dasselbe Tupel aus Ticket, Commit und Runde niemals zweimal.

## Kontext

- Aktives Ticket: `T-20-dreiwertiges-quellen-ergebnis.md` (T-17, T-18 und T-24
  sind codex-abgenommen und liegen bis zur gesammelten Abnahme über T-28 im
  Board-Root)
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

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->
