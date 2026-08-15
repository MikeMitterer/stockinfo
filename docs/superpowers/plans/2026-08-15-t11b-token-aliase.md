# T-11b — Token-Aliase + hartkodierte Farben — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Farbschicht des Dashboards auf die `ux-standards`-Token umstellen — RGB-Tripel statt HEX, Skill-Namen als primäre Token, benannte Skalen — **ohne sichtbare Änderung** der Oberfläche.

**Architecture:** Die acht Theme-Blöcke in `base.scss` tragen künftig die Skill-Token (`--surface-page`, `--text-primary`, …) als **RGB-Tripel**; die alten `--c-*` bleiben **im selben Block** als Rückwärts-Alias (`--c-bg: rgb(var(--surface-page))`), damit die per-Element aufgelöste Theme-Vorschau und die drei JS-Leser weiter funktionieren. `_variables.scss` bleibt die Null-Touch-Fassade: alle 18 SFCs binden sie bereits ein, `$color-*` zeigt künftig auf `rgb(var(--…))`. Komponenten-Templates werden nicht angefasst, außer wo hartkodierte Farben stehen.

**Tech Stack:** Vue 3 SFC, SCSS (`@use '../styles/variables' as *` je Komponente), Vite, Vitest.

## Global Constraints

- **Optik bleibt unverändert.** HEX→Tripel ist eine verlustfreie Umrechnung; jeder Wert muss exakt demselben Farbton entsprechen. Einzige bewusste Ausnahme: die drei `.err`/`tr.error`-Stellen wechseln von `#e5484d` auf `--status-out` (`#e5534b`) — vom Auftraggeber freigegeben.
- **`_variables.scss` darf kein CSS erzeugen.** Sie wird von 18 SFCs `@use`d; ein `:root { … }` darin landete 18× im Bündel. Nur Variablen/Funktionen/Mixins. **Alle `:root`-Regeln gehören nach `base.scss`.**
- **Aliase gehören in den Theme-Block, nie nur auf `:root`.** Ein Custom Property mit `var()` wird **dort** ersetzt, wo es deklariert ist, und vererbt sich fertig aufgelöst. `:root { --surface-page: var(--c-bg) }` würde alle acht Vorschau-Kacheln in `ThemesPanel.vue` auf *classic* zeigen.
- **Nicht erfinden:** Für `--surface-sunken`, `--text-secondary`, `--border-subtle`, `--accent-contrast` gibt es in den acht Alt-Paletten keine Entsprechung. Sie werden **nicht** geraten — sie kommen mit den echten Paletten in **T-11d**.
- Status-Farben sind themeunabhängig (Skill) → einmal auf `:root`, mit den **heutigen** Werten. Die Skill-Stufen (`25 158 112` …) kommen mit T-11d.
- Der Marken-Verlauf `--c-grad` ist pro Theme verschieden und **kein** Tripel — er bleibt unverändert. Die Skill-Regel „fester Marken-Verlauf" ist T-11d.
- Skalen (`--space-*`, `--radius-*`, `--font-*`) werden **angelegt, aber nicht nachgerüstet**: bestehende Komponenten behalten ihre Literale (sonst Optik-Risiko). Neue Regeln nutzen die Skala.
- Gate je Task: `npm run build` (`vue-tsc -b && vite build`) sauber **und** `npm test` grün. Vorbestehende Sass-„legacy-JS-API"-Warnung ist nicht neu.
- Arbeitsverzeichnis: `dashboard/`.

---

### Task 1: Theme-Blöcke auf RGB-Tripel + Skill-Token

**Files:**
- Modify: `dashboard/src/styles/base.scss:3-44` (Theme-Blöcke), plus neuer `:root`-Block für Status + Skalen

**Interfaces:**
- Produces: pro Theme-Block die Token `--surface-page`, `--surface-card`, `--surface-raised`, `--border-default`, `--text-primary`, `--text-muted`, `--accent`, `--accent-2` als **Tripel**; `--c-bg/-surface/-surface-2/-border/-text/-muted/-accent/-accent-2` als `rgb(var(--…))`-Alias im selben Block; `--c-grad` unverändert. Auf `:root`: `--status-ok/-near/-out` + Skalen.

