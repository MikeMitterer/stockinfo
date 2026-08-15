# T-11a — Navigation entrümpeln + Einstellungsseite — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Das Dashboard-Hauptmenü auf vier Arbeitsbereiche reduzieren und Config/Diagnose unter eine Einstellungsseite mit adressierbaren Reitern (`#/settings?tab=…`) ziehen, Zugang über ein Zahnrad rechts in der Kopfzeile.

**Architecture:** Additiv-vor-subtraktiv. Erst das Routing-Fundament (`useHashTab` parst/schreibt einen `?tab=`-Query, gibt `{ tab, settingsTab }` zurück), dann die neue `SettingsPanel.vue` (hängt die bestehenden Panels + einen kleinen Sprach-Block ein), dann Verdrahtung in `App.vue`, dann der Umbau der Kopfzeile (4 Tabs, Zahnrad statt DE/EN), zuletzt die subtraktive Bereinigung von `TabKey`/`TABS`/toten Zweigen mit vollem Typecheck. So bleibt die App nach jedem Task lauffähig und `vitest` grün.

**Tech Stack:** Vue 3 (`<script setup lang="ts">`), Vite, vue-i18n (Composition API), Vitest + @vue/test-utils, scoped SCSS mit `@use '../styles/variables' as *`.

## Global Constraints

- **i18n Pflicht:** Kein sichtbarer Text ohne Katalog-Eintrag. Jeder neue Key muss in **beiden** Katalogen stehen — `src/i18n/de.ts` (Schema-Quelle, `MessageSchema = typeof de`) **und** `src/i18n/en.ts`; fehlt einer, brechen die Typen.
- **Deutsch ist Basissprache**, Englisch zieht nach.
- **Erst-Besuch-Default = Browser-Sprache (unverändert lassen):** `detectLocale()` (`src/i18n/index.ts:24`) bleibt unangetastet — localStorage → `navigator.language` (`de*` → Deutsch, sonst `en`). T-11a verschiebt nur den Umschalter, ändert die Erkennung nicht.
- **Scoped SCSS + BEM** (`block__element--modifier`), sprechende Klassennamen, keine Utility-Ketten. Bestehende SCSS-Variablen aus `styles/variables` verwenden (`$color-*`, `$radius`, `$brand-gradient`, `$header-*`). **Keine** neuen CSS-Custom-Property-Token-Aliase — das ist T-11b.
- **Aktiv-Markierung messungsfrei:** Reiter-/Tab-Markierung ist ein per-Item-CSS-Unterstrich am aktiven Element, **kein** positionsberechneter Slider (sonst verrutscht er beim Sprachwechsel).
- **Testlauf:** `npm test` (= `vitest run`) im Ordner `dashboard/`. Typecheck: `npm run build` (= `vue-tsc -b && vite build`).
- **Arbeitsverzeichnis:** alle Pfade relativ zu `dashboard/`.
- **Panels werden nur verschoben, nicht umgebaut** (kein visueller Redesign in T-11a).

---

### Task 1: Routing-Fundament — Typen + `useHashTab` mit Query-Parsing

**Files:**
- Modify: `dashboard/src/types.ts:91-94` (TabKey/NavIconName + neuer SettingsTab)
- Modify: `dashboard/src/composables/useHashTab.ts` (komplett neu geschrieben)
- Modify: `dashboard/src/App.vue:53` (Destructuring `{ tab: activeTab }`)
- Test: `dashboard/tests/composables/useHashTab.spec.ts` (neu geschrieben)

**Interfaces:**
- Produces:
  - `type SettingsTab = 'appearance' | 'language' | 'links' | 'environment'` (in `types.ts`)
  - `TabKey` erweitert um `'settings'` (Superset, alte Werte bleiben in diesem Task)
  - `useHashTab(): { tab: Ref<TabKey>; settingsTab: Ref<SettingsTab> }`
  - Exporte aus `useHashTab.ts`: `SETTINGS_TABS: SettingsTab[]`, `DEFAULT_SETTINGS_TAB: SettingsTab`

- [ ] **Step 1: Typen ergänzen** — in `dashboard/src/types.ts` die Zeilen 90-94 ersetzen:

```ts
/** Aktive Unterseite/Tab des Dashboards. */
export type TabKey =
  | 'assets'
  | 'exchanges'
  | 'environment'
  | 'links'
  | 'themes'
  | 'analysis'
  | 'fx'
  | 'settings'

/** Reiter innerhalb der Einstellungsseite (adressierbar via #/settings?tab=…). */
export type SettingsTab = 'appearance' | 'language' | 'links' | 'environment'

/** Bekannte Icon-Namen der Navigation (deckungsgleich mit den Tabs). */
export type NavIconName = TabKey
```

