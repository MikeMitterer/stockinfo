# T-11d · Themes-Namen/Kontrast abgleichen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | backlog | ~3 h | UI-only | — |

**Löst:** Paletten aus `ux-standards/references/themes.md` übernehmen — gleiche
Theme-**Namen** ⇒ gleiche Farbe über Apps; Status/Kategorie themeunabhängig;
Kontrast (ΔE) prüfen. Konkret: StockInfos `classic` (pflaume/korall) → `mangolila`
umbenennen; `classic` wird für neutralgrau frei; helle `paper`-Palette ergänzen.
Teil-Ticket von **T-11** (Punkt 5).

<!-- Repo: frontend (dashboard/). Status: backlog. Scope: UI-only. -->

---

## Verify

Legende: ✅ live · ⚠️ Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Theme-Auswahl | `mangolila` ist das pflaume/korall-Theme (früher `classic`); `classic` neutralgrau | ➖ | |
| 2 | Theme-Auswahl | helle Palette `paper` vorhanden; `prefers-color-scheme: light` → `paper` | ➖ | |
| 3 | Status/Kategorie-Farben | über alle Themes gleich; Kontrast geprüft (ΔE-Regeln) | ➖ | |

---

## Details

### Kontext / Ziel
Gap-Analyse-Punkt 5 aus **T-11**. Zuordnung wichtiger als Ersetzen — Theme unter
falschem Namen wird umbenannt, nicht überschrieben.

### Akzeptanzkriterien
- [ ] `mangolila`/`classic` korrekt zugeordnet
- [ ] helle Palette `paper` ergänzt, System-Preference folgt
- [ ] Kontrast geprüft, nicht geschätzt

### Side-Effects
Kein Backend-Change. Theme-Namen folgen MakeLib-Konvention (`MAKE_THEME`).

### Auflösung
_(offen)_
