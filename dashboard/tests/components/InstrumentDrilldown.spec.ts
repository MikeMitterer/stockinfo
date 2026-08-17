import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import InstrumentDrilldown from '../../src/components/InstrumentDrilldown.vue'
import { i18n } from '../../src/i18n'
import { makeInstrument } from '../fixtures/instrument'

describe('InstrumentDrilldown', () => {
  it('zeigt alle acht Kennzahlen zum Pflegen', () => {
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: { item: makeInstrument() },
    })

    expect(wrapper.findAllComponents({ name: 'MetricEditor' })).toHaveLength(8)
  })

  it('erklärt, warum die Quelle nichts beigesteuert hat', () => {
    // Nicht-europäisches Domizil wird bewusst übersprungen — genau diese
    // Erklärung fehlt dem Nutzer heute.
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: { item: makeInstrument({ isin: 'US0378331005', ter: null }) },
    })

    expect(wrapper.text()).toContain(i18n.global.t('drilldown.noEuropeanSource'))
  })

  it('erklärt eine leere Quelle bei europäischem Domizil', () => {
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: { item: makeInstrument({ isin: 'IE00B4L5Y983', ter: null, volatility: null }) },
    })

    expect(wrapper.text()).toContain(i18n.global.t('drilldown.sourceEmpty'))
  })

  it('zeigt den Zeitpunkt der letzten Metadaten-Abfrage', () => {
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: { item: makeInstrument({ meta_fetched_at: '2026-08-16T10:00:00Z' }) },
    })

    expect(wrapper.text()).toContain(i18n.global.t('drilldown.fetchedAt'))
  })

  it('reicht ein commit-Ereignis eines Editors unverändert nach oben durch', async () => {
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: { item: makeInstrument({ provider: null }) },
    })

    const providerEditor = wrapper
      .findAllComponents({ name: 'MetricEditor' })
      .find((editor) => editor.props('field') === 'provider')
    providerEditor?.vm.$emit('commit', { provider: 'Vanguard' })

    expect(wrapper.emitted('commit')?.[0]?.[0]).toEqual({ provider: 'Vanguard' })
  })

  it('reicht die Vorschläge je Feld an den passenden Editor durch', () => {
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: {
        item: makeInstrument({ provider: null, fund_currency: null }),
        fieldOptions: { provider: ['Vanguard', 'iShares'], fund_currency: ['EUR', 'USD'] },
      },
    })

    const editors = wrapper.findAllComponents({ name: 'MetricEditor' })
    const providerEditor = editors.find((editor) => editor.props('field') === 'provider')
    const currencyEditor = editors.find((editor) => editor.props('field') === 'fund_currency')
    const replicationEditor = editors.find((editor) => editor.props('field') === 'replication')

    expect(providerEditor?.props('options')).toEqual(['Vanguard', 'iShares'])
    expect(currencyEditor?.props('options')).toEqual(['EUR', 'USD'])
    expect(replicationEditor?.props('options')).toBeUndefined()
  })
})
