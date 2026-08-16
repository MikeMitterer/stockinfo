import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'

import ConfirmDeleteDialog from '../../src/components/ConfirmDeleteDialog.vue'
import { i18n } from '../../src/i18n'
import type { InstrumentSummary } from '../../src/types'

/** Minimales Instrument für Tests — nur die für den Dialog relevanten Felder gesetzt. */
function makeItem(overrides: Partial<InstrumentSummary> = {}): InstrumentSummary {
  return {
    isin: 'IE00B4L5Y983',
    symbol: 'EUNL.DE',
    exchange: 'DE',
    name: 'iShares Core MSCI World',
    type: 'ETF',
    currency: 'EUR',
    provider: null,
    ter: null,
    replication: null,
    fund_size: null,
    volatility: null,
    accumulating: null,
    meta_fetched_at: null,
    latest_price: null,
    latest_quote_time: null,
    latest_currency: null,
    latest_fetched_at: null,
    history_count: 8,
    ...overrides,
  }
}

function mountDialog(item: InstrumentSummary | null) {
  return mount(ConfirmDeleteDialog, { props: { item }, global: { plugins: [i18n] } })
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
})

describe('ConfirmDeleteDialog', () => {
  it('rendert nichts, wenn item null ist', () => {
    const wrapper = mountDialog(null)
    expect(wrapper.find('.overlay').exists()).toBe(false)
  })

  it('zeigt Name und Symbol des Instruments', () => {
    const wrapper = mountDialog(makeItem())
    const text = wrapper.text()
    expect(text).toContain('iShares Core MSCI World')
    expect(text).toContain('EUNL.DE')
  })

  it('zeigt den Singular-Satz bei history_count = 1', () => {
    const wrapper = mountDialog(makeItem({ history_count: 1 }))
    expect(wrapper.text()).toContain('1 Kurspunkt geht verloren.')
  })

  it('zeigt den Null-Satz bei history_count = 0', () => {
    const wrapper = mountDialog(makeItem({ history_count: 0 }))
    expect(wrapper.text()).toContain('Keine Kurspunkte gespeichert.')
  })

  it('zeigt den Plural-Satz bei history_count = 8', () => {
    const wrapper = mountDialog(makeItem({ history_count: 8 }))
    expect(wrapper.text()).toContain('8 Kurspunkte gehen verloren.')
  })

  it('emittiert confirm bei Klick auf Löschen', async () => {
    const wrapper = mountDialog(makeItem())
    await wrapper.find('.confirm-delete__confirm').trigger('click')
    expect(wrapper.emitted('confirm')).toHaveLength(1)
  })

  it('emittiert cancel bei Klick auf Abbrechen', async () => {
    const wrapper = mountDialog(makeItem())
    await wrapper.find('.confirm-delete__cancel').trigger('click')
    expect(wrapper.emitted('cancel')).toHaveLength(1)
  })

  it('emittiert cancel bei Escape', async () => {
    const wrapper = mountDialog(makeItem())
    await wrapper.trigger('keydown', { key: 'Escape' })
    // Escape wird global (window) abgehört — hier direkt am window auslösen.
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    expect(wrapper.emitted('cancel')).toBeTruthy()
  })

  it('emittiert cancel bei Klick auf die abdunkelnde Fläche', async () => {
    const wrapper = mountDialog(makeItem())
    await wrapper.find('.overlay').trigger('click')
    expect(wrapper.emitted('cancel')).toHaveLength(1)
  })

  it('emittiert kein cancel bei Klick innerhalb des Dialogs', async () => {
    const wrapper = mountDialog(makeItem())
    await wrapper.find('.modal').trigger('click')
    expect(wrapper.emitted('cancel')).toBeUndefined()
  })
})
