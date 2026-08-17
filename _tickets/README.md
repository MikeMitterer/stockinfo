# _tickets — Verify-Board

Datei-basiertes Board für kleine, verifizierbare Arbeitseinheiten mit
**zweistufiger Mensch/KI-Verifikation** (Skill `task-verification-workflow`).

## Layout

```
_tickets/
├── README.md      # dieser Workflow (stabil)
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

## Stand dieser Runde

**Offen (Board-Root):**

| Ticket | Thema | Status |
|---|---|---|
| [T-09](T-09-manuelle-etf-werte-nachtragen.md) | Asset-Kennzahlen manuell nachtragen (persistent, DB+API+UI) | in-review |
| [T-13](T-13-toasts-und-dialoge.md) | Toasts statt Banner, Dialoge auf `NModal` — der Rest aus T-12 | in-review |
| [T-14](T-14-kontrast-umgekehrte-leisten.md) | Kontrast auf umgekehrten Leisten — und ein Prüfskript, das ihn sieht | ready |

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
