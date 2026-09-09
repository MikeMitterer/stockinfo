# T-07 · Environment-Tab: Herkunft der Config anzeigen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | done | erledigt (vom Nutzer abgenommen) | UI (nur Frontend, kein Backend) | — |

**Löst:** Nutzer-Finding — im Environment-Tab soll erkennbar sein, **woher** die
Werte kommen (`.env`-Datei bzw. Docker-Environment). Aktuell zeigt der Tab nur
die effektiven Werte, nicht deren Quelle.

<!--
  Repo:   frontend (EnvironmentPanel.vue) + evtl. backend (/env, EnvInfo)
  Scope:  UI-Hinweis; optional ein Quelle-Feld im /env-Response.
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|-------|
| 1 | `#/environment` | Kurzer Hinweis, dass Werte aus `.env` / Docker-Env stammen | ✅¹ | ok    |
| 2 | `#/environment` | `.env.example` als **Link** ins GH-Repo (neuer Tab) | ✅² | ok    |
| 3 | `#/environment`, Feld „Strikte Börse" | Erklärung, was es bedeutet (nur Default-Börse, sonst 404) | ✅³ | ok    |

> ¹ **(CC):** live (`#/environment`) — Hinweis unter der Werte-Liste: „Diese Werte stammen aus Umgebungsvariablen bzw. der .env-Datei (im Docker-Container: Container-Environment) und werden beim Start gelesen." i18n-Key `env.sourceNote` (DE+EN). Bewusst statisch (Herkunft für alle Werte gleich) — kein Backend-Feld.
> ² **(CC):** `.env.example` als Link → `https://github.com/MikeMitterer/stockinfo/blob/master/.env.example`, `target="_blank"`, `rel="noopener noreferrer"` (via `<i18n-t>`-Slot). Live geprüft (Attribute + öffnet neuen Tab).
> ³ **(CC):** Feldnotiz unter „Strikte Börse": „Aktiv (ja): Kurse werden nur an der Default-Börse abgefragt — findet die Auflösung dort nichts, gibt es einen Fehler (404) statt Ausweichen auf eine andere Börse." i18n-Key `env.strictExchangeHint` (DE+EN). Suite 83/83, Build grün.

---

## Details

### Kontext / Ziel
`Settings` (pydantic) liest ENV-Variablen bzw. `.env`. Für Nutzer ist im Tab
nicht sichtbar, dass genau diese Quelle greift und wo man sie ändert. Ein
kurzer erklärender Hinweis (i18n, DE+EN) genügt vermutlich; optional ein
Backend-Feld, das den aktiven Config-Ursprung nennt.

### Akzeptanzkriterien
- [x] Environment-Tab erklärt Herkunft der Werte (`.env` / Docker-Env)
- [x] `.env.example` als Link ins GH-Repo (neuer Tab, `rel="noopener"`)
- [x] „Strikte Börse" erklärt (nur Default-Börse, sonst 404)
- [x] i18n DE + EN (`env.sourceNote`, `env.strictExchangeHint`)
- [x] Keine Secrets im UI (nur Herkunft, nicht Werte wie API-Keys)

### Side-Effects
Rein informativ, nur Frontend. Kein Backend-Change (statischer Hinweis + Link).

### Auflösung
`EnvironmentPanel.vue`: Herkunfts-Hinweis unter der Werte-Liste (mit
`.env.example`-Link via `<i18n-t>`-Slot) + Feldnotiz zur „Strikten Börse".
Neue i18n-Keys `env.sourceNote`, `env.strictExchangeHint` (de/en). Test
`EnvironmentPanel.spec.ts` (neu, 2 Fälle). Suite 83/83, Build grün.
Commit `23a4c5e`, vom Nutzer abgenommen (2026-08-14).
