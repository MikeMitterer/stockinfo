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
> **Jetzt läuft Teil 3**, Branch `t-21d-offene-zuordnungen` — und er ist
> deutlich kleiner geworden: offene Zuordnungen nur noch **sichtbar** machen
> (`#2b`, `#3`, `#4`), dazu Stuttgart in die Börsentabelle.
>
> **⚠️ Codex, eine Prüfauflage vorab** *(Wunsch Mike, 2026-08-24)* — die
> Handzuordnung `#2c` **und** die Entwurfsfrage aus Runde 3 nach einem eigenen
> Status sind **gestrichen**. Begründung und Messung stehen im Ticket im Kasten
> „Die Handzuordnung ist gestrichen". Der Umstand soll ausdrücklich
> **eigenständig verifiziert** werden, nicht anhand meiner Zusammenfassung:
> Der Yahoo-Weg trägt suffixlose Symbole über `YAHOO_EXCHANGE_MICS` selbst
> nach (`VTI` → `ARCX`, `AAPL` → `XNAS`, gemessen am echten Bestand), sodass
> von sechs Papieren nur `GOLD.SG` offen bleibt — und dafür fehlt schlicht der
> Börseneintrag `XSTU`/`.SG`. Ist diese Messung falsch, fällt die
> Streichung mit ihr.

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
