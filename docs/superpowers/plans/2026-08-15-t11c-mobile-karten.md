# T-11c — Assets-Tabelle mobil → Kartenliste — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unter `md` (768 px) wird die neunspaltige Assets-Tabelle zu einer Kartenliste — je Papier eine Karte mit Symbol, Typ, Kurs und Name, Rest aufklappbar — ohne waagrechtes Scrollen und ohne Funktionsverlust gegenüber der Tabelle.

**Architecture:** Ein Composable `useIsCompact` (matchMedia) hält die Umschaltung an **einer** Stelle, statt sie über CSS zu verstreuen — damit weiß die Logik, was die Darstellung tut. `InstrumentsTable.vue` entscheidet nur noch zwischen `<table>` und Kartenliste; die Karte selbst ist eine eigene Komponente. Das ISIN-Nachtrage-Formular steckt heute in einer Tabellenzelle und wird vorher in eine eigene Komponente gezogen, damit Tabelle und Karte dieselbe Logik benutzen statt zweier Kopien.

**Tech Stack:** Vue 3 (`<script setup lang="ts">`), SCSS scoped + BEM, vue-i18n, Vitest + @vue/test-utils (jsdom).

## Global Constraints

- **i18n Pflicht:** kein sichtbarer Text ohne Katalog-Eintrag, jeder neue Key in **beiden** Katalogen (`src/i18n/de.ts` ist Schema-Quelle, `en.ts` zieht nach — fehlt einer, brechen die Typen).
- **Breakpoint `md` = 768 px** (Skill-Tabelle, verbindlich). Der Wert steht **einmal** im Composable, nicht in jeder Komponente.
- **Mobil voll bedienbar** (Skill): jede Handlung der Tabelle muss auf der Karte erreichbar sein — Auswahl, Aktualisieren, Löschen, JSON, externe Links, ISIN nachtragen **und Sortieren**.
- Antippbare Flächen mindestens **44 × 44 px**; was nur bei `:hover` erscheint, muss auf dem Telefon durch Antippen erreichbar sein.
- Farben/Abstände aus Token bzw. den vorhandenen SCSS-Variablen (`$color-*`, `token(--x, a)`, `$radius`) — keine neuen Literale. Die Skalen aus T-11b (`--space-*`, `--radius-*`, `--font-*`) dürfen in **neuem** CSS verwendet werden.
- Scoped SCSS, BEM (`block__element--modifier`), sprechende Klassennamen.
- Native `<select>` (Sortierung): `min-width: 0`, `max-width: 100%`, `font-size: 1rem` (unter 16 px zoomt iOS beim Antippen die ganze Seite), `option { font-family: inherit }`.
- **Desktop-Verhalten bleibt unverändert.** Ab 768 px rendert exakt die heutige Tabelle.
- Gate je Task: `npm run build` (`vue-tsc -b && vite build`) sauber **und** `npm test` grün. Vorbestehende Sass-„legacy-JS-API"-Warnung ist nicht neu.
- Arbeitsverzeichnis: `dashboard/`.

---

### Task 1: Composable `useIsCompact`

**Files:**
- Create: `dashboard/src/composables/useIsCompact.ts`
- Test: `dashboard/tests/composables/useIsCompact.spec.ts`

**Interfaces:**
- Produces: `useIsCompact(): Ref<boolean>` — `true`, solange der Viewport **schmaler als 768 px** ist. Export `COMPACT_QUERY = '(max-width: 767.98px)'`.

- [ ] **Step 1: Failing test schreiben** — `dashboard/tests/composables/useIsCompact.spec.ts`:

