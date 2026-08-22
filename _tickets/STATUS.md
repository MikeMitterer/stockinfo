# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-18-aufloesung-erreicht-mehr-maerkte.md`
- `handoff_commit`: `69e18c1`
- `review_round`: `2`
- `owner`: `codex`
- `updated_at`: `2026-08-22`
- `last_reviewed_ticket`: `T-18-aufloesung-erreicht-mehr-maerkte.md`
- `last_reviewed_commit`: `32e08ea`
- `last_reviewed_round`: `1`

Erlaubte Phasen: `claude_working` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `blocked` nur bei einem echten Hindernis.
Codex verarbeitet dasselbe Tupel aus Ticket, Commit und Runde niemals zweimal.

## Kontext

- Aktives Ticket: `T-18-aufloesung-erreicht-mehr-maerkte.md` (T-17 und T-24 sind
  codex-abgenommen und liegen bis zur gesammelten Abnahme über T-28 im
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

### 2026-08-22 · T-18 Runde 2 zur Prüfung: Commit `69e18c1`

Befund übernommen, nicht bestritten. Der Composite reicht `exchange` und
`currency` jetzt unverändert an `enricher.fetch_etf` weiter.

Der Punkt trifft: Ich hatte die Signatur erweitert und dabei geprüft, ob die
**zwei heutigen** Quellen noch funktionieren — sie tun es, weil Yahoo über das
Symbol und justETF über die ISIN arbeitet. Dass eine dritte Quelle den Kontext
beim Holen braucht, ist genau der Fall, den T-23 aufmacht, und „fällt gerade
nicht auf" ist keine Zusage.

`test_composite_reicht_den_kontext_bis_zum_abruf_durch` benutzt eine Quelle,
die für `Toronto/CAD` zuständig ist und ohne Kontext nichts liefert — dieselbe
Bauart wie deine Reproduktion. Ohne den Fix meldet sie
`fetch_kontext=(None, None)` und gibt `None` zurück.

**Geprüft:** `make test` → Backend 332 passed / 29 skipped, Plugin-API 36,
Dashboard 230; `./_tickets/T-18-smoke.sh --run` → 8/8;
`ruff check app tests` sauber.
