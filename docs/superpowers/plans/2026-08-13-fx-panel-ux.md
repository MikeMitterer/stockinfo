# Devisen-Panel-UX (T-06) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Devisen-Tab bekommt Währungs-Dropdowns (aus `/exchanges`, `GBp→GBP`), eine auf 3 Nachkommastellen gerundete Rate und eine lesbar formatierte Kurszeit.

**Architecture:** Reine Frontend-Änderung an `FxPanel.vue`, gespeist aus bereits vorhandenen Daten. Zwei neue pure Util-Funktionen (`formatDateTime`, `currenciesFromExchanges`) werden isoliert getestet und dann in `FxPanel`/`App.vue` verdrahtet. Kein Backend-Change.

**Tech Stack:** Vue 3 (`<script setup lang="ts">`), vue-i18n, Vitest + @vue/test-utils (jsdom), SCSS.

## Global Constraints

- **i18n MUST:** Kein hartkodierter UI-Text in Template/Code. Alle Texte über vue-i18n (`de.ts` + `en.ts`). Währungscodes sind Daten (keine Übersetzung). (Projektstandard code-standards.)
- **Keine hartkodierte Währungsliste:** Dropdown-Inhalt ausschließlich aus `/exchanges` ableiten (eine Quelle der Wahrheit, konsistent mit T-02).
- **Datumsformat:** `Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' })`.
- **Rate-Anzeige:** `toLocaleString(locale, { maximumFractionDigits: 3 })`; roher Wert bleibt intern erhalten (als `title`-Tooltip).
- **Branch zuerst:** Vor Task 1 einen Feature-Branch anlegen (`git checkout -b feat/fx-panel-ux`), da `master` der Default-Branch ist. Alle Task-Commits landen dort.
- **Arbeitsverzeichnis für alle Kommandos:** `dashboard/` (Vitest-Projekt). Test-Runner: `npx vitest run <pfad>`.

---

### Task 1: `formatDateTime`-Util

**Files:**
- Create: `dashboard/src/utils/datetime.ts`
- Test: `dashboard/tests/utils/datetime.spec.ts`

**Interfaces:**
- Consumes: `ExchangesResponse` nicht nötig; nur `string`/`Intl`.
- Produces: `formatDateTime(iso: string, locale: string): string`

- [ ] **Step 1: Write the failing test**

`dashboard/tests/utils/datetime.spec.ts`:
```ts
import { describe, expect, it } from 'vitest'

import { formatDateTime } from '../../src/utils/datetime'

describe('formatDateTime', () => {
  it('formatiert einen ISO-String lokalisiert (kein roher ISO-String)', () => {
    const out = formatDateTime('2026-08-13T07:41:13.759837+00:00', 'de')
    expect(out).not.toContain('T')       // kein 'YYYY-MM-DDTHH:...'
    expect(out).toMatch(/2026/)          // Jahr enthalten
  })

  it('gibt bei ungültigem Input den Rohwert zurück', () => {
    expect(formatDateTime('nope', 'de')).toBe('nope')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/utils/datetime.spec.ts`
Expected: FAIL — `formatDateTime` nicht gefunden / Modul fehlt.

- [ ] **Step 3: Write minimal implementation**

`dashboard/src/utils/datetime.ts`:
```ts
/**
 * Formatiert einen ISO-Zeitstempel lokalisiert (Datum + Uhrzeit).
 *
 * @param iso - ISO-8601-Zeitstempel (z.B. aus `quote_time`).
 * @param locale - aktive Locale (z.B. 'de' | 'en').
 * @returns Lokalisiertes „13. Aug. 2026, 09:41"; bei ungültigem Input der Rohwert.
 */
export function formatDateTime(iso: string, locale: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/utils/datetime.spec.ts`
Expected: PASS (beide Fälle).

- [ ] **Step 5: Commit**

```bash
git add dashboard/src/utils/datetime.ts dashboard/tests/utils/datetime.spec.ts
git commit -m "feat(dashboard): formatDateTime-Util für lokalisierte Zeitstempel"
```

---

### Task 2: `currenciesFromExchanges`-Util

**Files:**
- Create: `dashboard/src/utils/currencies.ts`
- Test: `dashboard/tests/utils/currencies.spec.ts`

**Interfaces:**
- Consumes: `ExchangesResponse | null` aus `../types` (Felder: `exchanges: { currency: string }[]`).
- Produces: `currenciesFromExchanges(data: ExchangesResponse | null): string[]` — eindeutig, sortiert, `GBp→GBP`.

- [ ] **Step 1: Write the failing test**

