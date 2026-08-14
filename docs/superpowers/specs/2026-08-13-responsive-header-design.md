# Design: Responsive Header / Mobile-Navigation (T-05)

**Datum:** 2026-08-13
**Ticket:** `_tickets/T-05-responsive-header-mobile.md`
**Scope:** Frontend (Dashboard). Kein Backend-Change.

## Problem

`AppHeader.vue` ist eine reine Flex-Zeile ohne jeden `@media`-Breakpoint (im
gesamten Dashboard existiert keine einzige Media Query). Bei 7 Tabs
(Icon + Label) + Sprachumschalter + Logo reißt die Zeile auf schmalen Screens;
die Navigation überlappt das Logo (in Screenshots bestätigt, Nutzer-Meldung
„UI funktioniert auf Mobile überhaupt nicht, Menü ist nicht mehr zu sehen").
Das Viewport-Meta ist bereits gesetzt (`width=device-width`).

## Lösung — Hamburger-Drawer

Unterhalb eines Breakpoints kollabiert die Tab-Zeile in einen ☰-Button, der
einen vertikalen Drawer mit allen 7 Tabs öffnet. Oberhalb bleibt die heutige
Optik unverändert.

### 1. Breakpoint

- SCSS-Variable, Startwert **768px**. Der finale Wert wird im Browser gegen
  „keine Überlappung von Logo/Nav/Sprache" verifiziert und ggf. angehoben
  (7 Icon+Label-Tabs sind breit — der Umbruchpunkt kann über 768px liegen).
- Oberhalb: heutiges Layout unverändert (Tab-Zeile, `margin-left: auto`).
- Unterhalb: Tab-Zeile aus, ☰-Button an.

### 2. Interaktion & State

- Lokaler `ref` `isOpen = ref(false)` in `AppHeader.vue`; Drawer per `v-if="isOpen"`.
- ☰-Button togglet `isOpen`.
- Drawer schließt bei:
  - **Tab-Auswahl** — emittiert `navigate` und setzt `isOpen = false`.
  - **Escape** — `keydown`-Listener (nur aktiv/registriert, solange nötig;
    `window`-Listener via `onMounted`/`onUnmounted`).
  - **Klick außerhalb** — ein Backdrop-Element hinter dem Drawer fängt den Klick
    und schließt.
- Der Sprachumschalter (DE/EN) bleibt in der Kopfzeile (kompakt); nur die 7
  Tabs wandern in den Drawer.

### 3. a11y & i18n

- ☰-Button: `:aria-label="t('nav.menu')"`, `:aria-expanded="isOpen"`,
  `aria-controls="mobile-nav"`. Drawer trägt `id="mobile-nav"` und ist ein
  `<nav>`-Landmark.
- **Ein** neuer i18n-Key `nav.menu` — `de.ts`: „Menü", `en.ts`: „Menu".
- Alle Tab-Labels werden über die bestehende `tabs`-computed wiederverwendet —
  kein weiterer hartkodierter Text.

### 4. CSS-Struktur (der eigentliche Fix)

- `.appheader nav.tabs` (Inline-Zeile): `display: flex` desktop →
  `@media (max-width: $bp) { display: none }`.
- `.hamburger`: `display: none` desktop →
  `@media (max-width: $bp) { display: inline-flex }`.
- `.drawer`: positioniert unter dem Header (`position: fixed; top: $header-h`);
  zusätzlich `@media (min-width: $bp+1) { display: none }` als Sicherung, falls
  beim Vergrößern noch offen.
- Desktop-Optik unverändert.

## Betroffene Einheiten

| Datei | Änderung |
|---|---|
| `components/AppHeader.vue` | ☰-Button, Drawer, `isOpen`-State, Escape/Klick-außerhalb, `@media`-Styles |
| `i18n/de.ts`, `i18n/en.ts` | neuer Key `nav.menu` |
| `tests/components/AppHeader.spec.ts` | **neu** — Toggle-/Schließ-Logik |

Kein Backend-Change; keine anderen Komponenten betroffen.

## Teststrategie (TDD)

jsdom wertet keine CSS-Media-Queries visuell aus — die Elemente sind unabhängig
vom Viewport im DOM, CSS blendet nur ein/aus. Daher testet Vitest die
**JS-Toggle-Logik** viewport-unabhängig; das responsive Ein-/Ausblenden wird im
**Browser** verifiziert.

- **`AppHeader.spec.ts`:**
  - ☰-Button ist vorhanden (mit `aria-label` aus `nav.menu`).
  - Klick auf ☰ öffnet den Drawer → 7 Tab-Einträge vorhanden.
  - Klick auf einen Drawer-Tab emittiert `navigate` mit dem richtigen Key **und**
    schließt den Drawer (`isOpen` false → Einträge weg).
  - Escape schließt den offenen Drawer.
- Bestehende Tests bleiben grün.
- **Browser-Verifikation (eigener Task):** bei schmaler Breite (~375px) keine
  Überlappung Logo/Nav/Sprache; ☰ öffnet/schließt; alle 7 Tabs erreichbar;
  Desktop-Breite unverändert; DE/EN.

## Bewusst NICHT im Scope (YAGNI)

- Keine Animationen/Transitions über das Nötigste hinaus.
- Kein Verschieben des Sprachumschalters in den Drawer.
- Keine Änderung an anderen Panels/Layouts; nur der Header.
- Keine allgemeine Responsive-Überarbeitung des restlichen Dashboards.