```ts
import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, type Ref } from 'vue'

import { COMPACT_QUERY, useIsCompact } from '../../src/composables/useIsCompact'

/** Ersetzt window.matchMedia durch eine steuerbare Attrappe. */
function stubMatchMedia(matches: boolean) {
  const listeners = new Set<(e: MediaQueryListEvent) => void>()
  const mql = {
    matches,
    media: COMPACT_QUERY,
    addEventListener: (_: string, cb: (e: MediaQueryListEvent) => void) => listeners.add(cb),
    removeEventListener: (_: string, cb: (e: MediaQueryListEvent) => void) => listeners.delete(cb),
  }
  const spy = vi.fn().mockReturnValue(mql)
  vi.stubGlobal('matchMedia', spy)
  return {
    spy,
    /** Simuliert einen Breitenwechsel. */
    emit(next: boolean) {
      mql.matches = next
      listeners.forEach((cb) => cb({ matches: next } as MediaQueryListEvent))
    },
    listenerCount: () => listeners.size,
  }
}

function mountCompact(): { compact: Ref<boolean>; unmount: () => void } {
  let compact!: Ref<boolean>
  const wrapper = mount(
    defineComponent({
      setup() {
        compact = useIsCompact()
        return () => null
      },
    }),
  )
  return { compact, unmount: () => wrapper.unmount() }
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('useIsCompact', () => {
  it('fragt die md-Grenze ab (unter 768px)', () => {
    const mm = stubMatchMedia(false)
    const { unmount } = mountCompact()
    expect(mm.spy).toHaveBeenCalledWith('(max-width: 767.98px)')
    unmount()
  })

  it('liefert den Anfangszustand aus matchMedia', () => {
    stubMatchMedia(true)
    const { compact, unmount } = mountCompact()
    expect(compact.value).toBe(true)
    unmount()
  })

  it('reagiert auf einen Breitenwechsel', async () => {
    const mm = stubMatchMedia(false)
    const { compact, unmount } = mountCompact()
    expect(compact.value).toBe(false)
    mm.emit(true)
    expect(compact.value).toBe(true)
    unmount()
  })

  it('meldet den Listener beim Unmount wieder ab', () => {
    const mm = stubMatchMedia(false)
    const { unmount } = mountCompact()
    expect(mm.listenerCount()).toBe(1)
    unmount()
    expect(mm.listenerCount()).toBe(0)
  })
})
```

- [ ] **Step 2: Test rot laufen lassen**

Run: `cd dashboard && npx vitest run tests/composables/useIsCompact.spec.ts`
Expected: FAIL (Modul existiert nicht)

- [ ] **Step 3: Implementieren** — `dashboard/src/composables/useIsCompact.ts`:

```ts
import { onMounted, onUnmounted, ref, type Ref } from 'vue'

/**
 * Grenze `md` aus den UX-Standards: darunter eine Spalte, Kartenliste statt
 * Tabelle. 767.98 statt 767, damit auch gebrochene Breiten (Zoom, DPR) sauber
 * kippen — ab genau 768px gilt das volle Layout.
 */
export const COMPACT_QUERY = '(max-width: 767.98px)'

/**
 * True, solange der Viewport schmaler als `md` ist. Einzige Stelle, die den
 * Umschaltpunkt kennt — die Darstellung folgt der Logik, nicht umgekehrt.
 */
export function useIsCompact(): Ref<boolean> {
  const query = window.matchMedia(COMPACT_QUERY)
  const compact = ref(query.matches)

  function onChange(event: MediaQueryListEvent): void {
    compact.value = event.matches
  }

  onMounted(() => query.addEventListener('change', onChange))
  onUnmounted(() => query.removeEventListener('change', onChange))

  return compact
}
```

- [ ] **Step 4: Test grün** — `cd dashboard && npx vitest run tests/composables/useIsCompact.spec.ts` → PASS (4)

- [ ] **Step 5: Commit**

```bash
git add dashboard/src/composables/useIsCompact.ts dashboard/tests/composables/useIsCompact.spec.ts
git commit -m "feat(dashboard): useIsCompact — md-Grenze als Composable (T-11c)"
```

---

### Task 2: ISIN-Editor herausziehen (reiner Refactor)

**Files:**
- Create: `dashboard/src/components/IsinEditor.vue`
- Modify: `dashboard/src/components/InstrumentsTable.vue` (Logik raus, Komponente rein)
- Test: `dashboard/tests/components/IsinEditor.spec.ts`

