# Responsive Header / Mobile-Navigation (T-05) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unter einem Breakpoint kollabiert die Header-Navigation in ein Hamburger-Menü (Drawer); oberhalb bleibt die heutige Optik unverändert.

**Architecture:** Rein `AppHeader.vue` + ein neuer i18n-Key. Eine `nav`-Zeile (die 7 Tabs) bleibt ein einziges Element: auf Desktop die bestehende Inline-Reihe, unter dem Breakpoint per `.open`-Klasse ein fixierter Drawer. Ein ☰-Button togglet, ein Backdrop fängt Klick-außerhalb, Escape schließt. Kein Backend-Change.

**Tech Stack:** Vue 3 `<script setup lang="ts">`, vue-i18n, Vitest + @vue/test-utils (jsdom), SCSS.

## Global Constraints

- **i18n MUST:** kein hartkodierter UI-Text; genau **ein** neuer Key `nav.menu` in `de.ts` **und** `en.ts` (DE „Menü", EN „Menu"). Tab-Labels werden über die bestehende `tabs`-computed wiederverwendet.
- **Breakpoint:** SCSS-Variable `$header-bp: 1024px` — konventionelle „unter Desktop"-Grenze (Tailwind `lg`, Material-Design Desktop-Schwelle). **Kein** geschätzter Wert. Ab 1024px volle Tab-Zeile (Desktop, unverändert), darunter (Tablet + Mobile) Hamburger-Drawer.
- **DRY:** die 7 Tab-Buttons existieren **einmal** (ein `<nav v-for>`), nicht doppelt für Desktop/Drawer.
- **Kein Backend-Change**; keine anderen Komponenten.
- **Branch zuerst:** vor Task 1 `git checkout -b feat/responsive-header` (Default-Branch ist `master`).
- **Arbeitsverzeichnis aller Kommandos:** `dashboard/`. Test-Runner: `npx vitest run <pfad>`.

---

### Task 1: Hamburger-Drawer im AppHeader

**Files:**
- Modify: `dashboard/src/styles/_variables.scss` (Breakpoint-Variable)
- Modify: `dashboard/src/i18n/de.ts`, `dashboard/src/i18n/en.ts` (Key `nav.menu`)
- Modify: `dashboard/src/components/AppHeader.vue`
- Test: `dashboard/tests/components/AppHeader.spec.ts` (neu)

**Interfaces:**
- Consumes: bestehende `tabs`-computed, `emit('navigate', TabKey)`, `t()`.
- Produces: keine neuen Exporte. Neu im DOM: `.hamburger`-Button, `nav.nav-tabs`(`.open`), `.backdrop`.

- [ ] **Step 1: Breakpoint-Variable ergänzen**

In `dashboard/src/styles/_variables.scss` neben `$header-h: 58px;` ergänzen:
```scss
$header-bp: 1024px; // konventionelle Desktop-Grenze (Tailwind lg / Material): ab hier
                    // volle Tab-Zeile, darunter Hamburger-Drawer
```

- [ ] **Step 2: i18n-Key `nav.menu` ergänzen**

In `dashboard/src/i18n/de.ts` im `nav`-Block (nach `home: 'Zur Startseite',`):
```ts
    menu: 'Menü',
```
In `dashboard/src/i18n/en.ts` im `nav`-Block (nach `home: 'Go to start page',`):
```ts
    menu: 'Menu',
```

- [ ] **Step 3: Failing test schreiben**

`dashboard/tests/components/AppHeader.spec.ts`:
```ts
import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'

import AppHeader from '../../src/components/AppHeader.vue'
import { i18n } from '../../src/i18n'

function mountHeader() {
  return mount(AppHeader, { props: { active: 'assets' }, global: { plugins: [i18n] } })
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
})

describe('AppHeader mobile menu', () => {
  it('rendert einen Hamburger-Button mit aria-label aus nav.menu', () => {
    const wrapper = mountHeader()
    const burger = wrapper.find('.hamburger')
    expect(burger.exists()).toBe(true)
    expect(burger.attributes('aria-label')).toBe('Menü')
  })

  it('öffnet den Drawer per Hamburger und schließt ihn bei Tab-Auswahl', async () => {
    const wrapper = mountHeader()
    expect(wrapper.find('.nav-tabs').classes()).not.toContain('open')

    await wrapper.find('.hamburger').trigger('click')
    expect(wrapper.find('.nav-tabs').classes()).toContain('open')

    const tabButtons = wrapper.findAll('.nav-tabs .tab')
    expect(tabButtons).toHaveLength(7)
    await tabButtons[1].trigger('click') // exchanges
    expect(wrapper.emitted('navigate')?.[0]).toEqual(['exchanges'])
    expect(wrapper.find('.nav-tabs').classes()).not.toContain('open')
  })

  it('schließt den offenen Drawer bei Escape', async () => {
    const wrapper = mountHeader()
    await wrapper.find('.hamburger').trigger('click')
    expect(wrapper.find('.nav-tabs').classes()).toContain('open')

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.nav-tabs').classes()).not.toContain('open')
  })
})
```

