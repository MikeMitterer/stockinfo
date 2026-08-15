# T-11b · Token-Aliase + hartkodierte Farben ersetzen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | backlog | ~2 h | UI-only | — |

**Löst:** Alias-Zeile auf die `ux-standards`-Token-Namen legen
(`--surface-page/-card/-sunken`, `--edge`, `--ink-*`, `--accent`,
`--status-ok/-near/-out`) → auf bestehende `--c-*`/`$health-*` mappen; keine
Umbenennungswelle. Nebenbei hartkodierte Farben ersetzen (z.B. `#e5484d` in
`.err` von `FxPanel.vue`/`AnalysisPanel.vue`). Teil-Ticket von **T-11** (Punkt 3).

<!-- Repo: frontend (dashboard/). Status: backlog. Scope: UI-only. -->

---

## Verify

Legende: ✅ live · ⚠️ Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `dashboard/src/styles/` | Alias-Zeile mappt Skill-Token auf bestehende `--c-*`/`$health-*` | ➖ | |
| 2 | `grep -rn '#e5484d\|#[0-9a-fA-F]\{3,6\}' dashboard/src/components` | keine hartkodierten Farben mehr in Komponenten (nur Token) | ➖ | |
| 3 | App in mehreren Themes | Farben unverändert (nur Namen dazugelegt, keine Optik-Änderung) | ➖ | |

---

## Details

### Kontext / Ziel
Gap-Analyse-Punkt 3 aus **T-11**. Macht Komponenten zwischen Apps portierbar.

### Akzeptanzkriterien
- [ ] Alias-Zeile vorhanden, alte `--c-*` laufen weiter
- [ ] Keine hartkodierten Farben in Komponenten
- [ ] Optik unverändert (nur Aliase)

### Side-Effects
Kein Backend-Change.

### Auflösung
_(offen)_
