# T-11b · Token-Aliase + hartkodierte Farben ersetzen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | backlog | ~2 h | UI-only | — |

**Löst:** Alias-Zeile auf die `ux-standards`-Token-Namen legen
(`--surface-page/-card/-raised/-sunken`, `--text-primary/-secondary/-muted`,
`--border-default/-subtle`, `--accent`, `--accent-contrast`,
`--status-ok/-near/-out`) → auf bestehende `--c-*`/`$health-*` mappen; keine
Umbenennungswelle. Nebenbei hartkodierte Farben ersetzen (z.B. `#e5484d` in
`.err` von `FxPanel.vue`/`AnalysisPanel.vue`). Teil-Ticket von **T-11** (Punkt 3).

**Stand Skill 2026-08-15:** Farben als **RGB-Tripel ohne Funktion** (`10 10 10`,
nicht `#0a0a0a`), Verwendung als `rgb(var(--name))` — nur so ist Deckkraft
nachrüstbar (`rgb(var(--surface-card) / .7)`). Zusätzlich die **Leisten-Token**
vorsehen (`--surface-header`, `--surface-statusbar`, `--text-bar`,
`--text-bar-secondary`, `--text-bar-muted`, `--border-bar`) — optional mit
Rückfall auf `--surface-page`/`--surface-card`/`--text-primary`; sie sind die
Voraussetzung für T-11d/T-11e. Skalen ebenfalls benannt: `--space-*`,
`--radius-sm/-lg/-full`, Schriftgrößen `--font-*` (**nicht** `--text-*` — das
sind die Textfarben).

<!-- Repo: frontend (dashboard/). Status: backlog. Scope: UI-only. -->

---

## Verify

Legende: ✅ live · ⚠️ Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `dashboard/src/styles/base.scss` | Skill-Token je Theme-Block; `--c-*` als Rückwärts-Alias **im selben Block** | ✅¹ | |
| 2 | `grep -rnE '#[0-9a-fA-F]{3,8}' dashboard/src/components` | keine hartkodierten Farben mehr in Komponenten (nur Token) | ⚠️² | |
| 3 | App in mehreren Themes | Farben unverändert (nur Namen dazugelegt, keine Optik-Änderung) | ⚠️³ | |
| 4 | DevTools → Elements | Farb-Token sind **RGB-Tripel** und werden als `rgb(var(--…))` verwendet; Deckkraft-Test `rgb(var(--surface-card) / .7)` ergibt eine sichtbare Fläche | ✅⁴ | |
| 5 | `dashboard/src/styles/` | Leisten-Token vorhanden (mit Rückfall); Skalen `--space-*`, `--radius-*`, `--font-*` benannt | ◑⁵ | |
| 6 | Einstellungen → Darstellung | die acht Vorschau-Kacheln zeigen **acht verschiedene** Paletten (nicht 8× classic) | ✅⁶ | |
| 7 | `cd dashboard && npm run build && npm test` | `vue-tsc` ohne Fehler, Build ok, **102/102** Tests grün | ✅ | |