- [ ] **Step 4: Run test to verify it fails**

Run: `npx vitest run tests/components/AppHeader.spec.ts`
Expected: FAIL — `.hamburger` existiert nicht, `.nav-tabs` fehlt die Klasse/Toggle.

- [ ] **Step 5: AppHeader.vue umbauen**

Ersetze den **`<script setup>`**-Block-Kopf: Imports und State ergänzen.
```ts
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { LOCALES, setLanguage } from '../i18n'
import type { NavIconName, TabKey } from '../types'
import NavIcon from './NavIcon.vue'

defineProps<{ active: TabKey }>()

const emit = defineEmits<{
  (event: 'navigate', tab: TabKey): void
}>()

const { t, locale } = useI18n()

const isOpen = ref(false)
```
Die `tabs`-computed bleibt unverändert. Danach (nach der computed) ergänzen:
```ts
/** Navigiert zum Tab und schließt das mobile Menü. */
function selectTab(key: TabKey): void {
  emit('navigate', key)
  isOpen.value = false
}

/** Schließt das mobile Menü bei Escape. */
function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') isOpen.value = false
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
```

Ersetze das **`<template>`** komplett durch:
```html
<template>
  <header class="appheader">
    <button class="brand" :title="t('nav.home')" @click="emit('navigate', 'assets')">
      <img class="logo" src="/stockinfo-logo.svg" alt="StockInfo" />
    </button>

    <button
      class="hamburger"
      :aria-label="t('nav.menu')"
      :aria-expanded="isOpen"
      aria-controls="mobile-nav"
      @click="isOpen = !isOpen"
    >
      ☰
    </button>

    <div v-if="isOpen" class="backdrop" @click="isOpen = false" />

    <nav id="mobile-nav" class="nav-tabs" :class="{ open: isOpen }">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab"
        :class="{ active: tab.key === active }"
        @click="selectTab(tab.key)"
      >
        <NavIcon :name="tab.icon" />
        <span>{{ tab.label }}</span>
      </button>
    </nav>

    <div class="lang" role="group" :aria-label="t('language.title')">
      <button
        v-for="lang in LOCALES"
        :key="lang"
        class="lng"
        :class="{ active: locale === lang }"
        :title="t(`language.${lang}`)"
        @click="setLanguage(lang)"
      >
        {{ lang.toUpperCase() }}
      </button>
    </div>
  </header>
</template>
```

Im **`<style scoped>`** die alte `nav { … }`-Regel auf `.nav-tabs` umbenennen und Hamburger/Backdrop/Media-Query ergänzen. Ersetze die Zeile
```scss
  nav { display: flex; gap: 0.25rem; margin-left: auto; }
```
durch:
```scss
  .nav-tabs { display: flex; gap: 0.25rem; margin-left: auto; }

  .hamburger {
    display: none; // Desktop: versteckt
    margin-left: auto;
    background: transparent;
    border: none;
    color: $color-text;
    font-size: 1.4rem;
    line-height: 1;
    padding: 0.3rem 0.55rem;
    border-radius: $radius;
    cursor: pointer;
    &:hover { background: $color-surface-2; }
  }

  .backdrop { display: none; } // Desktop: nie
```
und **am Ende** des `.appheader`-Blocks (vor dessen schließender `}`) ergänzen:
```scss
  @media (max-width: $header-bp) {
    .nav-tabs {
      display: none; // geschlossen
      &.open {
        display: flex;
        flex-direction: column;
        align-items: stretch;
        gap: 0.15rem;
        position: fixed;
        top: $header-h;
        left: 0;
        right: 0;
        margin-left: 0;
        padding: 0.5rem 1.25rem 0.75rem;
        background: color-mix(in srgb, $color-bg 96%, transparent);
        backdrop-filter: blur(8px);
        border-bottom: 1px solid $color-border;
        z-index: 19;

        .tab { width: 100%; justify-content: flex-start; }
        .tab.active::after { display: none; } // Unterstrich im Drawer weglassen
      }
    }

    .hamburger { display: inline-flex; align-items: center; }

    .backdrop {
      display: block;
      position: fixed;
      inset: $header-h 0 0 0;
      z-index: 18;
      background: transparent;
    }
  }
```