- [ ] **Step 2: Failing test schreiben** — `dashboard/tests/composables/useHashTab.spec.ts` komplett ersetzen:

```ts
import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import { defineComponent, nextTick, type Ref } from 'vue'

import { useHashTab } from '../../src/composables/useHashTab'
import type { SettingsTab, TabKey } from '../../src/types'

afterEach(() => {
  window.location.hash = ''
})

/** Mountet das Composable in einer Minimal-Komponente (für onMounted/onUnmounted). */
function mountHashTab(): {
  tab: Ref<TabKey>
  settingsTab: Ref<SettingsTab>
  unmount: () => void
} {
  let api!: { tab: Ref<TabKey>; settingsTab: Ref<SettingsTab> }
  const wrapper = mount(
    defineComponent({
      setup() {
        api = useHashTab()
        return () => null
      },
    }),
  )
  return { tab: api.tab, settingsTab: api.settingsTab, unmount: () => wrapper.unmount() }
}

describe('useHashTab', () => {
  it('liefert Default-Tab und Default-Reiter ohne Hash', () => {
    const { tab, settingsTab, unmount } = mountHashTab()
    expect(tab.value).toBe('assets')
    expect(settingsTab.value).toBe('appearance')
    unmount()
  })

  it('liest einen gültigen Tab aus dem Hash', () => {
    window.location.hash = '#/exchanges'
    const { tab, unmount } = mountHashTab()
    expect(tab.value).toBe('exchanges')
    unmount()
  })

  it('fällt bei unbekanntem Hash auf den Default zurück', () => {
    window.location.hash = '#/unbekannt'
    const { tab, unmount } = mountHashTab()
    expect(tab.value).toBe('assets')
    unmount()
  })

  it('schreibt Tab-Wechsel in den Hash', async () => {
    const { tab, unmount } = mountHashTab()
    tab.value = 'fx'
    await nextTick()
    expect(window.location.hash).toBe('#/fx')
    unmount()
  })

  it('parst den Settings-Reiter aus der Query', () => {
    window.location.hash = '#/settings?tab=environment'
    const { tab, settingsTab, unmount } = mountHashTab()
    expect(tab.value).toBe('settings')
    expect(settingsTab.value).toBe('environment')
    unmount()
  })

  it('fällt bei unbekanntem Reiter auf appearance zurück', () => {
    window.location.hash = '#/settings?tab=bogus'
    const { tab, settingsTab, unmount } = mountHashTab()
    expect(tab.value).toBe('settings')
    expect(settingsTab.value).toBe('appearance')
    unmount()
  })

  it('schreibt den Reiter als Query, wenn tab === settings', async () => {
    const { tab, settingsTab, unmount } = mountHashTab()
    tab.value = 'settings'
    settingsTab.value = 'links'
    await nextTick()
    expect(window.location.hash).toBe('#/settings?tab=links')
    unmount()
  })

  it('lässt die Query weg, wenn zu einem Arbeitsbereich gewechselt wird', async () => {
    window.location.hash = '#/settings?tab=links'
    const { tab, unmount } = mountHashTab()
    await nextTick()
    tab.value = 'assets'
    await nextTick()
    expect(window.location.hash).toBe('#/assets')
    unmount()
  })
})
```

- [ ] **Step 3: Test rot laufen lassen**

Run: `cd dashboard && npx vitest run tests/composables/useHashTab.spec.ts`
Expected: FAIL (`useHashTab(...).tab` undefined / falscher Rückgabetyp)

- [ ] **Step 4: `useHashTab.ts` neu implementieren** — Datei komplett ersetzen:

