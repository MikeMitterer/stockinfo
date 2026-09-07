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
  it.each([false, true])('entfernt Zahlen über das rechte rote Löschkreuz (Währung: %s)', async (currencyRequired) => {
    const wrapper = mount(DetailEditor, {
      props: {
        definition: { ...definition, unit: currencyRequired ? 'absolute' : 'percent', currency_required: currencyRequired },
        value: { ...value, value: 500, manual_value: 500, currency: 'EUR', manual_currency: 'EUR', origin: 'manual' },
      },
      global: { plugins: [i18n] },
    })
    expect(wrapper.find('.inline-number__clear').exists()).toBe(false)
    await wrapper.get('button.n-button--error-type').trigger('click')
    expect(wrapper.emitted('commit')?.[0]).toEqual([{ value: null, currency: currencyRequired ? 'EUR' : null }])
  })

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

  it('schaltet eine editierbare Ja-Nein-Angabe durch wahr, falsch und leer', async () => {
    const wrapper = mount(DetailEditor, {
      props: { definition: { ...definition, kind: 'boolean' }, value },
      global: { plugins: [i18n] },
    })
    const button = () => wrapper.get('button[aria-label="Risiko bearbeiten"]')
    await button().trigger('click')
    expect(wrapper.emitted('commit')?.at(-1)).toEqual([{ value: true, currency: null }])
    await wrapper.setProps({ value: { ...value, value: true, manual_value: true, origin: 'manual' } })
    await button().trigger('click')
    expect(wrapper.emitted('commit')?.at(-1)).toEqual([{ value: false, currency: null }])
    await wrapper.setProps({ value: { ...value, value: false, manual_value: false, origin: 'manual' } })
    expect(button().text()).toBe('Nein')
    await button().trigger('click')
    expect(wrapper.emitted('commit')?.at(-1)).toEqual([{ value: null, currency: null }])
    wrapper.unmount()
  })
})