`dashboard/tests/utils/currencies.spec.ts`:
```ts
import { describe, expect, it } from 'vitest'

import { currenciesFromExchanges } from '../../src/utils/currencies'

const data = {
  default_exchange: 'XETR',
  exchanges: [
    { mic: 'XETR', suffix: '.DE', name: 'Xetra', region: 'germany', currency: 'EUR' },
    { mic: 'XLON', suffix: '.L', name: 'London', region: 'europe', currency: 'GBp' },
    { mic: 'US', suffix: '', name: 'NYSE', region: 'usa', currency: 'USD' },
    { mic: 'XFRA', suffix: '.F', name: 'Frankfurt', region: 'germany', currency: 'EUR' },
  ],
}

describe('currenciesFromExchanges', () => {
  it('dedupliziert, sortiert und mappt GBp→GBP', () => {
    expect(currenciesFromExchanges(data)).toEqual(['EUR', 'GBP', 'USD'])
  })

  it('gibt [] zurück, wenn keine Daten vorliegen', () => {
    expect(currenciesFromExchanges(null)).toEqual([])
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/utils/currencies.spec.ts`
Expected: FAIL — Modul/Funktion fehlt.

- [ ] **Step 3: Write minimal implementation**

`dashboard/src/utils/currencies.ts`:
```ts
import type { ExchangesResponse } from '../types'

/**
 * Leitet die wählbaren FX-Währungen aus der Börsentabelle ab.
 * `GBp` (Londoner Pence) wird zu `GBP` normalisiert; Ergebnis ist eindeutig
 * und alphabetisch sortiert.
 *
 * @param data - Antwort von GET /exchanges (oder null, solange nicht geladen).
 * @returns Sortierte, eindeutige Währungscodes; `[]` ohne Daten.
 */
export function currenciesFromExchanges(data: ExchangesResponse | null): string[] {
  if (!data) return []
  const codes = data.exchanges.map((ex) => (ex.currency === 'GBp' ? 'GBP' : ex.currency))
  return [...new Set(codes)].sort()
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/utils/currencies.spec.ts`
Expected: PASS (beide Fälle).

- [ ] **Step 5: Commit**

```bash
git add dashboard/src/utils/currencies.ts dashboard/tests/utils/currencies.spec.ts
git commit -m "feat(dashboard): currenciesFromExchanges-Util (dedupe, sort, GBp→GBP)"
```

---

### Task 3: FxPanel — Rate auf 3 Stellen + formatierte Kurszeit

**Files:**
- Modify: `dashboard/src/components/FxPanel.vue`
- Test: `dashboard/tests/components/FxPanel.spec.ts`

**Interfaces:**
- Consumes: `formatDateTime` (Task 1). `useI18n().locale` für Zahl-/Datumsformat.
- Produces: keine neuen Exporte. Sichtbare Änderung: Rate ≤3 Nachkommastellen mit `title`=Rohwert; Kurszeit formatiert, `white-space: nowrap`.

> Hinweis: `FxPanel` bekommt in **Task 4** die `currencies`-Prop. Damit der
> bestehende Test in diesem Task grün bleibt (ohne Prop, mit Text-Inputs), wird
> die Template-Anzeige hier geändert, die Eingabefelder aber noch **nicht**. Der
> vorhandene Test wird auf die neue Zahlenformatierung angepasst.

- [ ] **Step 1: Update the existing test to assert the new formatting (failing)**

Ersetze in `dashboard/tests/components/FxPanel.spec.ts` den Testkörper so, dass die Locale deterministisch gesetzt und das 3-Stellen-Format geprüft wird:
```ts
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({ consola: { error: vi.fn() } }))
import FxPanel from '../../src/components/FxPanel.vue'
import { i18n } from '../../src/i18n'

beforeEach(() => {
  i18n.global.locale.value = 'en' // deterministisches Dezimaltrennzeichen '.'
})
afterEach(() => vi.unstubAllGlobals())

describe('FxPanel', () => {
  it('zeigt den Kurs auf 3 Nachkommastellen gerundet, Rohwert im title', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ base: 'EUR', quote: 'USD', rate: 1.1527377367019653, quote_time: '2026-08-13T07:41:13.759837+00:00', source: 'yfinance', cached: false, stale: false, fetched_at: 't' }),
      { status: 200 },
    )))
    const wrapper = mount(FxPanel, { global: { plugins: [i18n] } })
    await wrapper.find('button:last-of-type').trigger('click')
    await flushPromises()

    const rate = wrapper.find('.rate')
    expect(rate.text()).toContain('1 EUR = 1.153 USD')      // 3 Nachkommastellen
    expect(rate.text()).not.toContain('1.1527377367019653') // nicht roh
    expect(rate.attributes('title')).toBe('1.1527377367019653')
  })

  it('zeigt die Kurszeit formatiert (kein roher ISO-String)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ base: 'EUR', quote: 'USD', rate: 1.15, quote_time: '2026-08-13T07:41:13.759837+00:00', source: 'yfinance', cached: false, stale: false, fetched_at: 't' }),
      { status: 200 },
    )))
    const wrapper = mount(FxPanel, { global: { plugins: [i18n] } })
    await wrapper.find('button:last-of-type').trigger('click')
    await flushPromises()
    expect(wrapper.text()).not.toContain('2026-08-13T07:41:13') // kein ISO-Rohstring
    expect(wrapper.text()).toContain('2026')                    // Jahr sichtbar
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/components/FxPanel.spec.ts`
Expected: FAIL — Rate wird noch roh gerendert (`1.1527377367019653`), kein `title`, Kurszeit roh.