- [ ] **Step 1: Umrechnungstabelle erzeugen und prüfen**

Die Umrechnung darf nicht per Augenmaß passieren. Erzeuge sie mit einem Wegwerf-Skript und lies das Ergebnis:

```bash
cd dashboard && node -e '
const hex=s=>{const n=parseInt(s.slice(1),16);return [n>>16&255,n>>8&255,n&255].join(" ")};
const vals="#100c16 #221b2d #302640 #493a5c #f4f0fa #b0a3c6 #f2673f #d16bb5 #08111b #10202f #182f43 #2c4763 #eef5fb #9db6cf #4cc5ff #7c7bff #150f09 #251b12 #352818 #533f28 #f6eee2 #c4ad91 #f0973f #c76f2f #0c0c17 #191930 #242444 #3a3a63 #efedff #aaa6d6 #9a8bff #cf8bff #0e0e0e #1e1e1e #2c2c2c #474747 #f5f5f5 #b0b0b0 #e6e6e6 #9c9c9c #160c12 #281824 #3a2433 #593c4f #fbeaf1 #d3a6bc #ff7d8f #ff934a #0b120f #16241d #21362b #35533f #ecf6f0 #9dc2ad #3ee39f #17c07f #08080f #16162a #21213c #383860 #f0f0ff #a8a8d6 #2fe0ff #ff45d6 #3fb950 #f0a340 #e5534b".split(" ");
vals.forEach(v=>console.log(v, "->", hex(v)));'
```

Erwartung: 67 Zeilen, u.a. `#100c16 -> 16 12 22`, `#3fb950 -> 63 185 80`, `#e5534b -> 229 83 75`.

- [ ] **Step 2: Theme-Blöcke ersetzen**

`base.scss` Zeilen 3–44 ersetzen. Muster je Theme (hier *classic* vollständig; die übrigen sieben **exakt analog** mit den Werten aus Step 1):

```scss
// ─── Theme-Paletten (8 Themes, persistent via data-theme) ─────────────────────
// Primär sind die ux-standards-Token als RGB-Tripel (rgb(var(--x)) / rgb(var(--x) / .5)).
// Die --c-*-Namen bleiben als Rückwärts-Alias im SELBEN Block: ThemesPanel löst sie
// je Vorschau-Kachel im eigenen [data-theme]-Kontext auf — ein Alias auf :root
// würde dort fertig aufgelöst vererbt und alle Kacheln classic zeigen.
:root,
[data-theme='classic'] {
  --surface-page: 16 12 22;    --surface-card: 34 27 45;
  --surface-raised: 48 38 64;  --border-default: 73 58 92;
  --text-primary: 244 240 250; --text-muted: 176 163 198;
  --accent: 242 103 63;        --accent-2: 209 107 181;

  --c-bg: rgb(var(--surface-page));       --c-surface: rgb(var(--surface-card));
  --c-surface-2: rgb(var(--surface-raised)); --c-border: rgb(var(--border-default));
  --c-text: rgb(var(--text-primary));     --c-muted: rgb(var(--text-muted));
  --c-accent: rgb(var(--accent));         --c-accent-2: rgb(var(--accent-2));
  --c-grad: linear-gradient(120deg, #f2673f, #9a3593);
}
```

Zuordnung (gilt für alle acht Blöcke): `--c-bg`→`--surface-page`, `--c-surface`→`--surface-card`, `--c-surface-2`→`--surface-raised`, `--c-border`→`--border-default`, `--c-text`→`--text-primary`, `--c-muted`→`--text-muted`, `--c-accent`→`--accent`, `--c-accent-2`→`--accent-2`. `--c-grad` bleibt wörtlich stehen.

- [ ] **Step 3: Status-Token und Skalen auf `:root`**

Direkt nach den Theme-Blöcken in `base.scss` einfügen:

```scss
// ─── Bedeutungstragende Farben (themeunabhängig) ──────────────────────────────
// Werte = heutige Ampel-Töne. Die Skill-Stufen kommen mit den Paletten (T-11d).
:root {
  --status-ok: 63 185 80;
  --status-near: 240 163 64;
  --status-out: 229 83 75;
}

// ─── Skalen ───────────────────────────────────────────────────────────────────
// Angelegt für neue Regeln; Bestandswerte werden bewusst NICHT nachgerüstet
// (das wäre eine Optik-Änderung ohne Nutzen). --font-* sind Schriftgrößen,
// die Textfarben heißen --text-*.
:root {
  --space-1: 0.25rem; --space-2: 0.5rem;  --space-3: 0.75rem;
  --space-4: 1rem;    --space-6: 1.5rem;  --space-8: 2rem;

  --radius-sm: 8px; --radius-lg: 12px; --radius-full: 9999px;

  --font-xs: 0.75rem; --font-sm: 0.875rem; --font-base: 1rem;
  --font-lg: 1.125rem; --font-xl: 1.5rem;
}
```

- [ ] **Step 4: Gate**

Run: `cd dashboard && npm run build && npm test`
Expected: `vue-tsc` ohne Fehler, Build ok, alle Tests grün.

- [ ] **Step 5: Commit**

```bash
git add dashboard/src/styles/base.scss
git commit -m "refactor(dashboard): Theme-Paletten als RGB-Tripel + ux-standards-Token (T-11b)"
```

---

### Task 2: `_variables.scss` auf die neuen Token + `token()`-Funktion

**Files:**
- Modify: `dashboard/src/styles/_variables.scss`

**Interfaces:**
- Consumes: die Token aus Task 1.
- Produces: `$color-*` unverändert **im Namen**, neu im Wert (`rgb(var(--…))`); `$color-danger`/`$health-*` auf die Status-Token; neue SCSS-Funktion `token($name, $alpha: 1)`.

- [ ] **Step 1: Datei ersetzen**

```scss
// ─── Marken-Basis (fixe Referenzwerte) ────────────────────────────────────────
$brand-orange: #df5430;
$brand-purple: #812c7c;

// ─── Farbzugriff ──────────────────────────────────────────────────────────────
// Die Token sind RGB-Tripel (base.scss). token() macht daraus eine Farbe,
// wahlweise mit Deckkraft: token(--accent, .15) statt color-mix(…).
@function token($name, $alpha: 1) {
  @if $alpha == 1 {
    @return rgb(var(#{$name}));
  }
  @return rgb(var(#{$name}) / #{$alpha});
}

// ─── Themebare Farben — Werte kommen aus [data-theme] in base.scss ─────────────
$color-bg: token(--surface-page);
$color-surface: token(--surface-card);
$color-surface-2: token(--surface-raised);
$color-border: token(--border-default);
$color-text: token(--text-primary);
$color-muted: token(--text-muted);
$color-accent: token(--accent);
$color-accent-2: token(--accent-2);
$brand-gradient: var(--c-grad);

// ─── Health-Ampel (themeunabhängig, semantisch) ───────────────────────────────
$color-danger: token(--status-out);
$health-ok: token(--status-ok);
$health-warn: token(--status-near);
$health-down: token(--status-out);

// ─── Maße & Schrift ───────────────────────────────────────────────────────────
$radius: 10px;      // Bestandswert; die Skala (--radius-*) gilt für neue Regeln.
$font-mono: 'SF Mono', 'JetBrains Mono', 'Menlo', ui-monospace, monospace;
$header-h: 58px;
$header-bp: 1280px; // Tailwind xl: ab hier volle Tab-Zeile, darunter Hamburger-Drawer.
                    // 1280 statt 1024, weil die 7-Tab-Zeile ~1094px braucht (EN) und
                    // knapp über 1024 sonst staucht ("API & Links" bricht um).
$status-h: 32px;
```

- [ ] **Step 2: Gate**

