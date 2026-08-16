# T-11d · Themes-Namen/Kontrast abgleichen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | backlog | ~3 h | UI-only | — |

**Löst:** Paletten aus `ux-standards/references/themes.md` übernehmen — gleiche
Theme-**Namen** ⇒ gleiche Farbe über Apps; Status/Kategorie themeunabhängig;
Kontrast (ΔE) prüfen. Konkret: StockInfos `classic` (pflaume/korall) → `mangolila`
umbenennen; `classic` wird für neutralgrau frei; helle `paper`-Palette ergänzen.
Teil-Ticket von **T-11** (Punkt 5).

**Stand Skill 2026-08-16:** jetzt **dreizehn** Themes (neu gegenüber StockInfo:
`mangolila`, `amber`, `petrol`, `slate`, `aurora`, `carbon`, `paper`, `sepia`,
`meadow`) mit vollständigen RGB-Werten in `themes.md`.
Dazu **Leisten-Token** (`--surface-header`, `--surface-statusbar`, `--text-bar`,
`--text-bar-secondary`, `--text-bar-muted`, `--border-bar`) und vier
„Behandlungen" der Leisten (gleiche Ebene · tiefer · heller · Farbschleier ·
umgekehrt) — jede mindestens einmal vertreten. `carbon` bringt eigene,
kräftigere Status-/Kategorie-Stufen mit.

**Marke (Skill-Nachtrag, gleicher Tag):** Der Verlauf ist **themeunabhängig**
und je App eigen — für StockInfo **Koralle → Pflaume, `#df5430` → `#812c7c`,
135°**. Das sind exakt die heute toten `$brand-orange`/`$brand-purple` in
`_variables.scss`; sie werden damit wieder lebendig. Heute ist `--c-grad`
dagegen **pro Theme verschieden und 120°** — das fällt weg.

**Achtung, zwei verwechselbare Token:**
`--brand-contrast: 255 255 255` (fest, Zeichen auf dem Marken-Verlauf) steht
**neben** `--accent-contrast` (Text auf der *Akzent*fläche, wechselt mit dem
Theme — in sechs der elf Paletten nahezu schwarz). Die Plakette ist keine
Akzentfläche; ein Zeichen darauf, das mit dem Theme umschlägt, verschwindet in
genau diesen sechs. Die vier aus **T-11b** übrig gebliebenen `#fff` müssen
deshalb **einzeln** zugeordnet werden:

| Stelle | richtiges Token | warum |
|---|---|---|
| `base.scss` `button.primary` (auf `$brand-gradient`) | `--brand-contrast` | liegt auf dem Marken-Verlauf |
| `SettingsPanel.vue` aktiver Sprach-Knopf (auf Verlauf) | `--brand-contrast` | dito |
| `RangeSelector.vue` aktiver Zeitraum (auf Verlauf) | `--brand-contrast` | dito |
| `InstrumentsTable.vue` `.ext:hover`, `.icon.danger:hover` (auf `$color-accent` bzw. `$color-danger`) | `--accent-contrast` | echte Akzent-/Statusfläche |

<!-- Repo: frontend (dashboard/). Status: backlog. Scope: UI-only. -->

---

## Verify

Legende: ✅ live · ⚠️ Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Theme-Auswahl | `mangolila` ist das pflaume/korall-Theme (früher `classic`); `classic` neutralgrau | ➖ | |
| 2 | Theme-Auswahl | helle Palette `paper` vorhanden; `prefers-color-scheme: light` → `paper` | ➖ | |
| 3 | Status/Kategorie-Farben | über alle Themes gleich; Kontrast geprüft (ΔE-Regeln) | ➖ | |
| 4 | Theme-Auswahl | alle **dreizehn** Themes vorhanden, Werte 1:1 aus `themes.md` | ➖ | |
| 5 | `slate`, `carbon`, `aurora`, `sepia` | Kopf-/Statuszeile nutzen **Leisten-Token** — Behandlung sichtbar (tiefer / heller / Farbschleier / umgekehrt) | ➖ | |
| 6 | `sepia` (heller Inhalt, dunkle Leisten) | Wortmarke + Leisten-Text lesbar (eigene `--text-bar*`-Farben greifen) | ➖ | |
| 7 | Plakette in der Kopfzeile, **alle** Themes durchschalten | Verlauf bleibt konstant Koralle→Pflaume (135°); das Zeichen darin bleibt weiß und verschwindet in **keinem** Theme | ➖ | |
| 8 | `grep -rn '#fff' dashboard/src` | keine `#fff` mehr — je Stelle korrekt `--brand-contrast` (auf Verlauf) oder `--accent-contrast` (auf Akzent/Status) | ➖ | |

---

## Details

### Kontext / Ziel
Gap-Analyse-Punkt 5 aus **T-11**. Zuordnung wichtiger als Ersetzen — Theme unter
falschem Namen wird umbenannt, nicht überschrieben.

### Akzeptanzkriterien
- [ ] `mangolila`/`classic` korrekt zugeordnet
- [ ] helle Palette `paper` ergänzt, System-Preference folgt
- [ ] Kontrast geprüft, nicht geschätzt
- [ ] alle dreizehn Paletten übernommen (Werte unverändert aus `themes.md`)
- [ ] `theme-tokens.py check --zonen` läuft mit Exit-Code 0 durch
- [ ] Leisten-Token gesetzt; mindestens je eine Behandlung sichtbar vertreten
- [ ] Theme-Vorschau zeigt vier Farbflecken aus **fest notierten** Werten
      (Token nicht aktiver Themes stehen im Dokument nicht zur Verfügung)

### Side-Effects
Kein Backend-Change. Theme-Namen folgen MakeLib-Konvention (`MAKE_THEME`).

### Auflösung
_(offen)_