> ¹ **(CC):** live gegen `http://localhost:5173/` (2026-08-15). **64/64** Werte
> exakt: alle 8 Themes × 8 Token gegen die Original-HEX-Liste gemessen
> (`getComputedStyle` über ein Probe-Element je `data-theme`), 0 Abweichungen.
> Abweichung vom Ticket-Wortlaut: die Skill-Token sind **primär** (RGB-Tripel),
> `--c-*` ist der Alias — also andersherum als „Alias-Zeile" nahelegt. Grund:
> ein Alias auf `:root` würde die Theme-Vorschau brechen (siehe ⁶).
> ² **(CC):** ⚠️ vier `#fff` bleiben bewusst stehen (`SettingsPanel`,
> `RangeSelector`, `InstrumentsTable` ×2) plus `base.scss` `button.primary` —
> sie brauchen `--accent-contrast`, das erst mit **T-11d** kommt. Raten wäre
> hier ein Fehler. Alles Übrige ist ersetzt; `rgba()` nur noch im
> Dialog-Schleier (`JsonModal`, bewusst themeneutral, kommentiert).
> ³ **(CC):** ⚠️ zwei **freigegebene** Ausnahmen, sonst unverändert:
> (a) Fehlerrot `#e5484d` → `#e5534b` (Token) an drei Stellen;
> (b) Statuszeile und ein Tabellenrand hatten die *classic*-Palette fest
> verdrahtet und folgen jetzt dem Theme — in den sieben übrigen Themes sichtbar
> **anders, aber richtig**. Gemessen: Kopfzeile `rgba(11,18,15,0.85)`,
> Statuszeile `rgba(11,18,15,0.9)` (forest); Sichtprüfung in *forest* und
> *sunset* ohne Auffälligkeiten.
> ⁴ **(CC):** `rgb(var(--surface-card) / .7)` → `rgba(22,36,29,0.7)`;
> `rgb(var(--accent) / .15)` → `rgba(62,227,159,0.15)`; Status-Token exakt
> `63 185 80 / 240 163 64 / 229 83 75`. Im geladenen CSS **null** `color-mix`
> mehr (18 Stellen ersetzt).
> ⁵ **(CC):** ◑ Skalen vollständig vorhanden und gemessen (`--space-4: 1rem`,
> `--radius-lg: 12px`, `--font-base: 1rem`). **Leisten-Token (`--surface-header`,
> `--surface-statusbar`, `--text-bar*`, `--border-bar`) bewusst NICHT angelegt** —
> sie tragen erst mit den echten Paletten Werte (**T-11d**); leere Hüllen jetzt
> anzulegen brächte nichts. Bestandswerte wurden nicht auf die Skalen
> nachgerüstet (wäre eine Optik-Änderung ohne Nutzen).
> ⁶ **(CC):** acht Kacheln, acht verschiedene Paletten — der Nachweis, dass die
> Aliase im Theme-Block und nicht auf `:root` stehen.

---

## Details

### Kontext / Ziel
Gap-Analyse-Punkt 3 aus **T-11**. Macht Komponenten zwischen Apps portierbar.

### Akzeptanzkriterien
- [x] Skill-Token vorhanden, alte `--c-*` laufen weiter (als Alias im Theme-Block)
- [x] Keine hartkodierten Farben in Komponenten — bis auf 4× `#fff`, die auf
      `--accent-contrast` (T-11d) warten
- [x] Optik unverändert bis auf die zwei freigegebenen Ausnahmen
- [x] RGB-Tripel + `rgb(var(--x) / a)` funktionieren; `color-mix` abgelöst
- [ ] Human-Abnahme

### Side-Effects
Kein Backend-Change.

**Bewusst offen gelassen (gehört zu T-11d):** `--surface-sunken`,
`--text-secondary`, `--border-subtle`, `--accent-contrast` und die Leisten-Token
haben in den acht Alt-Paletten keine Entsprechung — sie wurden **nicht geraten**,
sondern kommen mit den echten Paletten aus `references/themes.md`. Ebenso bleibt
der pro Theme verschiedene `--c-grad`; die Skill-Regel „fester Marken-Verlauf"
ist T-11d.

**Erkenntnis für Folge-Tickets:** Ein Custom Property mit `var()` wird **dort**
ersetzt, wo es deklariert ist, und vererbt sich fertig aufgelöst. Deshalb steht
in `base.scss` alles Theme-Abhängige im jeweiligen `[data-theme]`-Block — ein
Alias auf `:root` würde die Theme-Vorschau (und jede künftige
Theme-in-Theme-Darstellung) stillschweigend auf *classic* festnageln.

### Auflösung
Branch `t-11b-token-aliase` (gestapelt auf `t-11a-nav-settings`), Commits
`842e491 · 20c59bb · 3d3fd0a · 1b35029`. Task-Reviews grün (Task 1 einzeln,
Tasks 2+3 zusammengefasst, Task 4 im Whole-Branch-Review). **Offen:**
Human-Abnahme, dann Merge.

---

## Abschluss (2026-08-16)

Code ist in `master` (Fast-Forward des Branch-Stapels). Die ausstehende
Human-Abnahme entfällt auf Entscheid des Auftraggebers — die KI-Vorabchecks in
der Matrix oben bleiben unverändert stehen, samt ihrer ➖-Zeilen. Die dort
notierten Einschränkungen sind in **T-12** als Prüfpunkte übernommen.
