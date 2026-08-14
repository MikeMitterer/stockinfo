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

Testszenarien für die letzten Änderungen (Commits `1729bee`…`aee2c84`):

**Offen (Board-Root):**

| Ticket | Thema | Status |
|---|---|---|
| [T-08](T-08-chart-prozent-veraenderung.md) | Kurs-Graph: %-Veränderung (Zeitraum + Hover) | backlog |
| [T-09](T-09-manuelle-etf-werte-nachtragen.md) | Asset-Kennzahlen manuell nachtragen (persistent, DB+API+UI) | backlog |
| [T-10](T-10-fx-betrag-konvertieren.md) | Devisen: konkreten Betrag umrechnen (Betrag × Rate, Frontend) | backlog |

**Erledigt (`solved/`):**

| Ticket | Thema |
|---|---|
| T-01 | Devisen-Tab (FxPanel) + `/fx`-Endpoint — UI-getestet |
| T-02 | Börsen-Panel datengetrieben + `strict_exchange` sichtbar — UI-getestet |
| T-03 | justETF nur europäische UCITS-ISINs — Guard-Test |
| T-04 | **Bug:** Dev-Proxy reichte `/exchanges`,`/fx`,`/analyze` nicht durch — behoben |
| T-06 | Devisen-UX: Dropdown (GBp→GBP), 3 Nachkommastellen, formatiertes Datum — umgesetzt + UI-getestet |
| T-05 | **Bug:** Header/Menü Mobile — Hamburger-Drawer links, Breakpoint 1280px — vom Nutzer abgenommen |
| T-07 | Environment-Tab: Config-Herkunft + .env.example-Link + Strikte-Börse-Hinweis — vom Nutzer abgenommen |

T-04–T-06 sind beim Testen entstanden (Nutzer-Findings).

**Voraussetzung Test:** Stack läuft (`make dev-up`) — Backend `:8000`,
Dashboard `:5173`.
