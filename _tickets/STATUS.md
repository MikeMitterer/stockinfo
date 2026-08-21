# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `claude_working`
- `ticket`: `T-24-rest-core-vertrag.md`
- `handoff_commit`: `—`
- `review_round`: `1`
- `owner`: `claude`
- `updated_at`: `2026-08-21`
- `last_reviewed_ticket`: `T-17-still-falsche-antworten.md`
- `last_reviewed_commit`: `1a2f2bd`
- `last_reviewed_round`: `2`

Erlaubte Phasen: `claude_working` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `blocked` nur bei einem echten Hindernis.
Codex verarbeitet dasselbe Tupel aus Ticket, Commit und Runde niemals zweimal.

## Kontext

- Aktives Ticket: `T-24-rest-core-vertrag.md` (T-17 ist codex-abgenommen und
  liegt bis zur gesammelten Abnahme über T-28 im Board-Root)
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

<!-- Leer. Claude trägt hier nur die nächste unverarbeitete Übergabe ein. -->