- [ ] **Step 3: Implement formatting in FxPanel.vue**

Im `<script setup>`-Block `locale` aus `useI18n` beziehen und zwei Helper ergänzen; `formatDateTime` importieren:
```ts
import { formatDateTime } from '../utils/datetime'
// ...
const { t, locale } = useI18n()
// ...
/** Rate lokalisiert mit höchstens 3 Nachkommastellen. */
function formatRate(rate: number): string {
  return rate.toLocaleString(locale.value, { maximumFractionDigits: 3 })
}
```

Im `<template>` die Rate-Zeile und die Kurszeit-Zeile ersetzen:
```html
<p class="rate mono" :title="String(result.rate)">
  1 {{ result.base }} = {{ formatRate(result.rate) }} {{ result.quote }}
</p>
```
```html
<div><dt>{{ t('fx.quoteTime') }}</dt>
  <dd class="mono nowrap">{{ formatDateTime(result.quote_time, locale) }}</dd></div>
```

Im `<style scoped>` innerhalb `.fx` eine Regel ergänzen:
```scss
.nowrap { white-space: nowrap; }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/components/FxPanel.spec.ts`
Expected: PASS (beide Fälle).

- [ ] **Step 5: Commit**

```bash
git add dashboard/src/components/FxPanel.vue dashboard/tests/components/FxPanel.spec.ts
git commit -m "feat(dashboard): FxPanel Rate auf 3 Stellen + formatierte Kurszeit"
```

---

### Task 4: FxPanel — Währungs-Dropdowns + App.vue-Verdrahtung

**Files:**
- Modify: `dashboard/src/components/FxPanel.vue`
- Modify: `dashboard/src/App.vue`
- Test: `dashboard/tests/components/FxPanel.spec.ts`

**Interfaces:**
- Consumes: `currenciesFromExchanges` (Task 2), `exchanges`-Ref in `App.vue` (bereits via `useExchanges`).
- Produces: `FxPanel`-Prop `currencies: string[]`. `App.vue` computed `fxCurrencies`.

- [ ] **Step 1: Write the failing test (dropdown rendering)**

Ergänze in `dashboard/tests/components/FxPanel.spec.ts` einen Test (die bestehenden Tests bekommen zusätzlich die Prop, siehe Step 3):
```ts
it('rendert Währungs-Dropdowns aus der currencies-Prop', () => {
  const wrapper = mount(FxPanel, {
    global: { plugins: [i18n] },
    props: { currencies: ['EUR', 'GBP', 'USD'] },
  })
  const selects = wrapper.findAll('select')
  expect(selects).toHaveLength(2)
  const options = selects[0].findAll('option').map((o) => o.text())
  expect(options).toEqual(['EUR', 'GBP', 'USD'])
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/components/FxPanel.spec.ts`
Expected: FAIL — es gibt (noch) `<input>` statt `<select>`; `findAll('select')` ist leer.

- [ ] **Step 3: Implement dropdowns in FxPanel.vue**

`defineProps` ergänzen:
```ts
defineProps<{ currencies: string[] }>()
```

Im `<template>` die beiden `<input>`-Felder durch `<select>` ersetzen (⇄-Button unverändert dazwischen):
```html
<select v-model="base" class="code" :aria-label="t('fx.base')">
  <option v-for="c in currencies" :key="c" :value="c">{{ c }}</option>
</select>
<button class="swap" :title="t('fx.swap')" @click="swap">⇄</button>
<select v-model="quote" class="code" :aria-label="t('fx.quote')">
  <option v-for="c in currencies" :key="c" :value="c">{{ c }}</option>
</select>
```

