# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-24-rest-core-vertrag.md`
- `handoff_commit`: `403020b`
- `review_round`: `1`
- `owner`: `codex`
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

### 2026-08-21 · T-24 Teil 1 zur Prüfung: Commit `403020b`

**Ich habe das Ticket in zwei Übergaben geschnitten** — an derselben Kante, die
T-24 von T-25 trennt: Definition jetzt, Laufzeit danach. Ein Commit über beides
wäre für einen Diff-Review zu groß. Die Aufteilung steht im Ticketkopf.

Teil 1 deckt `#1`–`#6` und `#7d`–`#7i`. Offen und ausdrücklich **nicht** in
diesem Diff: `GET /fields` (`#7b`, `#7c`), der OpenAPI-Schnappschuss (`#7`) und
die Währungskorrektur im Code (`#8`–`#10`).

**Was entstanden ist:**

- `contract/core-contract.json` — das verbindliche Artefakt. Fünf Modelle
  (`quote`, `instrument`, `daily`, `history`, `fx`) mit `kind`, `required` und
  `meaning` je Feld, dazu `identity`, `errors`, `compatibility`, `generation`
  und ein getrennter `planned`-Block.
- `docs/rest-core-contract.md` — die Erklärung. Wo Text und Artefakt
  auseinandergehen, gilt das Artefakt; das steht im Dokument.
- `contract/fixtures/` — dreizehn HTTP-Umschläge, vier davon absichtlich
  vertragswidrig mit `violates`-Feld.
- `tests/test_contract.py` — prüft beide gegeneinander, **ohne** Import der App.

**Drei Punkte, bei denen ich eine Entscheidung getroffen habe:**

1. **Das Artefakt ist maschinenlesbar, nicht nur Prosa.** `#7i` verlangt
   Konsistenz zwischen Artefakt und Fixtures — gegen ein Markdown-Dokument
   lässt sich das nicht prüfen. Nebeneffekt: `GET /fields` kann in Teil 2
   dieselbe Quelle bedienen, statt die Wahrheit ein zweites Mal zu halten.
2. **`planned` ist getrennt vom Core.** `listing_id`, `(ticker, mic)`, der
   `details`-Container und die Laufzeitseite der Generation sind entschieden,
   aber nicht Teil von `core_version 1.0.0`. Sonst würde das Artefakt Felder
   zusagen, die keine Antwort trägt, und der OpenAPI-Schnappschuss aus Teil 2
   müsste dagegen fallen.
3. **`currency` steht im Artefakt schon als Pflichtfeld**, obwohl der Code sie
   heute noch weglassen kann. Das ist die eine bewusste Verhaltensänderung des
   Tickets (`#8`); sie kommt in Teil 2. Ein fünftes Modell `history` ist
   dazugekommen — `/quote/{isin}/history` ist öffentlich und war in der
   Aufzählung des Tickets nicht genannt.

**Geprüft:** `.venv/bin/pytest tests/ -q` → 291 passed, 16 skipped; Ruff sauber;
alle dreizehn Fixtures und das Artefakt parsen. `tests/test_contract.py` allein:
35 passed, 16 skipped.

**Zu P-01 aus der Mustersammlung:** Dieser Diff enthält keinen Test, der eine
Kette behauptet — `test_contract.py` liest ausschließlich Dateien und
importiert bewusst nichts. Was er **nicht** zeigt, ist, ob die laufende App dem
Artefakt entspricht; das ist T-25 `#7j`, und ich behaupte es nirgends.
