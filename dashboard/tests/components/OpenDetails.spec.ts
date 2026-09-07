import { mount, flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import OpenDetails from '../../src/components/OpenDetails.vue'
import DetailEditor from '../../src/components/DetailEditor.vue'
import { i18n } from '../../src/i18n'
import { useOverrides } from '../../src/composables/useOverrides'
import { makeInstrument } from '../fixtures/instrument'
import type { DetailDefinition, DetailValue } from '../../src/types'

const definition: DetailDefinition = {
  name: 'sample.risk', kind: 'number', unit: null, label_en: 'Risk', label_de: 'Risiko',
  overridable: true, minimum: 0, maximum: 100, currency_required: false,
}
const value: DetailValue = {
  value: null, unit: null, currency: null, origin: null, source: null, as_of: null,
  shadowed: false, manual_value: null, manual_currency: null,
}
const previousLocale = i18n.global.locale.value
beforeEach(() => { i18n.global.locale.value = 'de' })
afterEach(() => { vi.unstubAllGlobals(); i18n.global.locale.value = previousLocale })

describe('Offene Detailfelder', () => {
  it('zeigt ein vorher unbekanntes Plugin-Feld und reicht die Eingabe weiter', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ details: [definition] }))))
    const wrapper = mount(OpenDetails, {
      props: { item: makeInstrument({ details: { 'sample.risk': value } }) },
      global: { plugins: [i18n] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Risiko')
    wrapper.getComponent(DetailEditor).vm.$emit('commit', { value: 0, currency: null })
    expect(wrapper.emitted('commit')?.[0]).toEqual([{ details: { 'sample.risk': { value: 0, currency: null } } }])
  })

  it('zeigt BTC-EUR keine Fondsfelder aus dem globalen Katalog', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ details: [definition, { ...definition, name: 'fund_currency' }] }))))
    const wrapper = mount(OpenDetails, {
      props: { item: makeInstrument({ type: 'crypto', details: {} }) },
      global: { plugins: [i18n] },
    })
    await flushPromises()
    expect(wrapper.findComponent(DetailEditor).exists()).toBe(false)
    expect(wrapper.text()).toContain(i18n.global.t('details.empty'))
  })

  it.each([
    ['nicht überschreibbar', false, null],
    ['von der Quelle geliefert', true, 'provider'],
  ] as const)('sperrt den Editor: %s', (_scenario, overridable, origin) => {
    const wrapper = mount(DetailEditor, {
      props: { definition: { ...definition, overridable }, value: { ...value, value: 4, origin } },
      global: { plugins: [i18n] },
    })
    expect(wrapper.findComponent({ name: 'UxInlineNumber' }).exists()).toBe(false)
    expect(wrapper.text()).toContain('4')
  })

  it('schreibt per Listing-ID und PATCH, auch für unbekannte Felder', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{}'))
    vi.stubGlobal('fetch', fetchMock)
    await useOverrides().save(makeInstrument(), { details: { 'sample.risk': { value: false } } })
    expect(fetchMock.mock.calls[0][0]).toContain('/instruments/by-id/00000000-0000-4000-8000-000000000001/details')
    expect(fetchMock.mock.calls[0][1].method).toBe('PATCH')
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ 'sample.risk': { value: false } })
  })
})