**Interfaces:**
- Produces: `IsinEditor` mit Prop `symbol: string`, Emit `save(payload: { symbol: string; isin: string })`. Kapselt Knopf „+ ISIN", Eingabe, Prüfung (`isIsin`), Bestätigen/Abbrechen, Fehlerhinweis.

**Warum zuerst:** Tabelle **und** Karte brauchen dasselbe Formular. Erst herausziehen, dann in beiden verwenden — sonst steht die Logik zweimal da und läuft auseinander.

- [ ] **Step 1: Failing test** — `dashboard/tests/components/IsinEditor.spec.ts`:

```ts
import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'

import IsinEditor from '../../src/components/IsinEditor.vue'
import { i18n } from '../../src/i18n'

function mountEditor() {
  return mount(IsinEditor, { props: { symbol: 'APC.DE' }, global: { plugins: [i18n] } })
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
})

describe('IsinEditor', () => {
  it('zeigt zunächst nur den Knopf zum Nachtragen', () => {
    const wrapper = mountEditor()
    expect(wrapper.find('.isin__add').exists()).toBe(true)
    expect(wrapper.find('.isin__input').exists()).toBe(false)
  })

  it('öffnet die Eingabe per Klick', async () => {
    const wrapper = mountEditor()
    await wrapper.find('.isin__add').trigger('click')
    expect(wrapper.find('.isin__input').exists()).toBe(true)
  })

  it('emittiert save bei gültiger ISIN', async () => {
    const wrapper = mountEditor()
    await wrapper.find('.isin__add').trigger('click')
    await wrapper.find('.isin__input').setValue('US0378331005')
    await wrapper.find('.isin__ok').trigger('click')
    expect(wrapper.emitted('save')?.[0]).toEqual([{ symbol: 'APC.DE', isin: 'US0378331005' }])
  })

  it('zeigt bei ungültiger ISIN einen Hinweis und emittiert nicht', async () => {
    const wrapper = mountEditor()
    await wrapper.find('.isin__add').trigger('click')
    await wrapper.find('.isin__input').setValue('QUATSCH')
    await wrapper.find('.isin__ok').trigger('click')
    expect(wrapper.emitted('save')).toBeUndefined()
    expect(wrapper.find('.isin__err').exists()).toBe(true)
  })

  it('normalisiert Kleinschreibung', async () => {
    const wrapper = mountEditor()
    await wrapper.find('.isin__add').trigger('click')
    await wrapper.find('.isin__input').setValue('us0378331005')
    await wrapper.find('.isin__ok').trigger('click')
    expect(wrapper.emitted('save')?.[0]).toEqual([{ symbol: 'APC.DE', isin: 'US0378331005' }])
  })
})
```

- [ ] **Step 2: Test rot** — `npx vitest run tests/components/IsinEditor.spec.ts` → FAIL

- [ ] **Step 3: `IsinEditor.vue` anlegen**

Die Logik wird **wörtlich** aus `InstrumentsTable.vue` übernommen (`editingSymbol`/`isinDraft`/`isinInvalid`, `startIsin`, `cancelIsin`, `confirmIsin`, `vFocus`) — nur auf ein einzelnes Papier verengt (statt `editingSymbol` genügt ein `editing: boolean`) und die Klassennamen auf BEM gebracht (`isin__add`, `isin__input`, `isin__ok`, `isin__cancel`, `isin__err`). Bestehende i18n-Keys weiterverwenden: `table.addIsin`, `table.isinPlaceholder`, `table.isinInvalid`, `table.save`, `table.cancel`. Enter bestätigt, Escape bricht ab. `@click.stop` am Wurzelelement, damit der Klick nicht die Zeile/Karte auswählt. Styles aus der Tabelle übernehmen (`.isin-input`, `.mini`, `.isin-err`).

- [ ] **Step 4: In der Tabelle verwenden**

In `InstrumentsTable.vue` die ISIN-Zelle ersetzen:

