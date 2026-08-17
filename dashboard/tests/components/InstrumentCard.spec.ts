import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'

import InstrumentCard from '../../src/components/InstrumentCard.vue'
import { i18n } from '../../src/i18n'
import type { InstrumentSummary } from '../../src/types'
import { makeInstrument } from '../fixtures/instrument'

function mountCard(overrides: Partial<InstrumentSummary> = {}) {
  return mount(InstrumentCard, {
    props: {
      item: makeInstrument(overrides),
      selected: false, refreshing: false, saving: false,
      extraetfUrl: '', yahooUrl: '',
    },
    global: { plugins: [i18n] },
  })
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
})

// Hinweis zu T-11c (Fußzeilen-Overflow bei 375px): jsdom führt kein echtes
// Layout aus (keine Box-Maße, kein Zeilenumbruch), daher lässt sich
// `flex-wrap: wrap` hier nicht sinnvoll durch einen Test absichern — ein
// Test, der nur `.icard__foot`/`.icard__actions` auf Existenz prüft, würde
// nichts über das Umbruchverhalten aussagen und wäre eine Scheinsicherung.
// Verifiziert wurde die Behebung stattdessen live im Browser bei 375px
// Viewport: `.icard__foot` benötigt 318px (65px Toggle + 245.3px Actions +
// 8px Gap) in 265px verfügbarer Breite, `.icard__actions` benötigt 245.3px
// für fünf 44px-Ziele — beide Zeilen brechen jetzt um, `document
// .documentElement.scrollWidth - clientWidth` ist wieder 0.
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
    // Deutsches Zahlenformat: Der Wert lief vorher über `toFixed` und stand
    // deshalb mit Punkt in einer deutschen Oberfläche.
    expect(wrapper.find('.icard__details').text()).toContain('25,80')
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
