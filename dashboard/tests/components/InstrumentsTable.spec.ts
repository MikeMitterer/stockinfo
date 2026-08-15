import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import InstrumentsTable from '../../src/components/InstrumentsTable.vue'
import { useTableSort } from '../../src/composables/useTableSort'
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
  // sortKey/direction sind Modul-Level-Singletons — zwischen Tests zurücksetzen,
  // sonst hängt eine Sortierung aus einem früheren Test nach.
  useTableSort().setSortKey(null)
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

  it('zeigt eine sichtbare Beschriftung, die auf das Select verweist', () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    const label = wrapper.find('.tsort__label')
    const select = wrapper.find('.tsort__select')
    expect(label.exists()).toBe(true)
    expect(label.text()).toBe('Sortieren nach')
    expect(label.attributes('for')).toBe(select.attributes('id'))
  })

  it('erste Option ist der Platzhalter "Ohne Sortierung" mit leerem Wert', () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    const options = wrapper.findAll('.tsort__select option')
    expect(options[0].text()).toBe('Ohne Sortierung')
    expect(options[0].attributes('value')).toBe('')
  })

  it('Select steht ohne aktive Sortierung auf dem leeren Platzhalter-Wert', () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    const select = wrapper.find('.tsort__select')
    expect((select.element as HTMLSelectElement).value).toBe('')
  })

  it('Richtungsknopf ist ohne aktive Sortierung deaktiviert', () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    expect(wrapper.find('.tsort__dir').attributes('disabled')).toBeDefined()
  })

  it('Wahl des Platzhalters setzt eine aktive Sortierung zurück', async () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    const select = wrapper.find('.tsort__select')

    // erst eine Spalte wählen, damit Sortierung aktiv ist …
    await select.setValue('name')
    expect((select.element as HTMLSelectElement).value).toBe('name')
    expect(wrapper.find('.tsort__dir').attributes('disabled')).toBeUndefined()
    expect(window.localStorage.getItem('stockinfo-sort')).not.toBeNull()

    // … dann den Platzhalter wählen und Reset prüfen
    await select.setValue('')
    expect((select.element as HTMLSelectElement).value).toBe('')
    expect(wrapper.find('.tsort__dir').attributes('disabled')).toBeDefined()
    expect(window.localStorage.getItem('stockinfo-sort')).toBeNull()
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
