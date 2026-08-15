# T-11e · Statuszeile + Toast-Meldungen + „?"-Hinweise

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | backlog | ~4 h | UI-only | — |

**Löst:** Rest der `ux-standards`-Angleichung: Statuszeile (links App-Name +
aktiver Kontext + Daten-Alter, rechts Version + anklickbarer Service-Status-Punkt
→ Statusseite); Zustände als **Toast** statt Inline-`ErrorBanner`; „?"-Hinweise
mit bis zu zwei Verweisen (Vertiefung / „Zur Einstellung →"). Teil-Ticket von
**T-11** (Rest). Zuletzt — höchstes Risiko.

<!-- Repo: frontend (dashboard/). Status: backlog. Scope: UI-only. -->

---

## Verify

Legende: ✅ live · ⚠️ Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Statuszeile | links App-Name + Daten-Alter; rechts Version + farbiger Status-Punkt (anklickbar → Statusseite) | ➖ | |
| 2 | Fehlerfall | Meldung als **Toast** (schiebt Layout nicht); Fehler bleibt bis Klick, verschwindet bei Ursache-Wegfall | ➖ | |
| 3 | Fachbegriff (z.B. `strict_exchange`) | „?"-Hinweis mit Verweis(en), „Zur Einstellung →" springt auf den Reiter | ➖ | |

---

## Details

### Kontext / Ziel
Restliche kleinere Punkte aus **T-11**. Verweis „Zur Einstellung →" nutzt die in
T-11a gebauten adressierbaren Reiter (`#/settings?tab=…`).

### Akzeptanzkriterien
- [ ] Statuszeile nach Skill (links Herkunft/Alter, rechts Version + Status-Punkt)
- [ ] Toast-Meldungen ersetzen Inline-Banner nach Skill-Regeln
- [ ] „?"-Hinweise mit Verweisen auf die Settings-Reiter

### Side-Effects
Kein Backend-Change (Statusseite ggf. eigener Verweis).

### Auflösung
_(offen)_