```vue
            <td class="mono dim isin-cell">
              <span v-if="item.isin">{{ item.isin }}</span>
              <IsinEditor v-else :symbol="item.symbol" @save="emit('set-isin', $event)" />
            </td>
```

und die nun ungenutzten Teile entfernen: Imports (`isIsin`, `watch`), Refs `editingSymbol`/`isinDraft`/`isinInvalid`, die Direktive `vFocus`, die Funktionen `startIsin`/`cancelIsin`/`confirmIsin`, sowie die zugehörigen Styles (`.isin-edit`, `.isin-input`, `.mini`, `.isin-err`) — `.isin-cell` bleibt.

- [ ] **Step 5: Gate** — `npm run build && npm test`. Alle bestehenden Tests bleiben grün; das Verhalten ist unverändert.

- [ ] **Step 6: Commit**

```bash
git add dashboard/src/components/IsinEditor.vue dashboard/src/components/InstrumentsTable.vue dashboard/tests/components/IsinEditor.spec.ts
git commit -m "refactor(dashboard): ISIN-Editor aus der Tabelle herausgezogen (T-11c)"
```

---

### Task 3: `InstrumentCard.vue`

**Files:**
- Create: `dashboard/src/components/InstrumentCard.vue`
- Modify: `dashboard/src/i18n/de.ts`, `dashboard/src/i18n/en.ts`
- Test: `dashboard/tests/components/InstrumentCard.spec.ts`

**Interfaces:**
- Consumes: `IsinEditor` (Task 2), `InstrumentSummary`.
- Produces: `InstrumentCard` mit Props `{ item: InstrumentSummary; selected: boolean; refreshing: boolean; extraetfUrl: string; yahooUrl: string }` und Emits `select`, `refresh`, `remove`, `json`, `set-isin` — dieselben Namen wie die Tabelle, damit der Elternteil nicht zwei Verdrahtungen braucht.

**Aufbau der Karte** (vom Auftraggeber festgelegt):

```
┌────────────────────────────────┐
│ APC.DE  [STOCK]     265,00 EUR │   Symbol + Typ-Badge · Kurs rechts
│ Apple Inc.                     │   Name, einzeilig gekürzt
│ ⌄ mehr        [JSON][eETF][Y!][↻][✕] │
└────────────────────────────────┘
```

Aufgeklappt kommen darunter als Beschriftung/Wert-Paare: ISIN (oder der `IsinEditor`), TER, Vola, Thes., Pkt.

- [ ] **Step 1: i18n-Keys ergänzen**

`de.ts` im `table`-Block: `more: 'mehr'`, `less: 'weniger'`, `details: 'Weitere Kennzahlen'`.
`en.ts` analog: `more: 'more'`, `less: 'less'`, `details: 'More metrics'`.

- [ ] **Step 2: Failing test** — `dashboard/tests/components/InstrumentCard.spec.ts`:

