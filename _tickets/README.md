# _tickets — Verify-Board

Datei-basiertes Board für kleine, verifizierbare Arbeitseinheiten mit
**zweistufiger Mensch/KI-Verifikation** (Skill `task-verification-workflow`).

## Layout

```
_tickets/
├── README.md      # dieser Workflow (stabil)
├── STATUS.md      # ephemere Claude↔Codex-Mailbox
├── CODEX-REVIEW-AUTOMATION.md # Zustandsprotokoll + Scheduled-Task-Prompt
├── CLAUDE-REVIEW-PATTERNS.md   # dauerhaftes, compaction-festes Review-Wissen
├── QUESTIONS.md   # ephemerer Capture-Buffer, tendiert gegen leer
├── T-NN-*.md      # offene Tickets (Board-Root)
└── solved/        # erledigte Tickets (git mv bei done)
```

## Regeln

- **Ort = Status.** Ticket im Root = offen. Erledigt → `git mv T-NN-*.md solved/`.
- **Verify-Matrix zweistufig.** Spalte `AI` füllt nur die KI (Live-Vorabcheck,
  Ehrlichkeits-Legende + Fußnoten-Evidenz). Spalte `Human` füllt **nur der
  Mensch** — die KI überschreibt sie **nie**.
- Legende `AI`: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung ·
  ◑ teilweise · ➖ keine Live-Verifikation.
- **Fragen** landen in `QUESTIONS.md` und drainieren → erledigt / GitHub-Issue /
  gelöscht. Nichts wohnt dort.
- **Claude↔Codex-Kommunikation** läuft operativ über `STATUS.md`: aktuelle
  Nachricht in `INBOX → Claude`, Antwort oder Übergabe in `OUTBOX → Codex`.
  Beide Bereiche werden nach Verarbeitung geleert; dauerhafte Erkenntnisse
  wandern ins Ticket, in die Spec oder das Review-Dokument. Keine Historie im
  Status-Hub — dafür existiert Git.
- **Zustandsübergaben sind atomar.** Claude setzt nach dem Produkt-Commit
  `ready_for_codex` samt `handoff_commit` und stoppt Produktänderungen. Codex
  setzt während der Prüfung `codex_reviewing` und danach `approved` oder
  `changes_requested`. Identität eines Durchlaufs ist
  `(ticket, handoff_commit, review_round)`; dasselbe Tupel wird nie zweimal
  geprüft. Der vollständige Vertrag und der Scheduled-Task-Prompt stehen in
  `.agents/AGENT-WORKFLOW.md`.
- **Der Reviewer-Task hängt am bestehenden Codex-Review-Chat.** Kein
  Standalone-Task: Der bestehende Chat liefert die fortlaufende fachliche
  Lernkurve, das Musterregister sichert sie zusätzlich gegen Compaction und
  Sitzungswechsel ab.
- **Wiederkehrende Claude-Muster überleben Chat-Compaction.** Sie werden nur
  in `.agents/CLAUDE-LESSONS.md` dauerhaft gepflegt. Jeder Review liest diese
  Datei zuerst und ergänzt ausschließlich belegte, verallgemeinerbare Muster;
  Einzelfindings bleiben im Ticket beziehungsweise Review-Ergebnis.

## Scope-Vertrag für Implementierungstickets

Vor dem ersten Produktedit enthält jedes Implementierungsticket diesen Block:

```markdown
## Scope-Vertrag

- **Ergebnis:** Ein Satz mit dem beobachtbaren Ergebnis.
- **Fachliche Änderungen:** Höchstens drei einzeln benannte Regeln.
- **Produktflächen/-dateien:** Erwartetes Inventar vor dem ersten Edit.
- **Tests/Dokumentation:** Erwartete mechanische Anpassungen.
- **Nicht-Ziele:** Ausdrücklich ausgeschlossene Arbeiten.
- **Budget:** Geschätzte Produktdateien, Test-/Dokudateien und Diff-Zeilen.
```

Für bestehende offene Tickets ergänzt Claude den Block unmittelbar vor dem
nächsten Produktedit. Historische Tickets unter `solved/` werden nicht
umgeschrieben. Die Auslöser und der kurze `scope_checkpoint` stehen im
verbindlichen Vertrag `.agents/AGENT-WORKFLOW.md`.

Jede normale Übergabe enthält zusätzlich diese Soll/Ist-Tabelle:

| Wert | geplant | tatsächlich |
|---|---:|---:|
| fachliche Änderungen | | |
| Produktdateien | | |
| Test-/Dokumentationsdateien | | |
| Diff-Zeilen | | |

Jede Abweichung erhält einen Satz Begründung. Test- und Dokumentationsdateien
stehen getrennt von Produktdateien, damit mechanische Fixture-Anpassungen
sichtbar bleiben, ohne als neue Produktarchitektur zu gelten.

## Stand dieser Runde

**Offen (Board-Root):**

| Ticket | Thema | Status |
|---|---|---|
| [T-09](40-done/T-09-manuelle-etf-werte-nachtragen.md) | Asset-Kennzahlen manuell nachtragen (persistent, DB+API+UI) | in-review |
| [T-13](40-done/T-13-toasts-und-dialoge.md) | Toasts statt Banner, Dialoge auf `NModal` — der Rest aus T-12 | in-review |
| [T-14](80-iced/T-14-kontrast-umgekehrte-leisten.md) | Kontrast auf umgekehrten Leisten — und ein Prüfskript, das ihn sieht | ready |

`in-review` heißt: umgesetzt, die `AI`-Spalte der Verify-Matrix ist gefüllt, die
`Human`-Spalte noch nicht. **Nach `solved/` wandert ein Ticket erst auf Ansage** —
die KI verschiebt es nie von sich aus.

**Erledigt (`solved/`):** T-01…T-08, T-10, T-11-Reihe und T-12.

Zur T-11-Reihe: Der Branch-Stapel wurde am 16.08.2026 per Fast-Forward nach
`master` geführt. T-11d/e/f/g/h wurden nicht einzeln umgesetzt — sie wollten
nachbauen, was `@mikemitterer/ux-foundation` mitbringt, und gingen in T-12 auf.

Zu T-12: Die App bezieht Token, Themes, Schriften, Reset, Symbole, Leisten und
die wiederkehrenden Composables aus dem Fundament; Bedienelemente kommen von
Naive UI. Die vier eigenen Paletten (`earth`, `night`, `sunset`, `neon`) sind
entfallen. Eigen bleibt die **Marke** — Koralle nach Pflaume.

Zu T-13: Meldungen sind Toasts, die Dialoge sitzen auf `NModal`, und die
„?"-Hinweise kommen als `UxInfoHint` aus dem Fundament. „Alle aktualisieren"
ist dabei in die Kopfzeile gezogen — im oberen rechten Eck des Inhalts
verdeckte die Meldung sonst den Knopf, mit dem man ihre Ursache behebt.
Verify #7 (Kontrast in `sepia`) reißt und lebt als **T-14** weiter.

Zu T-09: Fehlende Kennzahlen (TER, Vola, Thesaurierend) lassen sich an Ort und
Stelle nachtragen und liegen in einer **eigenen** Tabelle — der Kurs-Refresh
schreibt die Instrumentenzeile neu und hätte sie sonst mitgenommen. Vorrang hat
die Quelle; verdeckt sie eine Eingabe, sagt die Oberfläche das und nennt den
eigenen Wert.

**Voraussetzung Test:** Stack läuft (`make dev-up`) — Backend `:8000`,
Dashboard `:5173`.
