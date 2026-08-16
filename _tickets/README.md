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
| [T-09](T-09-manuelle-etf-werte-nachtragen.md) | Asset-Kennzahlen manuell nachtragen (persistent, DB+API+UI) | backlog |
| [T-11](T-11-ux-standards-angleichen.md) | **Epic:** App an ux-standards angleichen (Nav, Settings, Token, Mobil-Tabellen, Themes) | in Arbeit |
| [T-11a](T-11a-navigation-einstellungsseite.md) | Navigation entrümpeln + Einstellungsseite | **Code fertig + reviewt + browsergeprüft** → Abnahme |
| [T-11b](T-11b-token-aliase-hardcoded-farben.md) | Token-Aliase + hartkodierte Farben | **Code fertig + reviewt + gemessen** → Abnahme |
| [T-11c](T-11c-assets-tabelle-mobil-karten.md) | Assets-Tabelle mobil → Kartenliste | **Code fertig + browsergeprüft (11/12)** → Abnahme |
| [T-11i](T-11i-loeschen-bestaetigen.md) | **Bug-Schutz:** Löschen bestätigen (Dialog) | **Code fertig + browsergeprüft (8/9)** → Abnahme |
| [T-11d](T-11d-themes-namen-kontrast.md) | Themes: 13 Paletten, Leisten-Token, feste Marke | ⏸ **ruht** — wartet auf gemeinsame UX-Foundation |
| [T-11e](T-11e-statuszeile-toasts-hinweise.md) | Statuszeile + Toast-Meldungen + „?"-Hinweise | backlog |
| [T-11f](T-11f-schriften-inter-space-grotesk.md) | Schriften: Inter + Space Grotesk gebündelt | backlog |
| [T-11g](T-11g-symbole-statt-hamburger.md) | Symbole statt Hamburger, Einstellungen nach links | ready |
| [T-11h](T-11h-zeichen-wortmarke-favicon.md) | Zeichen, Wortmarke und FavIcon trennen | ready |

### Branch-Stapel (nichts nach `master` gemerged)

```
master
 └─ t-11a-nav-settings        317ccb5   T-11a
     └─ t-11b-token-aliase    d476275   + T-11b (inkl. Chart-Regression behoben)
         └─ t-11c-mobile-karten      140b0ed   + T-11c
             └─ t-11i-loeschen-bestaetigen  3fea8dd   + T-11i
                 └─ t-11d-themes            a511983   nur Plan/Ticket, kein Code
```

**Offener Stash:** `stash@{0}` auf `t-11d-themes` — Rohfassung der 13 Paletten in
`base.scss`, **ungeprüft** (Kontrastlauf kam nicht mehr dran). Bringt die
UX-Foundation die Paletten mit → `git stash drop`. Sonst → `git stash pop` und
mit `theme-tokens.py check --zonen` prüfen.

**Vor der Abnahme wissen:**
- T-11g dreht Teile von T-05 (Hamburger) und T-11a (Einstellungen rechts)
  bewusst zurück — die ✅ in T-11a Zeile 2/8 meinen den damaligen Soll-Zustand.
- T-11c Zeile 8 (ISIN mobil) ist ➖: es gibt kein Testpapier ohne ISIN.
- T-11i Zeile 4 (echtes Löschen) ist ➖: bewusst nicht ausgelöst, hätte Daten
  samt Historie vernichtet.

**Erledigt (`solved/`):**

| Ticket | Thema |
|---|---|
| T-01 | Devisen-Tab (FxPanel) + `/fx`-Endpoint — UI-getestet |
| T-02 | Börsen-Panel datengetrieben + `strict_exchange` sichtbar — UI-getestet |
| T-03 | justETF nur europäische UCITS-ISINs — Guard-Test |
| T-04 | **Bug:** Dev-Proxy reichte `/exchanges`,`/fx`,`/analyze` nicht durch — behoben |
| T-05 | **Bug:** Header/Menü Mobile — Hamburger-Drawer links, Breakpoint 1280px — vom Nutzer abgenommen |
| T-06 | Devisen-UX: Dropdown (GBp→GBP), 3 Nachkommastellen, formatiertes Datum — UI-getestet |
| T-07 | Environment-Tab: Config-Herkunft + .env.example-Link + Strikte-Börse-Hinweis — abgenommen |
| T-08 | Kurs-Graph: %-Veränderung (rechte Achse, Badge, Tooltip) — abgenommen |
| T-10 | Devisen: konkreten Betrag umrechnen (Betrag × Rate) — abgenommen |

T-04–T-10 sind großteils beim Testen entstanden (Nutzer-Findings).

**Voraussetzung Test:** Stack läuft (`make dev-up`) — Backend `:8000`,
Dashboard `:5173`.
