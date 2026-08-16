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
| [T-12](T-12-ux-foundation-naive-ui.md) | **Auf `ux-foundation` + Naive UI umstellen** — löst T-11d/e/f/g/h ab | in-progress |

**Erledigt (`solved/`):** T-01…T-08, T-10 (Devisen, Börsen, Charts, Bugfixes)
und die gesamte T-11-Reihe.

Zu T-11: Der Branch-Stapel `t-11a → t-11b → t-11c → t-11i → t-11d` wurde am
16.08.2026 per Fast-Forward nach `master` geführt (147 Tests grün, `vue-tsc`
sauber); die ausstehenden Human-Abnahmen entfielen auf Entscheid des
Auftraggebers. T-11d/e/f/g/h wurden **nicht einzeln** umgesetzt — sie wollten
nachbauen, was `@mikemitterer/ux-foundation` seit dem 16.08.2026 mitbringt, und
gehen in T-12 auf.

**Voraussetzung Test:** Stack läuft (`make dev-up`) — Backend `:8000`,
Dashboard `:5173`.