- [ ] **Step 6: Run the failing test again — expect PASS**

Run: `npx vitest run tests/components/AppHeader.spec.ts`
Expected: PASS (3 Fälle).

- [ ] **Step 7: Full suite + typecheck/build**

Run: `npx vitest run` → alle grün (keine Regression).
Run: `npm run build` → `vue-tsc` + Vite-Build sauber.

- [ ] **Step 8: Commit**

```bash
git add dashboard/src/styles/_variables.scss dashboard/src/i18n/de.ts dashboard/src/i18n/en.ts dashboard/src/components/AppHeader.vue dashboard/tests/components/AppHeader.spec.ts
git commit -m "feat(dashboard): Header-Navigation mobil als Hamburger-Drawer"
```

---

### Task 2: Browser-Verifikation + Breakpoint feinjustieren

**Files:**
- Modify (nur falls Breakpoint angepasst werden muss): `dashboard/src/styles/_variables.scss`

**Interfaces:**
- Consumes: Task 1.
- Produces: bestätigt die Verify-Matrix in `_tickets/T-05-responsive-header-mobile.md` (#1–#4); ggf. finaler `$header-bp`-Wert.

- [ ] **Step 1: Desktop-Regression prüfen**

Stack läuft (`make dev-up`). Browser bei **≥1024px** (`#/assets`): Header wie bisher — Logo links, 7 Tabs in einer Zeile, DE/EN rechts, **keine** Überlappung, **kein** ☰. → T-05 #4

- [ ] **Step 2: Übergangsbereich prüfen (der eigentliche Bug)**

Fensterbreite langsam von ~1200px auf ~360px verkleinern. Look for: An **keiner** Breite überlappen Logo/Nav/Sprache. Bei ≥1024px die volle Tab-Zeile, unter 1024px der ☰. Der konventionelle 1024px-Breakpoint liegt über dem Überlaufpunkt der 7 Tabs — es sollte **keine** Überlappung geben. Nur falls wider Erwarten doch (sehr lange Labels o.ä.): kurz notieren, nicht raten. → T-05 #1

- [ ] **Step 3: Mobile-Funktion prüfen (~375px)**

- ☰ sichtbar; Klick öffnet den Drawer mit **allen 7 Tabs** (Icon + Label). → T-05 #2
- Tab-Klick navigiert **und** schließt den Drawer; Klick auf Backdrop schließt; Escape schließt.
- Sprachumschalter DE/EN in der Kopfzeile sichtbar und bedienbar; DE/EN umschalten → „Menü"/„Menu" am ☰-aria-label. → T-05 #3

- [ ] **Step 4: Matrix nachtragen + ggf. Commit**

AI-Spalte in `_tickets/T-05-responsive-header-mobile.md` (#1–#4) mit Evidenz füllen (Legende ✅/⚠️/◑/➖), Human-Spalte frei lassen.
Falls `$header-bp` angepasst wurde:
```bash
git add dashboard/src/styles/_variables.scss
git commit -m "fix(dashboard): Header-Breakpoint an Tab-Zeilenbreite angepasst"
```

---

## Self-Review

**Spec coverage:**
- Hamburger-Drawer unter Breakpoint, Desktop unverändert → Task 1 (Template/CSS). ✓
- Toggle-State, Escape, Klick-außerhalb (Backdrop), Auswahl-schließt → Task 1 (`isOpen`, `selectTab`, `onKeydown`, `.backdrop`). ✓
- a11y (`aria-label`/`aria-expanded`/`aria-controls`, `<nav>`-Landmark) → Task 1 Template. ✓
- i18n `nav.menu` DE+EN, sonst kein neuer Text → Task 1 Step 2 + Global Constraints. ✓
- DRY: 7 Tabs einmalig → ein `<nav v-for>`, per `.open`-Klasse Desktop/Drawer. ✓
- Breakpoint konventionell (1024px, Tailwind lg / Material), nicht geschätzt; im Browser verifiziert → `$header-bp` + Task 2. ✓
- Tests (Toggle/Escape/navigate) vitest; responsive im Browser → Task 1 Spec + Task 2. ✓
- Kein Backend-Change → keine Task berührt Backend. ✓

**Placeholder scan:** kein TBD/TODO; jeder Code-Step enthält konkreten Code bzw. konkretes Kommando. ✓

**Type consistency:** `selectTab(key: TabKey)`, `onKeydown(event: KeyboardEvent)`, `isOpen: Ref<boolean>`, Klasse `.nav-tabs`/`.open`/`.hamburger`/`.backdrop`, id `mobile-nav`, Key `nav.menu`, Var `$header-bp` — durchgängig gleich in Plan-Steps und Tests. ✓