```ts
import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'

import InstrumentCard from '../../src/components/InstrumentCard.vue'
import { i18n } from '../../src/i18n'
import type { InstrumentSummary } from '../../src/types'

const item: InstrumentSummary = {
  isin: 'US0378331005', symbol: 'APC.DE', exchange: 'XETR', name: 'Apple Inc.',
  type: 'stock', currency: 'EUR', provider: null, ter: null, replication: null,
  fund_size: null, volatility: 25.8, accumulating: null, meta_fetched_at: null,
  latest_price: 265, latest_quote_time: null, latest_currency: 'EUR',
  latest_fetched_at: null, history_count: 2,
}

function mountCard(overrides: Partial<InstrumentSummary> = {}) {
  return mount(InstrumentCard, {
    props: {
      item: { ...item, ...overrides },
      selected: false, refreshing: false,
      extraetfUrl: '', yahooUrl: '',
    },
    global: { plugins: [i18n] },
  })
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
})

describe('InstrumentCard', () => {
  it('zeigt Symbol, Typ, Kurs und Name', () => {
    const wrapper = mountCard()
    expect(wrapper.find('.icard__symbol').text()).toBe('APC.DE')
    expect(wrapper.find('.icard__type').text()).toBe('stock')
    expect(wrapper.find('.icard__price').text()).toContain('265,00')
    expect(wrapper.find('.icard__name').text()).toBe('Apple Inc.')
  })

  it('hält die Kennzahlen bis zum Aufklappen verborgen', async () => {
    const wrapper = mountCard()
    expect(wrapper.find('.icard__details').exists()).toBe(false)
    await wrapper.find('.icard__toggle').trigger('click')
    expect(wrapper.find('.icard__details').exists()).toBe(true)
    expect(wrapper.find('.icard__details').text()).toContain('25.80')
  })

  it('emittiert select beim Antippen der Karte', async () => {
    const wrapper = mountCard()
    await wrapper.find('.icard__head').trigger('click')
    expect(wrapper.emitted('select')).toHaveLength(1)
  })

  it('löst beim Aufklappen kein select aus', async () => {
    const wrapper = mountCard()
    await wrapper.find('.icard__toggle').trigger('click')
    expect(wrapper.emitted('select')).toBeUndefined()
  })

  it('emittiert refresh und remove aus den Aktionen', async () => {
    const wrapper = mountCard()
    await wrapper.find('.icard__action--refresh').trigger('click')
    await wrapper.find('.icard__action--remove').trigger('click')
    expect(wrapper.emitted('refresh')).toHaveLength(1)
    expect(wrapper.emitted('remove')).toHaveLength(1)
    expect(wrapper.emitted('select')).toBeUndefined()
  })

  it('bietet den ISIN-Editor, wenn keine ISIN da ist', async () => {
    const wrapper = mountCard({ isin: null })
    await wrapper.find('.icard__toggle').trigger('click')
    expect(wrapper.find('.isin__add').exists()).toBe(true)
  })
})
```

- [ ] **Step 3: Test rot** — `npx vitest run tests/components/InstrumentCard.spec.ts` → FAIL

- [ ] **Step 4: Implementieren**

Formatierer (`price`, `formatPercent`, `accumulating`) und die Link-Bauer (`extraetfLink`, `yahooLink`) verhalten sich wie in der Tabelle — die Karte bekommt die **fertige URL** als Prop (`extraetfUrl`, `yahooUrl`), damit die Template-Auswahl (ETF vs. Stock) beim Elternteil bleibt und nicht doppelt existiert.

Wichtig:
- Klick auf `.icard__head` (Symbol/Kurs/Name) emittiert `select` → öffnet den Graph wie am Desktop.
- `.icard__toggle` und `.icard__actions` tragen `@click.stop`, sonst wählt jeder Knopf zusätzlich die Karte aus.
- `.icard__toggle` trägt `aria-expanded` und `aria-controls`; der aufgeklappte Bereich trägt die passende `id`.
- Alle Knöpfe mindestens 44 × 44 px (`min-height`/`min-width`).
- Zahlen rechtsbündig mit `font-variant-numeric: tabular-nums`.
- Ausgewählte Karte wie die ausgewählte Zeile markieren (`token(--accent, 0.12)` + Balken links).

- [ ] **Step 5: Test grün** — `npx vitest run tests/components/InstrumentCard.spec.ts` → PASS (6)

- [ ] **Step 6: Commit**

```bash
git add dashboard/src/components/InstrumentCard.vue dashboard/src/i18n dashboard/tests/components/InstrumentCard.spec.ts
git commit -m "feat(dashboard): InstrumentCard für die mobile Kartenliste (T-11c)"
```

---

### Task 4: Umschaltung + Sortierung in der Kartenansicht

**Files:**
- Modify: `dashboard/src/components/InstrumentsTable.vue`
- Modify: `dashboard/src/i18n/de.ts`, `dashboard/src/i18n/en.ts`
- Test: `dashboard/tests/components/InstrumentsTable.spec.ts` (neu, falls nicht vorhanden)

