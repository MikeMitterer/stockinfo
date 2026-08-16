# T-11d · Themes-Namen/Kontrast abgleichen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | backlog | ~3 h | UI-only | — |

**Löst:** Paletten aus `ux-standards/references/themes.md` übernehmen — gleiche
Theme-**Namen** ⇒ gleiche Farbe über Apps; Status themeunabhängig in zwei Stufen;
Kontrast mit dem Skill-Werkzeug belegen. Teil-Ticket von **T-11** (Punkt 5).

**Überholt (Stand 2026-08-15):** Ursprünglich war geplant, StockInfos `classic`
(pflaume/korall) in `mangolila` umzubenennen. Das gilt **nicht mehr**:
`mangolila` ist im Skill inzwischen *warmes Anthrazit*, der Pflaumen-Entwurf
wurde ausdrücklich verworfen (Farbton 264° statt 304° der Marke, nur 19° von
`aurora` entfernt). StockInfos altes Pflaumen-Theme entspricht damit **keinem**
Skill-Theme — die Paletten werden schlicht ersetzt, nicht zugeordnet.

**Stand Skill 2026-08-16:** jetzt **dreizehn** Themes (neu gegenüber StockInfo:
`mangolila`, `amber`, `petrol`, `slate`, `aurora`, `carbon`, `paper`, `sepia`,
`meadow`) mit vollständigen RGB-Werten in `themes.md`.
Dazu **Leisten-Token** (`--surface-header`, `--surface-statusbar`, `--text-bar`,
`--text-bar-secondary`, `--text-bar-muted`, `--border-bar`) und vier
„Behandlungen" der Leisten (gleiche Ebene · tiefer · heller · Farbschleier ·
umgekehrt) — jede mindestens einmal vertreten.

**Widerspruch in der Quelle (beim Umsetzen beachten):** Der Fließtext in
`themes.md` sagt zweimal, `carbon` bringe eigene, kräftigere Status-Stufen mit —
im **erzeugten** `carbon`-Block stehen sie nicht (mehr). Da die Wertblöcke per
`theme-tokens.py export` erzeugt werden und der Fließtext von Hand ist, gilt der
Block: `carbon` bekommt **keine** eigenen Status-Werte. Ebenso veraltet ist die
Aufzählung der dunklen Themes („mangolila, classic, slate, ocean, forest,
aurora") — tatsächlich sind **neun** dunkel, zusätzlich `amber`, `petrol` und
`carbon`. Beides an Mike gemeldet, nicht eigenmächtig im Skill korrigiert.

**Marke (Skill-Nachtrag, gleicher Tag):** Der Verlauf ist **themeunabhängig**
und je App eigen — für StockInfo **Koralle → Pflaume, `#df5430` → `#812c7c`,
135°**. Das sind exakt die heute toten `$brand-orange`/`$brand-purple` in
`_variables.scss`; sie werden damit wieder lebendig. Heute ist `--c-grad`
dagegen **pro Theme verschieden und 120°** — das fällt weg.

**Achtung, zwei verwechselbare Token:**
`--brand-contrast: 255 255 255` (fest, Zeichen auf dem Marken-Verlauf) steht
**neben** `--accent-contrast` (Text auf der *Akzent*fläche, wechselt mit dem
Theme — in acht der dreizehn Paletten nahezu schwarz). Die Plakette ist keine
Akzentfläche; ein Zeichen darauf, das mit dem Theme umschlägt, verschwindet in
genau diesen acht. Die vier aus **T-11b** übrig gebliebenen `#fff` müssen
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
| 1 | Theme-Auswahl | `mangolila` ist warmes **Anthrazit** (nicht pflaume); `classic` neutralgrau | ➖ | |
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
Gap-Analyse-Punkt 5 aus **T-11**. Die Werte werden **kopiert, nicht nachgerechnet**
— der Skill sagt es wörtlich: dieselbe Palette zweimal zu lösen liefert
schlimmstenfalls leicht andere Zahlen, und dann heißen zwei Paletten gleich und
sehen verschieden aus.

### Akzeptanzkriterien
- [ ] `earth`/`night`/`sunset`/`neon` entfallen; gespeicherte Wahl fällt sauber auf die Systemvorgabe
- [ ] helle Paletten ergänzt; `prefers-color-scheme` entscheidet (dunkel → `mangolila`, hell → `paper`)
- [ ] Kontrast geprüft, nicht geschätzt
- [ ] alle dreizehn Paletten übernommen (Werte unverändert aus `themes.md`)
- [ ] `theme-tokens.py check --zonen` läuft mit Exit-Code 0 durch
- [ ] Leisten-Token gesetzt; mindestens je eine Behandlung sichtbar vertreten
- [ ] Theme-Vorschau zeigt vier Farbflecken (`--surface-page`, `--surface-card`,
      `--text-primary`, `--accent`) — StockInfo löst das über `data-theme` an der
      Kachel und braucht die im Skill beschriebene Kopie der Werte nicht

### Side-Effects
Kein Backend-Change. Theme-Namen folgen MakeLib-Konvention (`MAKE_THEME`).

### Auflösung
_(offen)_

---

## Abschluss (2026-08-16)

**Nicht einzeln umgesetzt — abgelöst durch T-12.** Was dieses Ticket
nachbauen wollte, liefert `@mikemitterer/ux-foundation` seit dem 16.08.2026
fertig. Ein zweiter Nachbau wäre genau die Doppelung, die das Paket beenden
soll. Die Anforderungen sind in T-12 als Abnahmekriterien übernommen.