Run: `cd dashboard && npm run build && npm test`
Expected: sauber/grün. Die Datei erzeugt weiterhin **kein** CSS (nur Variablen + Funktion).

- [ ] **Step 3: Commit**

```bash
git add dashboard/src/styles/_variables.scss
git commit -m "refactor(dashboard): \$color-*/\$health-* auf Token, token()-Funktion (T-11b)"
```

---

### Task 3: Hartkodierte Farben ersetzen

**Files:**
- Modify: `dashboard/src/components/AnalysisPanel.vue:96,100`
- Modify: `dashboard/src/components/FxPanel.vue:114`
- Modify: `dashboard/src/components/StatusBar.vue:41`
- Modify: `dashboard/src/components/InstrumentsTable.vue:246`
- Modify: `dashboard/src/components/JsonModal.vue:82`
- Modify: `dashboard/src/components/HistoryChart.vue:99,119,120`

**Interfaces:**
- Consumes: `token()`, `$color-danger`, `$color-border` aus Task 2.

- [ ] **Step 1: Fehlerrot vereinheitlichen**

`AnalysisPanel.vue:96` `.err { color: #e5484d; … }` → `color: $color-danger;`
`AnalysisPanel.vue:100` `tr.error td { color: #e5484d; }` → `color: $color-danger;`
`FxPanel.vue:114` `.err { color: #e5484d; }` → `color: $color-danger;`

(Bewusste Mini-Änderung: `#e5484d` → `#e5534b`, freigegeben.)

- [ ] **Step 2: Themeblinde `rgba` ersetzen**

`StatusBar.vue:41` `rgba(20, 16, 25, 0.9)` — hartkodiert die *classic*-Palette und sieht in den anderen sieben Themes falsch aus → `token(--surface-page, 0.9)`.

`InstrumentsTable.vue:246` `rgba(56, 44, 70, 0.5)` (Näherung an `$color-border` bei 50 %) → `token(--border-default, 0.5)`.

`JsonModal.vue:82` `rgba(0, 0, 0, 0.6)` — der Dialog-Schleier ist bewusst neutral-schwarz und **kein** Theme-Ton. Unverändert lassen; einen Kommentar dazuschreiben:
```scss
  // Bewusst neutrales Schwarz, kein Theme-Ton — der Schleier soll in jedem
  // Theme gleich abdunkeln.
  background: rgba(0, 0, 0, 0.6);
```

- [ ] **Step 3: Stale JS-Fallbacks korrigieren**

`HistoryChart.vue:99,119,120` lesen `cssVar('--c-accent', '#df5430')` usw. Die Fallbacks sind veraltet (`#df5430` ist nicht der classic-Akzent `#f2673f`; `#9a8fb0`/`#382c46` entsprechen keinem Theme). Da `--c-*` als Alias erhalten bleibt, funktionieren die Leser weiter — nur die Fallback-Literale auf die tatsächlichen classic-Werte ziehen: `#f2673f` (accent), `#b0a3c6` (muted), `#493a5c` (border).

- [ ] **Step 4: Kein Rest**

Run: `cd dashboard && grep -rnE '#[0-9a-fA-F]{3,8}' src/components src/styles | grep -v 'c-grad' | grep -v '\$brand-'`
Expected: nur noch `#fff` (4 Stellen: `SettingsPanel.vue`, `RangeSelector.vue`, `InstrumentsTable.vue:309,314`) und `base.scss:80` — die bleiben, bis `--accent-contrast` mit T-11d kommt. Notiere die Liste im Report.

- [ ] **Step 5: Gate + Commit**

Run: `cd dashboard && npm run build && npm test`

```bash
git add dashboard/src/components
git commit -m "refactor(dashboard): hartkodierte Farben auf Token (T-11b)"
```

---

### Task 4: `color-mix` auf `token()` umstellen

**Files:**
- Modify: die 16 `color-mix`-Stellen in `ExchangesPanel.vue`, `InstrumentsTable.vue`, `ErrorBanner.vue`, `App.vue`, `AppHeader.vue`, `HistoryChart.vue`, `FxPanel.vue` — plus `base.scss:137,141`