**Interfaces:**
- Consumes: `useIsCompact` (Task 1), `InstrumentCard` (Task 3), bestehendes `useTableSort`.

**Warum die Sortierung hier auftaucht:** Die Sortier-Bedienung *sind* heute die Spaltenköpfe. Ohne Ersatz verlöre die Kartenansicht das Sortieren ganz — das wäre ein Funktionsverlust, kein Umbau. Deshalb bekommt die Kartenliste eine schlanke Leiste: ein `<select>` mit den Sortierschlüsseln und ein Knopf für die Richtung.

- [ ] **Step 1: i18n-Keys ergänzen**

`de.ts` im `table`-Block: `sortBy: 'Sortieren nach'`, `sortAsc: 'Aufsteigend'`, `sortDesc: 'Absteigend'`.
`en.ts`: `sortBy: 'Sort by'`, `sortAsc: 'Ascending'`, `sortDesc: 'Descending'`.

- [ ] **Step 2: Failing test** — `dashboard/tests/components/InstrumentsTable.spec.ts`:

```ts
import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import InstrumentsTable from '../../src/components/InstrumentsTable.vue'
import { i18n } from '../../src/i18n'
import type { InstrumentSummary } from '../../src/types'

const base: InstrumentSummary = {
  isin: 'US0378331005', symbol: 'APC.DE', exchange: 'XETR', name: 'Apple Inc.',
  type: 'stock', currency: 'EUR', provider: null, ter: null, replication: null,
  fund_size: null, volatility: 25.8, accumulating: null, meta_fetched_at: null,
  latest_price: 265, latest_quote_time: null, latest_currency: 'EUR',
  latest_fetched_at: null, history_count: 2,
}
const instruments = [base, { ...base, symbol: 'VGWL.DE', name: 'Vanguard FTSE All-World' }]

/** Setzt die Viewport-Breite für useIsCompact. */
function stubMatchMedia(compact: boolean) {
  vi.stubGlobal('matchMedia', vi.fn().mockReturnValue({
    matches: compact, media: '',
    addEventListener: () => {}, removeEventListener: () => {},
  }))
}

function mountTable() {
  return mount(InstrumentsTable, {
    props: {
      instruments, selectedSymbol: null, refreshingSymbol: null,
      extraetfEtfUrl: '', extraetfStockUrl: '', yahooUrl: '',
    },
    global: { plugins: [i18n] },
  })
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('InstrumentsTable — Darstellung nach Breite', () => {
  it('zeigt ab md die Tabelle und keine Karten', () => {
    stubMatchMedia(false)
    const wrapper = mountTable()
    expect(wrapper.find('table').exists()).toBe(true)
    expect(wrapper.findAll('.icard')).toHaveLength(0)
  })

  it('zeigt unter md Karten und keine Tabelle', () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    expect(wrapper.find('table').exists()).toBe(false)
    expect(wrapper.findAll('.icard')).toHaveLength(2)
  })

  it('bietet unter md eine Sortier-Auswahl', () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    expect(wrapper.find('.tsort__select').exists()).toBe(true)
    expect(wrapper.find('.tsort__dir').exists()).toBe(true)
  })

  it('reicht select aus einer Karte nach oben durch', async () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    await wrapper.find('.icard__head').trigger('click')
    expect(wrapper.emitted('select')).toHaveLength(1)
  })

  it('zeigt den Leerzustand unabhängig von der Breite', () => {
    stubMatchMedia(true)
    const wrapper = mount(InstrumentsTable, {
      props: {
        instruments: [], selectedSymbol: null, refreshingSymbol: null,
        extraetfEtfUrl: '', extraetfStockUrl: '', yahooUrl: '',
      },
      global: { plugins: [i18n] },
    })
    expect(wrapper.find('.empty').exists()).toBe(true)
  })
})
```

- [ ] **Step 3: Test rot** — `npx vitest run tests/components/InstrumentsTable.spec.ts` → FAIL

- [ ] **Step 4: Implementieren**