```ts
import { onMounted, onUnmounted, ref, watch, type Ref } from 'vue'

import type { SettingsTab, TabKey } from '../types'

const TABS: TabKey[] = [
  'assets',
  'exchanges',
  'environment',
  'links',
  'themes',
  'analysis',
  'fx',
  'settings',
]
const DEFAULT_TAB: TabKey = 'assets'

export const SETTINGS_TABS: SettingsTab[] = ['appearance', 'language', 'links', 'environment']
export const DEFAULT_SETTINGS_TAB: SettingsTab = 'appearance'

interface HashRoute {
  tab: TabKey
  settingsTab: SettingsTab
}

/** Zerlegt die Hash-Route in Tab und (bei settings) Reiter — z.B. "#/settings?tab=language". */
function parseHash(): HashRoute {
  const raw = window.location.hash.replace(/^#\/?/, '')
  const [tabPart, queryPart = ''] = raw.split('?')
  const tab = (TABS as string[]).includes(tabPart) ? (tabPart as TabKey) : DEFAULT_TAB
  const rawSettingsTab = new URLSearchParams(queryPart).get('tab') ?? ''
  const settingsTab = (SETTINGS_TABS as string[]).includes(rawSettingsTab)
    ? (rawSettingsTab as SettingsTab)
    : DEFAULT_SETTINGS_TAB
  return { tab, settingsTab }
}

/** Baut die Hash-Route: bei settings mit ?tab=<reiter>, sonst schlicht #/<tab>. */
function toHash(tab: TabKey, settingsTab: SettingsTab): string {
  return tab === 'settings' ? `#/settings?tab=${settingsTab}` : `#/${tab}`
}

/**
 * Aktiver Tab + Settings-Reiter, synchron mit einer deep-linkbaren Hash-Route.
 * Einzige Stelle, die die URL-Struktur besitzt.
 */
export function useHashTab(): { tab: Ref<TabKey>; settingsTab: Ref<SettingsTab> } {
  const initial = parseHash()
  const tab = ref<TabKey>(initial.tab)
  const settingsTab = ref<SettingsTab>(initial.settingsTab)

  function onHashChange(): void {
    const route = parseHash()
    tab.value = route.tab
    settingsTab.value = route.settingsTab
  }

  watch([tab, settingsTab], ([t, s]) => {
    const next = toHash(t, s)
    if (window.location.hash !== next) {
      window.location.hash = next
    }
  })

  onMounted(() => {
    if (!window.location.hash) {
      window.location.hash = toHash(tab.value, settingsTab.value)
    }
    window.addEventListener('hashchange', onHashChange)
  })

  onUnmounted(() => window.removeEventListener('hashchange', onHashChange))

  return { tab, settingsTab }
}
```

- [ ] **Step 5: `App.vue` an den neuen Rückgabewert anpassen** — Zeile 53 ändern:

```ts
// vorher: const activeTab = useHashTab()
const { tab: activeTab } = useHashTab()
```

(Der Rest von `App.vue` bleibt in diesem Task unverändert; `activeTab` ist weiter ein `Ref<TabKey>`.)

- [ ] **Step 6: Tests grün laufen lassen**

Run: `cd dashboard && npx vitest run tests/composables/useHashTab.spec.ts`
Expected: PASS (8 Tests)

- [ ] **Step 7: Commit**

```bash
git add dashboard/src/types.ts dashboard/src/composables/useHashTab.ts dashboard/src/App.vue dashboard/tests/composables/useHashTab.spec.ts
git commit -m "feat(dashboard): useHashTab parst adressierbare Settings-Reiter (T-11a)"
```

---

### Task 2: `SettingsPanel.vue` + i18n-Keys

**Files:**
- Create: `dashboard/src/components/SettingsPanel.vue`
- Modify: `dashboard/src/i18n/de.ts` (nav.settings + settings-Block)
- Modify: `dashboard/src/i18n/en.ts` (nav.settings + settings-Block)
- Test: `dashboard/tests/components/SettingsPanel.spec.ts` (neu)

**Interfaces:**
- Consumes: `SettingsTab`, `SETTINGS_TABS` (aus Task 1); `EnvInfo` (types.ts); `LOCALES`, `setLanguage` (i18n)
- Produces: `SettingsPanel` mit Props `{ tab: SettingsTab; env: EnvInfo | null }`, Emit `update:tab(tab: SettingsTab)` → im Parent per `v-model:tab` nutzbar.

- [ ] **Step 1: i18n-Keys ergänzen (de.ts)** — in `dashboard/src/i18n/de.ts` im `nav`-Block (nach `menu:`) einfügen:

```ts
    settings: 'Einstellungen',
```

und nach dem `language`-Block (nach dessen schließender `},`) einen neuen Top-Level-Block einfügen:

```ts
  settings: {
    title: 'Einstellungen',
    tab: {
      appearance: 'Darstellung',
      language: 'Sprache',
      links: 'API & Links',
      environment: 'Environment',
    },
    language: {
      hint:
        'Ohne eigene Wahl folgt die Sprache dem Browser. Eine Auswahl hier wird ' +
        'gespeichert und beim nächsten Start wiederhergestellt.',
    },
  },
