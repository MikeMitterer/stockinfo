# T-07 · Environment-Tab: Herkunft der Config anzeigen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| root (backend + frontend) | backlog | ~1 h | UI (+ evtl. /env-Feld) | — |

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
|---|---|---|:--:|---|
| 1 | `#/environment` | Kurzer Hinweis, dass Werte aus `.env` / Docker-Env stammen (per `pydantic-settings`) | ➖ | |
| 2 | `#/environment` | Verweis auf `.env.example` als Vorlage (Doku der Keys) | ➖ | |

---

## Details

### Kontext / Ziel
`Settings` (pydantic) liest ENV-Variablen bzw. `.env`. Für Nutzer ist im Tab
nicht sichtbar, dass genau diese Quelle greift und wo man sie ändert. Ein
kurzer erklärender Hinweis (i18n, DE+EN) genügt vermutlich; optional ein
Backend-Feld, das den aktiven Config-Ursprung nennt.

### Akzeptanzkriterien
- [ ] Environment-Tab erklärt Herkunft der Werte (`.env` / Docker-Env)
- [ ] i18n DE + EN
- [ ] Keine Secrets im UI (nur Herkunft, nicht Werte wie API-Keys)

### Side-Effects
Rein informativ. Falls ein `/env`-Feld ergänzt wird: additiv, rückwärtskompatibel.

### Auflösung
_(offen)_
