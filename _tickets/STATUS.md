# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `claude_working`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `806c1a1`
- `review_round`: `7`
- `owner`: `claude`
- `updated_at`: `2026-08-24`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `806c1a1`
- `last_reviewed_round`: `7`

Erlaubte Phasen: `claude_working` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `blocked` nur bei einem echten Hindernis.
Codex verarbeitet dasselbe Tupel aus Ticket, Commit und Runde niemals zweimal.

## Kontext

> **Teil 2 + 2b sind freigegeben** *(Runde 7, `806c1a1`, Codex,
> 2026-08-24)* — nach sieben Runden ohne offenen Befund. Das Ticket bleibt im
> Board-Root; die Abnahme läuft gesammelt über T-28 und ist Mikes Sache.
>
> **Jetzt läuft Teil 3** — API und Dashboard: offene Zuordnungen sichtbar
> machen und von Hand setzbar, dazu die Vertragsversion. Deckt die Zeilen
> `#2b`, `#2c`, `#3` und `#4` der Verify-Matrix ab; `#2c` steht bis heute auf
> `➖ Teil 3`.
>
> **Die Entwurfsfrage aus Runde 3 gehört dazu:** Eine von Hand gesetzte
> Zuordnung ist heute von einer maschinellen nicht zu unterscheiden — beide
> tragen `resolved`. Damit kann ein späterer Auflösungslauf eine manuelle
> Korrektur überschreiben. Das Ticket hält bereits fest, dass Teil 3 dafür
> einen eigenen Status braucht, den der automatische Weg nicht anfasst; offen
> ist, wie er heißt und wie die Endpunkte ihn führen. Das wird vor dem ersten
> Edit entworfen, nicht im Code entschieden.

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

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->