```

- [ ] **Step 2: i18n-Keys ergänzen (en.ts)** — in `dashboard/src/i18n/en.ts` im `nav`-Block (nach `menu:`) einfügen:

```ts
    settings: 'Settings',
```

und nach dem `language`-Block einen neuen Top-Level-Block einfügen:

```ts
  settings: {
    title: 'Settings',
    tab: {
      appearance: 'Appearance',
      language: 'Language',
      links: 'API & Links',
      environment: 'Environment',
    },
    language: {
      hint:
        'Without an explicit choice the language follows the browser. A selection ' +
        'here is saved and restored on next start.',
    },
  },
```

- [ ] **Step 3: Failing test schreiben** — `dashboard/tests/components/SettingsPanel.spec.ts`:

```ts
import { shallowMount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'

import SettingsPanel from '../../src/components/SettingsPanel.vue'
import { i18n } from '../../src/i18n'

function mountPanel(tab: 'appearance' | 'language' | 'links' | 'environment' = 'appearance') {
  return shallowMount(SettingsPanel, {
    props: { tab, env: null },
    global: { plugins: [i18n] },
  })
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
})

describe('SettingsPanel', () => {
  it('rendert vier Reiter in der Reihenfolge Darstellung, Sprache, Links, Environment', () => {
    const wrapper = mountPanel()
    const labels = wrapper.findAll('.settings__tab').map((b) => b.text())
    expect(labels).toEqual(['Darstellung', 'Sprache', 'API & Links', 'Environment'])
  })

  it('markiert den aktiven Reiter', () => {
    const wrapper = mountPanel('language')
    const active = wrapper.findAll('.settings__tab').filter((b) => b.classes('active'))
    expect(active).toHaveLength(1)
    expect(active[0].text()).toBe('Sprache')
  })

  it('emittiert update:tab beim Klick auf einen Reiter', async () => {
    const wrapper = mountPanel('appearance')
    const linksTab = wrapper.findAll('.settings__tab').find((b) => b.text() === 'API & Links')!
    await linksTab.trigger('click')
    expect(wrapper.emitted('update:tab')?.[0]).toEqual(['links'])
  })

  it('setzt die Sprache über den Sprach-Block und behält die Reiter-Markierung', async () => {
    const wrapper = mountPanel('language')
    const enBtn = wrapper.findAll('.lang-choice__btn').find((b) => b.text() === 'Englisch')!
    await enBtn.trigger('click')
    expect(i18n.global.locale.value).toBe('en')
    // Marker bleibt auf dem Sprach-Reiter (messungsfrei, aus der tab-Prop abgeleitet)
    const active = wrapper.findAll('.settings__tab').filter((b) => b.classes('active'))
    expect(active).toHaveLength(1)
  })
})
```

- [ ] **Step 4: Test rot laufen lassen**

Run: `cd dashboard && npx vitest run tests/components/SettingsPanel.spec.ts`
Expected: FAIL (SettingsPanel existiert nicht)

- [ ] **Step 5: `SettingsPanel.vue` implementieren**

```vue
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { LOCALES, setLanguage } from '../i18n'
import { SETTINGS_TABS } from '../composables/useHashTab'
import type { EnvInfo, SettingsTab } from '../types'
import EnvironmentPanel from './EnvironmentPanel.vue'
import LinksPanel from './LinksPanel.vue'
import ThemesPanel from './ThemesPanel.vue'

defineProps<{ tab: SettingsTab; env: EnvInfo | null }>()

const emit = defineEmits<{
  (event: 'update:tab', tab: SettingsTab): void
}>()

const { t, locale } = useI18n()
</script>