**Interfaces:**
- Consumes: `token()` aus Task 2.

- [ ] **Step 1: Umstellen**

`color-mix(in srgb, $color-accent 15%, transparent)` → `token(--accent, 0.15)`.
Das ist wertgleich: `color-mix` mit `transparent` liefert dieselbe Farbe bei Alpha 0.15.

Vorgehen: alle Vorkommen finden und einzeln ersetzen, Prozentwert → Dezimalwert.

```bash
cd dashboard && grep -rn 'color-mix' src/
```

Zuordnung der Variablen: `$color-accent`→`--accent`, `$color-bg`→`--surface-page`, `$color-border`→`--border-default`, `$color-muted`→`--text-muted`, `$color-surface`→`--surface-card`, `$color-danger`→`--status-out`, `var(--c-muted)`→`--text-muted`.

- [ ] **Step 2: Kein Rest**

Run: `cd dashboard && grep -rn 'color-mix' src/`
Expected: keine Treffer mehr. Findet sich eine Stelle, die sich **nicht** sauber übersetzen lässt (z.B. Mischung zweier echter Farben statt gegen `transparent`), bleibt sie stehen — dann im Report begründen.

- [ ] **Step 3: Gate + Commit**

Run: `cd dashboard && npm run build && npm test`

```bash
git add dashboard/src
git commit -m "refactor(dashboard): color-mix durch token(--x, alpha) ersetzt (T-11b)"
```

---

## Nach dem Plan: Verifikation

- **Farbtreue maschinell prüfen** (nicht nach Augenmaß): im Browser je Theme die berechneten Werte gegen die Original-HEX-Liste halten:
  ```js
  const want = { classic:'#100c16', ocean:'#08111b', earth:'#150f09', night:'#0c0c17',
                 mono:'#0e0e0e', sunset:'#160c12', forest:'#0b120f', neon:'#08080f' };
  Object.entries(want).map(([t,hex]) => {
    document.documentElement.dataset.theme = t;
    const got = getComputedStyle(document.body).backgroundColor;
    const [r,g,b] = hex.match(/\w\w/g).map(h => parseInt(h,16));
    return [t, got, `rgb(${r}, ${g}, ${b})`, got === `rgb(${r}, ${g}, ${b})`];
  });
  ```
  Alle acht müssen `true` liefern.
- **Theme-Vorschau**: `#/settings?tab=appearance` — die acht Kacheln müssen **verschiedene** Paletten zeigen (nicht 8× classic). Das ist der Lackmustest für die Alias-Platzierung.
- **Deckkraft**: `rgb(var(--surface-card) / .7)` ergibt eine sichtbare Fläche (Verify #4 des Tickets).
- Danach Verify-Matrix in `_tickets/T-11b-token-aliase-hardcoded-farben.md` füllen.

## Self-Review

**Spec-Coverage:** Alias-Namen (Task 1) ✓ · RGB-Tripel + `rgb(var())` (Task 1/2) ✓ · Leisten-Token — **bewusst nicht** (kommen mit T-11d, siehe Constraints; Ticket-Verify #5 nennt sie „vorsehen", die Zeile wird beim Ausfüllen auf ◑ gesetzt) · Skalen (Task 1) ✓ · hartkodierte Farben (Task 3) ✓ · Deckkraft-Nachweis (Verifikation) ✓.

**Placeholder-Scan:** keine TBD; jeder Schritt trägt konkreten Code oder ein ausführbares Kommando.

**Typkonsistenz:** `token()` ist in Task 2 definiert und wird erst in Task 3/4 verwendet — Reihenfolge stimmt. Die in Task 1 erzeugten Token-Namen decken exakt die in Task 2 referenzierten ab (`--surface-page/-card/-raised`, `--border-default`, `--text-primary/-muted`, `--accent`, `--accent-2`, `--status-ok/-near/-out`). `--surface-sunken`/`--text-secondary`/`--border-subtle`/`--accent-contrast` werden nirgends referenziert — konsistent mit „nicht erfinden".
