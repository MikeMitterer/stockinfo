import { mount } from '@vue/test-utils'
import { NSelect } from 'naive-ui'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import InstrumentsTable from '../../src/components/InstrumentsTable.vue'
import { useTableSort } from '../../src/composables/useTableSort'
import { i18n } from '../../src/i18n'
import { makeInstrument } from '../fixtures/instrument'

const base = makeInstrument()
const instruments = [base, makeInstrument({ symbol: 'VGWL.DE', name: 'Vanguard FTSE All-World' })]

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
      instruments, selectedSymbol: null, refreshingSymbol: null, savingSymbol: null,
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
    // Richtungsknopf erst sichtbar, sobald tatsächlich sortiert wird (s.u.)
    expect(wrapper.find('.tsort__dir').exists()).toBe(false)
  })

  it('trägt einen zugänglichen Namen — ein Feld ohne Namen ist keins', () => {
    stubMatchMedia(true)
    const wrapper = mountTable()

    expect(wrapper.findComponent(NSelect).attributes('aria-label')).toBe('Sortieren nach')
  })

  it('bietet den Leerlauf als erste Wahl — sonst ließe sich Sortieren nicht abschalten', () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    const optionen = wrapper.findComponent(NSelect).props('options')!

    expect(optionen[0]).toEqual({ value: '', label: 'Ohne Sortierung' })
  })

  it('steht ohne aktive Sortierung auf dem Leerlauf', () => {
    stubMatchMedia(true)
    const wrapper = mountTable()

    expect(wrapper.findComponent(NSelect).props('value')).toBe('')
  })

  it('übernimmt die gewählte Spalte', async () => {
    stubMatchMedia(true)
    const wrapper = mountTable()

    wrapper.findComponent(NSelect).vm.$emit('update:value', 'name')
    await wrapper.vm.$nextTick()

    expect(wrapper.findComponent(NSelect).props('value')).toBe('name')
    expect(wrapper.find('.tsort__dir').exists()).toBe(true)
  })

  it('Richtungsknopf ist ohne aktive Sortierung nicht vorhanden', () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    expect(wrapper.find('.tsort__dir').exists()).toBe(false)
  })

  it('Wahl des Leerlaufs setzt eine aktive Sortierung zurück', async () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    const auswahl = wrapper.findComponent(NSelect)

    auswahl.vm.$emit('update:value', 'name')
    await wrapper.vm.$nextTick()
    expect(window.localStorage.getItem('stockinfo-sort')).not.toBeNull()

    auswahl.vm.$emit('update:value', '')
    await wrapper.vm.$nextTick()

    expect(wrapper.findComponent(NSelect).props('value')).toBe('')
    expect(wrapper.find('.tsort__dir').exists()).toBe(false)
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
        instruments: [], selectedSymbol: null, refreshingSymbol: null, savingSymbol: null,
        extraetfEtfUrl: '', extraetfStockUrl: '', yahooUrl: '',
      },
      global: { plugins: [i18n] },
    })
    expect(wrapper.find('.empty').exists()).toBe(true)
  })
})
