# T-11d · Themes-Namen/Kontrast abgleichen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | backlog | ~3 h | UI-only | — |

**Löst:** Paletten aus `ux-standards/references/themes.md` übernehmen — gleiche
Theme-**Namen** ⇒ gleiche Farbe über Apps; Status/Kategorie themeunabhängig;
Kontrast (ΔE) prüfen. Konkret: StockInfos `classic` (pflaume/korall) → `mangolila`
umbenennen; `classic` wird für neutralgrau frei; helle `paper`-Palette ergänzen.
Teil-Ticket von **T-11** (Punkt 5).

**Stand Skill 2026-08-15:** jetzt **elf** Themes (neu: `slate`, `aurora`,
`carbon`, `sepia`, `meadow`) mit vollständigen RGB-Werten in `themes.md`.
Dazu **Leisten-Token** (`--surface-header`, `--surface-statusbar`, `--text-bar`,
`--text-bar-secondary`, `--text-bar-muted`, `--border-bar`) und vier
„Behandlungen" der Leisten (gleiche Ebene · tiefer · heller · Farbschleier ·
umgekehrt) — jede mindestens einmal vertreten. `carbon` bringt eigene,
kräftigere Status-/Kategorie-Stufen mit.

<!-- Repo: frontend (dashboard/). Status: backlog. Scope: UI-only. -->

---

## Verify

Legende: ✅ live · ⚠️ Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Theme-Auswahl | `mangolila` ist das pflaume/korall-Theme (früher `classic`); `classic` neutralgrau | ➖ | |
| 2 | Theme-Auswahl | helle Palette `paper` vorhanden; `prefers-color-scheme: light` → `paper` | ➖ | |
| 3 | Status/Kategorie-Farben | über alle Themes gleich; Kontrast geprüft (ΔE-Regeln) | ➖ | |
| 4 | Theme-Auswahl | alle **elf** Themes vorhanden, Werte 1:1 aus `themes.md` | ➖ | |
| 5 | `slate`, `carbon`, `aurora`, `sepia` | Kopf-/Statuszeile nutzen **Leisten-Token** — Behandlung sichtbar (tiefer / heller / Farbschleier / umgekehrt) | ➖ | |
| 6 | `sepia` (heller Inhalt, dunkle Leisten) | Wortmarke + Leisten-Text lesbar (eigene `--text-bar*`-Farben greifen) | ➖ | |

---

## Details

### Kontext / Ziel
Gap-Analyse-Punkt 5 aus **T-11**. Zuordnung wichtiger als Ersetzen — Theme unter
falschem Namen wird umbenannt, nicht überschrieben.

### Akzeptanzkriterien
- [ ] `mangolila`/`classic` korrekt zugeordnet
- [ ] helle Palette `paper` ergänzt, System-Preference folgt
- [ ] Kontrast geprüft, nicht geschätzt
- [ ] alle elf Paletten übernommen (Werte unverändert aus `themes.md`)
- [ ] Leisten-Token gesetzt; mindestens je eine Behandlung sichtbar vertreten
- [ ] Theme-Vorschau zeigt vier Farbflecken aus **fest notierten** Werten
      (Token nicht aktiver Themes stehen im Dokument nicht zur Verfügung)

### Side-Effects
Kein Backend-Change. Theme-Namen folgen MakeLib-Konvention (`MAKE_THEME`).

### Auflösung
_(offen)_