<template>
  <section class="settings">
    <h2 class="settings__title">{{ t('settings.title') }}</h2>

    <nav class="settings__tabs" role="tablist" :aria-label="t('settings.title')">
      <button
        v-for="key in SETTINGS_TABS"
        :key="key"
        class="settings__tab"
        :class="{ active: key === tab, 'settings__tab--diag': key === 'environment' }"
        role="tab"
        :aria-selected="key === tab"
        @click="emit('update:tab', key)"
      >
        {{ t(`settings.tab.${key}`) }}
      </button>
    </nav>

    <div class="settings__body">
      <ThemesPanel v-if="tab === 'appearance'" />

      <div v-else-if="tab === 'language'" class="settings__lang">
        <p class="settings__hint">{{ t('settings.language.hint') }}</p>
        <div class="lang-choice" role="group" :aria-label="t('language.title')">
          <button
            v-for="lang in LOCALES"
            :key="lang"
            class="lang-choice__btn"
            :class="{ active: locale === lang }"
            @click="setLanguage(lang)"
          >
            {{ t(`language.${lang}`) }}
          </button>
        </div>
      </div>

      <LinksPanel v-else-if="tab === 'links'" />

      <EnvironmentPanel v-else-if="tab === 'environment'" :env="env" />
    </div>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.settings {
  &__title {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0 0 1rem;
  }

  &__tabs {
    display: flex;
    gap: 0.25rem;
    border-bottom: 1px solid $color-border;
    margin-bottom: 1.25rem;
  }

  &__tab {
    background: transparent;
    border: none;
    color: $color-muted;
    padding: 0.5rem 0.9rem;
    border-radius: $radius $radius 0 0;
    white-space: nowrap;
    position: relative;
    cursor: pointer;

    &:hover { color: $color-text; }

    &.active {
      color: $color-text;

      // messungsfreier Unterstrich am aktiven Reiter — verrutscht nicht beim Sprachwechsel
      &::after {
        content: '';
        position: absolute;
        left: 0.9rem;
        right: 0.9rem;
        bottom: -1px;
        height: 2px;
        background: $brand-gradient;
        border-radius: 2px;
      }
    }

    // Diagnose-Reiter (Environment) sichtbar abgesetzt ganz rechts
    &--diag { margin-left: auto; }
  }

  &__hint {
    color: $color-muted;
    font-size: 0.875rem;
    margin: 0 0 0.75rem;
  }
}