In `InstrumentsTable.vue`:
- `const compact = useIsCompact()`.
- Template: `<div v-if="compact" class="cards"> … </div>` mit `v-for` über `sortedInstruments` → `<InstrumentCard>`; `<div v-else class="scroll"> <table> … </table> </div>` unverändert.
- Die fertigen URLs pro Papier an die Karte geben: `:extraetf-url="extraetfLink(item)"` und `:yahoo-url="yahooLink(item)"`.
- Emits der Karte 1:1 weiterreichen (`@select`, `@refresh`, `@remove`, `@json`, `@set-isin`).
- Sortierleiste **nur** in der Kartenansicht (`v-if="compact"`), oberhalb der Karten:
  - `<select class="tsort__select">` mit den neun `columns` (Label über `t(column.label)`), gebunden an `sortKey`;
  - `<button class="tsort__dir">` schaltet `direction` um, `:title` aus `table.sortAsc`/`table.sortDesc`, zeigt `▲`/`▼`.
  - Beides nutzt das bestehende `useTableSort` — **keine zweite Sortierlogik**.
- `.scroll { overflow-x: auto }` bleibt für die Tabelle; unter `md` gibt es keine Tabelle mehr, also auch kein waagrechtes Scrollen.

- [ ] **Step 5: Test grün** — `npx vitest run tests/components/InstrumentsTable.spec.ts` → PASS (5)

- [ ] **Step 6: Gate** — `npm run build && npm test`

- [ ] **Step 7: Commit**

```bash
git add dashboard/src dashboard/tests
git commit -m "feat(dashboard): Assets unter md als Kartenliste + Sortierleiste (T-11c)"
```

---

## Nach dem Plan: Verifikation

- **Messen statt schätzen**, bei 375 / 414 / 768 / 1024 px:
  - `document.documentElement.scrollWidth - clientWidth` muss **0** sein (unter `md` gibt es keine Tabelle mehr, die überläuft);
  - bei ≥ 768 px steht die Tabelle, bei < 768 px stehen Karten;
  - jede antippbare Fläche misst ≥ 44 px (`getBoundingClientRect()` über alle `button`/`a` in der Kartenliste).
- Aufklappen zeigt die restlichen Kennzahlen; Antippen der Karte öffnet den Graph im Dock.
- ISIN nachtragen funktioniert in beiden Darstellungen.
- Sortierung in der Kartenansicht ändert die Reihenfolge und die Richtung.
- Danach Verify-Matrix in `_tickets/T-11c-assets-tabelle-mobil-karten.md` füllen.

## Self-Review

**Spec-Coverage:** Kartenliste < md (Task 3/4) ✓ · Tabelle ≥ md unverändert (Task 4) ✓ · `useIsCompact` mit matchMedia statt verstreutem CSS (Task 1) ✓ · wichtigste Werte + Status auf der Karte (Task 3, vom Auftraggeber festgelegt) ✓ · kein waagrechtes Scrollen (Verifikation) ✓ · mobil voll bedienbar inkl. Sortierung und ISIN (Task 2/4) ✓ · i18n beidsprachig (Task 3/4) ✓ · 44 px (Task 3 + Verifikation) ✓.

**Placeholder-Scan:** keine TBD; jeder Test ist ausformuliert, jeder Schritt nennt Datei und Kommando.

**Typkonsistenz:** `useIsCompact(): Ref<boolean>` (Task 1) wird in Task 4 verbraucht. `IsinEditor` Prop `symbol` + Emit `save` (Task 2) wird in Task 2 (Tabelle) und Task 3 (Karte) gleich verwendet. `InstrumentCard`-Props/Emits (Task 3) decken sich mit der Verdrahtung in Task 4; die Karte bekommt fertige URLs, die Template-Auswahl bleibt beim Elternteil. Klassennamen der Tests (`icard__head`, `icard__toggle`, `icard__details`, `icard__action--refresh`, `tsort__select`, `tsort__dir`, `isin__add`) sind über Tasks 2–4 konsistent.
