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
| [T-09](T-09-manuelle-etf-werte-nachtragen.md) | Asset-Kennzahlen manuell nachtragen (persistent, DB+API+UI) | backlog |
| [T-13](T-13-toasts-und-dialoge.md) | Toasts statt Banner, Dialoge auf `NModal` — der Rest aus T-12 | ready |

**Erledigt (`solved/`):** T-01…T-08, T-10, die gesamte T-11-Reihe und T-12.

Zur T-11-Reihe: Der Branch-Stapel wurde am 16.08.2026 per Fast-Forward nach
`master` geführt. T-11d/e/f/g/h wurden nicht einzeln umgesetzt — sie wollten
nachbauen, was `@mikemitterer/ux-foundation` mitbringt, und gingen in T-12 auf.

Zu T-12: Die App bezieht Token, Themes, Schriften, Reset, Symbole, Leisten und
die wiederkehrenden Composables aus dem Fundament; Bedienelemente kommen von
Naive UI. Die vier eigenen Paletten (`earth`, `night`, `sunset`, `neon`) sind
entfallen. Eigen bleibt die **Marke** — Koralle nach Pflaume.

**Voraussetzung Test:** Stack läuft (`make dev-up`) — Backend `:8000`,
Dashboard `:5173`.