Bestehende Tests (die kein `currencies` übergeben) in derselben Datei auf die Prop heben — bei `mount(FxPanel, ...)` jeweils `props: { currencies: ['EUR', 'USD'] }` ergänzen, damit die Default-Auswahl EUR/USD wählbar ist.

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/components/FxPanel.spec.ts`
Expected: PASS (Dropdown-Test + die beiden Format-Tests).

- [ ] **Step 5: Wire FxPanel in App.vue**

In `dashboard/src/App.vue`:
- Import ergänzen: `import { currenciesFromExchanges } from './utils/currencies'`
- Nach der `exchanges`-Deklaration eine computed ergänzen:
```ts
const fxCurrencies = computed(() => currenciesFromExchanges(exchanges.value))
```
(`computed` wird bereits importiert.)
- Im `<template>` die FxPanel-Zeile ersetzen:
```html
<FxPanel v-else-if="activeTab === 'fx'" :currencies="fxCurrencies" />
```

- [ ] **Step 6: Run the full dashboard test suite**

Run: `npx vitest run`
Expected: PASS — alle Tests grün (keine Regression in App/Exchanges).

- [ ] **Step 7: Commit**

```bash
git add dashboard/src/components/FxPanel.vue dashboard/src/App.vue dashboard/tests/components/FxPanel.spec.ts
git commit -m "feat(dashboard): FxPanel Währungs-Dropdowns aus /exchanges (GBp→GBP)"
```

---

### Task 5: i18n-Audit + manuelle UI-Verifikation

**Files:**
- Modify (nur falls Audit hartkodierten Text findet): `dashboard/src/components/FxPanel.vue`, `dashboard/src/i18n/de.ts`, `dashboard/src/i18n/en.ts`

**Interfaces:**
- Consumes: alle vorigen Tasks.
- Produces: bestätigt „kein hartkodierter UI-Text" und schließt die Verify-Matrix in `_tickets/T-06-fx-panel-ux.md` (#1–#6).

- [ ] **Step 1: Hardcoded-Text-Audit**

Prüfe, dass jeder sichtbare Text in `FxPanel.vue` über `t('…')` läuft (Labels, aria-labels, Status). Erwartung: bereits erfüllt — Dropdowns nutzen `t('fx.base')`/`t('fx.quote')`, Kurszeit `t('fx.quoteTime')`; Options sind Währungscodes (Daten). **Falls** doch ein hartkodierter String auftaucht: Key in `de.ts` **und** `en.ts` ergänzen und im Template ersetzen.

Run (Gegencheck auf verdächtige Literale im Template):
```bash
grep -nE ">[^<{]*[A-Za-zÄÖÜäöü]{3,}[^<}]*<" dashboard/src/components/FxPanel.vue | grep -v "{{"
```
Expected: keine Treffer außer Währungscodes/Symbolen.

- [ ] **Step 2: Build/Typecheck**

Run: `npm run build` (im `dashboard/`)
Expected: erfolgreicher Vue-tsc/Vite-Build (keine Typfehler durch die neue Prop).

- [ ] **Step 3: Manuelle UI-Verifikation gegen die Verify-Matrix**

Stack läuft (`make dev-up`). Im Browser `#/fx`:
- Basis/Ziel als **Dropdown** wählbar; Liste = Währungen aus `/exchanges`, `GBP` (nicht `GBp`), keine Dubletten. → T-06 #1
- Umrechnen EUR→USD: Rate mit **3 Nachkommastellen**; Hover zeigt Rohwert. → T-06 #5
- Kurszeit **lesbar** (z.B. „13. Aug. 2026, 09:41"), **kein Umbruch**. → T-06 #3, #6
- `stale`-Badge unverändert; Sprache DE/EN umschalten → Zahlen/Datum lokalisiert.

Trage die AI-Spalte in `_tickets/T-06-fx-panel-ux.md` mit Evidenz nach (Legende ✅/⚠️/◑/➖). Human-Spalte bleibt frei.

- [ ] **Step 4: Commit (nur falls Audit Änderungen brachte)**

```bash
git add dashboard/src/components/FxPanel.vue dashboard/src/i18n/de.ts dashboard/src/i18n/en.ts
git commit -m "chore(dashboard): i18n-Audit FxPanel (T-06)"
```

---

## Self-Review

**Spec coverage:**
- Dropdown aus `/exchanges`, GBp→GBP, dedupe, sort → Task 2 (Util) + Task 4 (UI/Verdrahtung). ✓
- Rate 3 Nachkommastellen + Rohwert-Tooltip → Task 3. ✓
- Kurszeit lokalisiert + nowrap → Task 1 (Util) + Task 3. ✓
- i18n durchgängig, kein hartkodierter Text → Task 5 (Audit) + Global Constraints. ✓
- Tests (datetime, currencies, FxPanel) → Tasks 1, 2, 3, 4. ✓
- Kein Backend-Change, `useFx` unverändert → keine Task berührt sie. ✓

**Placeholder scan:** Keine TBD/TODO; jeder Code-Step enthält konkreten Code bzw. konkretes Kommando. ✓

**Type consistency:** `formatDateTime(iso, locale)`, `currenciesFromExchanges(data)`, Prop `currencies: string[]`, `fxCurrencies` computed — durchgängig gleich benannt in Tasks 1–5. `FxRate`/`ExchangesResponse`/`ExchangeInfo` wie in `types.ts`. ✓