.lang-choice {
  display: inline-flex;
  gap: 2px;
  padding: 3px;
  border-radius: $radius;
  background: $color-surface;
  border: 1px solid $color-border;

  &__btn {
    background: transparent;
    border: none;
    color: $color-muted;
    padding: 0.35rem 0.8rem;
    border-radius: 7px;
    cursor: pointer;

    &:hover { color: $color-text; }
    &.active { color: #fff; background: $brand-gradient; }
  }
}
</style>
```

- [ ] **Step 6: Tests grün laufen lassen**

Run: `cd dashboard && npx vitest run tests/components/SettingsPanel.spec.ts`
Expected: PASS (4 Tests)

- [ ] **Step 7: Commit**

```bash
git add dashboard/src/components/SettingsPanel.vue dashboard/src/i18n/de.ts dashboard/src/i18n/en.ts dashboard/tests/components/SettingsPanel.spec.ts
git commit -m "feat(dashboard): SettingsPanel mit adressierbaren Reitern (T-11a)"
```

---

### Task 3: `SettingsPanel` in `App.vue` verdrahten

**Files:**
- Modify: `dashboard/src/App.vue` (Import, `settingsTab` aus `useHashTab`, settings-Zweig)

**Interfaces:**
- Consumes: `useHashTab()` liefert `{ tab, settingsTab }` (Task 1); `SettingsPanel` mit `v-model:tab` + `:env` (Task 2)
- Produces: `#/settings` rendert die echte Einstellungsseite (alle vier Reiter erreichbar).

- [ ] **Step 1: Import ergänzen** — in `dashboard/src/App.vue` bei den Komponenten-Imports (alphabetisch bei den anderen Panels):

```ts
import SettingsPanel from './components/SettingsPanel.vue'
```

- [ ] **Step 2: `settingsTab` aus `useHashTab` holen** — Zeile 53 erweitern:

```ts
// vorher: const { tab: activeTab } = useHashTab()
const { tab: activeTab, settingsTab } = useHashTab()
```

- [ ] **Step 3: settings-Zweig einhängen** — im `<main>` **vor** `<ThemesPanel v-else />` (also nach der `FxPanel`-Zeile, aktuell Zeile 189) einfügen:

```vue
    <SettingsPanel
      v-else-if="activeTab === 'settings'"
      v-model:tab="settingsTab"
      :env="env"
    />
```

- [ ] **Step 4: Manuell prüfen (kein neuer Unit-Test hier)** — Bestehende Suite darf nicht brechen:

Run: `cd dashboard && npm test`
Expected: PASS (alle bestehenden Tests grün; `App.vue` kompiliert)

- [ ] **Step 5: Commit**

```bash
git add dashboard/src/App.vue
git commit -m "feat(dashboard): #/settings rendert SettingsPanel (T-11a)"
```

---

### Task 4: Kopfzeile umbauen — 4 Arbeitsbereiche, Zahnrad statt DE/EN

**Files:**
- Modify: `dashboard/src/components/NavIcon.vue` (Zahnrad-Icon `settings`)
- Modify: `dashboard/src/components/AppHeader.vue` (tabs auf 4, DE/EN raus, Zahnrad-Button)
- Test: `dashboard/tests/components/AppHeader.spec.ts` (angepasst)

**Interfaces:**
- Consumes: `NavIcon name="settings"`; `t('nav.settings')`; Emit `navigate('settings')`
- Produces: Hauptmenü = `assets`, `exchanges`, `fx`, `analysis`; Zahnrad rechts navigiert zu `settings`.

- [ ] **Step 1: Zahnrad-Icon in `NavIcon.vue`** — `KNOWN_ICONS` (Zeile 7) um `'settings'` ergänzen:

```ts
const KNOWN_ICONS: NavIconName[] = ['assets', 'environment', 'links', 'exchanges', 'themes', 'analysis', 'fx', 'settings']
```

und im Template **vor** dem `v-else`-Fallback (nach dem `fx`-Zweig) einfügen:

```vue
    <template v-else-if="name === 'settings'">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </template>
```

- [ ] **Step 2: Failing test schreiben** — `dashboard/tests/components/AppHeader.spec.ts` komplett ersetzen:

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

describe('AppHeader', () => {
  it('rendert genau vier Arbeitsbereiche in fester Reihenfolge', () => {
    const wrapper = mountHeader()
    const labels = wrapper.findAll('.nav-tabs .tab span').map((s) => s.text())
    expect(labels).toEqual(['Assets', 'Börsen', 'Devisen', 'Analyse'])
  })

  it('zeigt keinen Sprach-Umschalter mehr in der Kopfzeile', () => {
    const wrapper = mountHeader()
    expect(wrapper.find('.lang').exists()).toBe(false)
  })

  it('rendert ein Zahnrad, das zu settings navigiert', async () => {
    const wrapper = mountHeader()
    const gear = wrapper.find('.settings-btn')
    expect(gear.exists()).toBe(true)
    expect(gear.attributes('aria-label')).toBe('Einstellungen')
    await gear.trigger('click')
    expect(wrapper.emitted('navigate')?.[0]).toEqual(['settings'])
  })

  it('öffnet den Drawer per Hamburger und schließt ihn bei Tab-Auswahl', async () => {
    const wrapper = mountHeader()
    await wrapper.find('.hamburger').trigger('click')
    expect(wrapper.find('.nav-tabs').classes()).toContain('open')

    const tabButtons = wrapper.findAll('.nav-tabs .tab')
    expect(tabButtons).toHaveLength(4)
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

- [ ] **Step 3: Test rot laufen lassen**

Run: `cd dashboard && npx vitest run tests/components/AppHeader.spec.ts`
Expected: FAIL (7 Tabs statt 4, `.lang` noch da, `.settings-btn` fehlt)

- [ ] **Step 4: `AppHeader.vue` umbauen**

Script-Teil — Import und `tabs` ändern, DE/EN-Import raus:

```ts
// vorher: import { LOCALES, setLanguage } from '../i18n'
// (Zeile entfernen)

// vorher: const { t, locale } = useI18n()
const { t } = useI18n()

const tabs = computed<{ key: TabKey; label: string; icon: NavIconName }[]>(() => [
  { key: 'assets', label: t('nav.assets'), icon: 'assets' },
  { key: 'exchanges', label: t('nav.exchanges'), icon: 'exchanges' },
  { key: 'fx', label: t('nav.fx'), icon: 'fx' },
  { key: 'analysis', label: t('nav.analysis'), icon: 'analysis' },
])
```

Template — den kompletten `.lang`-Block (aktuell Zeilen 75-86) durch den Zahnrad-Button ersetzen:

```vue
    <button
      class="settings-btn"
      :class="{ active: active === 'settings' }"
      :title="t('nav.settings')"
      :aria-label="t('nav.settings')"
      @click="emit('navigate', 'settings')"
    >
      <NavIcon name="settings" />
    </button>
```

Style — den `.lang { … }`-Block (Zeilen 168-188) durch `.settings-btn` ersetzen und in der Media-Query `.lang { margin-left: auto; }` (Zeile 216) auf `.settings-btn` umstellen:

```scss
  .settings-btn {
    display: inline-flex;
    align-items: center;
    background: transparent;
    border: none;
    color: $color-muted;
    padding: 0.4rem 0.5rem;
    border-radius: $radius;
    cursor: pointer;

    &:hover { color: $color-text; background: $color-surface-2; }
    &.active { color: $color-text; background: $color-surface; }
  }
```

```scss
  @media (max-width: $header-bp) {
    // … unverändert …
    // vorher: .lang { margin-left: auto; }
    .settings-btn { margin-left: auto; }
    // … unverändert …
  }
```

- [ ] **Step 5: Tests grün laufen lassen**

Run: `cd dashboard && npx vitest run tests/components/AppHeader.spec.ts`
Expected: PASS (6 Tests)

- [ ] **Step 6: Commit**

```bash
git add dashboard/src/components/NavIcon.vue dashboard/src/components/AppHeader.vue dashboard/tests/components/AppHeader.spec.ts
git commit -m "feat(dashboard): Hauptmenü auf 4 Arbeitsbereiche + Zahnrad statt DE/EN (T-11a)"
```

---

### Task 5: Subtraktive Bereinigung + voller Typecheck

**Files:**
- Modify: `dashboard/src/types.ts` (TabKey ohne themes/environment/links)
- Modify: `dashboard/src/composables/useHashTab.ts` (TABS-Whitelist kürzen)
- Modify: `dashboard/src/components/NavIcon.vue` (tote Icon-Zweige + KNOWN_ICONS)
- Modify: `dashboard/src/App.vue` (tote v-if-Zweige + Imports)

**Interfaces:**
- Consumes: alles aus Tasks 1-4.
- Produces: finaler, konsistenter `TabKey = assets | exchanges | analysis | fx | settings`; sauberer `vue-tsc`-Typecheck.

- [ ] **Step 1: `TabKey` bereinigen** — in `dashboard/src/types.ts` `themes`, `environment`, `links` aus dem Union entfernen:

```ts
/** Aktive Unterseite/Tab des Dashboards. */
export type TabKey = 'assets' | 'exchanges' | 'analysis' | 'fx' | 'settings'
```

(`SettingsTab` und `NavIconName = TabKey` bleiben unverändert.)

- [ ] **Step 2: `TABS`-Whitelist kürzen** — in `dashboard/src/composables/useHashTab.ts`:

```ts
const TABS: TabKey[] = ['assets', 'exchanges', 'analysis', 'fx', 'settings']
```

- [ ] **Step 3: `NavIcon.vue` bereinigen** — `KNOWN_ICONS` auf die tatsächlich genutzten Namen kürzen:

```ts
const KNOWN_ICONS: NavIconName[] = ['assets', 'exchanges', 'analysis', 'fx', 'settings']
```

und die drei nun toten Template-Zweige entfernen: `v-else-if="name === 'environment'"`, `v-else-if="name === 'links'"`, `v-else-if="name === 'themes'"` (die zugehörigen `<template>`-Blöcke). `assets`, `exchanges`, `analysis`, `fx`, `settings` und der `v-else`-Fallback bleiben.

- [ ] **Step 4: `App.vue` bereinigen** — die drei toten Zweige und den `v-else`-Fallback entfernen; die drei jetzt in `SettingsPanel` gekapselten Imports entfernen.

Entfernen aus dem Template (Zeilen 186, 187, 190):

```vue
    <EnvironmentPanel v-else-if="activeTab === 'environment'" :env="env" />
    <LinksPanel v-else-if="activeTab === 'links'" />
    <ThemesPanel v-else />
```

Entfernen aus den Imports:

```ts
import EnvironmentPanel from './components/EnvironmentPanel.vue'
import LinksPanel from './components/LinksPanel.vue'
import ThemesPanel from './components/ThemesPanel.vue'
```

Danach endet die `v-if`-Kette im `<main>` mit dem `SettingsPanel`-Zweig; `activeTab` ist durch die `TABS`-Validierung immer eines der fünf gültigen Ziele. Der `<main>`-Block sieht dann so aus:

```vue
  <main class="content" :class="{ 'with-dock': selectedItem && activeTab === 'assets' }">
    <ErrorBanner :errors="errors" @dismiss="dismissError" />
    <template v-if="activeTab === 'assets'">
      <Toolbar :refreshing="refreshing" :busy="busy" @refresh="onRefreshAll" @add="onAdd" />
      <InstrumentsTable
        :instruments="instruments"
        :selected-symbol="selectedSymbol"
        :refreshing-symbol="refreshingSymbol"
        :extraetf-etf-url="env?.extraetf_etf_url ?? ''"
        :extraetf-stock-url="env?.extraetf_stock_url ?? ''"
        :yahoo-url="env?.yahoo_url ?? ''"
        @select="select"
        @refresh="onRefreshOne"
        @remove="onRemove"
        @set-isin="onSetIsin"
        @json="jsonItem = $event"
      />
    </template>

    <ExchangesPanel v-else-if="activeTab === 'exchanges'" :data="exchanges" />
    <AnalysisPanel v-else-if="activeTab === 'analysis'" :instruments="instruments" />
    <FxPanel v-else-if="activeTab === 'fx'" :currencies="fxCurrencies" />
    <SettingsPanel v-else-if="activeTab === 'settings'" v-model:tab="settingsTab" :env="env" />
  </main>
```

- [ ] **Step 5: Voller Typecheck + Testlauf**

Run: `cd dashboard && npm run build && npm test`
Expected: `vue-tsc` ohne Fehler, `vite build` erfolgreich, alle Vitest-Tests grün. (Falls `vue-tsc` einen verbliebenen Verweis auf `'themes' | 'environment' | 'links'` als TabKey meldet, dort auf den finalen Union anpassen.)

- [ ] **Step 6: Commit**

```bash
git add dashboard/src/types.ts dashboard/src/composables/useHashTab.ts dashboard/src/components/NavIcon.vue dashboard/src/App.vue
git commit -m "refactor(dashboard): TabKey auf finale Arbeitsbereiche + Settings bereinigt (T-11a)"
```

---

## Nach dem Plan: Verifikation & Ticket

Nicht Teil der TDD-Tasks, aber vor „fertig":

- **Browser-Verifikation (Verify-Matrix des Teil-Tickets T-11a):** Stack `make dev-up` (Backend `:8000`, Dashboard `:5173`).
  - Hauptmenü zeigt genau 4 Punkte (Assets, Börsen, Devisen, Analyse); kein DE/EN in der Kopfzeile.
  - Zahnrad rechts öffnet die Einstellungsseite.
  - Reiter direkt per URL: `http://localhost:5173/#/settings?tab=environment` lädt den Environment-Reiter; analog `?tab=appearance|language|links`.
  - Sprache im Sprach-Reiter umschalten → wirkt app-weit; Aktiv-Markierung bleibt auf „Sprache"; Hauptnav-Markierung stimmt nach dem Sprachwechsel.
  - Erst-Besuch (localStorage `stockinfo-lang` löschen, Reload) → Sprache folgt dem Browser.
  - Unter 768 px kein waagrechtes Scrollen; Desktop unverändert.
- **Teil-Ticket-Files anlegen** (`_tickets/T-11a…e`) via Skill `task-verification-workflow` — T-11a mit ausgefüllter Verify-Matrix (AI-Spalte nach der Browser-Runde), T-11b…e als Backlog-Stubs. T-11 (Epic) bleibt offen, bis alle Teile in `solved/`.

## Self-Review

**Spec coverage:**
- Nav 4 Arbeitsbereiche (Assets, Börsen, Devisen, Analyse) → Task 4. ✓
- Zahnrad rechts statt Menüpunkt → Task 4. ✓
- DE/EN aus Kopfzeile → Task 4. ✓
- SettingsPanel, Reiter-Reihenfolge Darstellung→Sprache→Links→Environment, Environment abgesetzt → Task 2. ✓
- Panels wiederverwendet, nur Sprache neu → Task 2. ✓
- `useHashTab` `{ tab, settingsTab }`, Query-Parsing `#/settings?tab=…` → Task 1. ✓
- `SettingsTab`-Typ in types.ts → Task 1. ✓
- Erst-Besuch = Browser-Sprache unverändert → Global Constraints + `detectLocale` unangetastet + Verify-Punkt. ✓
- Aktiv-Markierung messungsfrei/sprachwechselfest → Task 2 (CSS ::after) + Test (Step 3, Sprach-Marker) + Constraints. ✓
- i18n beide Kataloge → Task 2. ✓
- YAGNI: kein Token/Mobil-Karten/Theme-Palette/Statusbar → nicht im Plan. ✓

**Placeholder-Scan:** keine TBD/TODO; jeder Code-Step trägt vollständigen Code. ✓

**Typkonsistenz:** `useHashTab(): { tab, settingsTab }` (Task 1) == Verbrauch in App.vue (Task 3) und SettingsPanel-Prop `tab: SettingsTab` + Emit `update:tab` == `v-model:tab` (Task 2/3). `SETTINGS_TABS` in Task 1 exportiert, in Task 2 importiert. `NavIcon name="settings"` (Task 4) nach `KNOWN_ICONS`-Ergänzung (Task 4). Finaler `TabKey` (Task 5) deckt alle in App.vue verbleibenden Zweige (assets/exchanges/analysis/fx/settings). ✓
