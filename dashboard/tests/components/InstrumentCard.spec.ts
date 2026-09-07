import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'

import InfoHint from '../../src/components/InfoHint.vue'
import InstrumentCard from '../../src/components/InstrumentCard.vue'
import { i18n } from '../../src/i18n'
import type { InstrumentSummary } from '../../src/types'
import { makeInstrument } from '../fixtures/instrument'

function mountCard(overrides: Partial<InstrumentSummary> & { isin?: string | null } = {}) {
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

  it('hält Details und Detailbereich bis zum Aufklappen verborgen', async () => {
    const wrapper = mountCard()
    expect(wrapper.find('.icard__details').exists()).toBe(false)
    expect(wrapper.findComponent({ name: 'InstrumentDrilldown' }).exists()).toBe(false)

    await wrapper.find('.icard__toggle').trigger('click')

    expect(wrapper.find('.icard__details').exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'InstrumentDrilldown' }).exists()).toBe(true)
  })

  it('bietet mobil dieselben acht Felder wie am Schreibtisch (Task 8)', async () => {
    const wrapper = mountCard()
    await wrapper.find('.icard__toggle').trigger('click')

    expect(wrapper.findAllComponents({ name: 'MetricEditor' })).toHaveLength(8)
  })

  it('zeigt keine Anzahl gespeicherter Kurspunkte', async () => {
    const wrapper = mountCard({ history_count: 42 })
    await wrapper.find('.icard__toggle').trigger('click')

    expect(wrapper.find('.icard__details').text()).not.toContain('42')
  })

  it('reicht ein commit aus dem Detailbereich unverändert als override weiter', async () => {
    const wrapper = mountCard()
    await wrapper.find('.icard__toggle').trigger('click')

    wrapper.findComponent({ name: 'InstrumentDrilldown' }).vm.$emit('commit', { provider: 'Vanguard' })

    expect(wrapper.emitted('override')?.[0]?.[0]).toEqual({ provider: 'Vanguard' })
  })

  it('reicht fieldOptions unverändert an den Detailbereich durch', async () => {
    const wrapper = mount(InstrumentCard, {
      props: {
        item: makeInstrument(),
        selected: false, refreshing: false, saving: false,
        extraetfUrl: '', yahooUrl: '',
        fieldOptions: { provider: ['Vanguard', 'iShares'] },
      },
      global: { plugins: [i18n] },
    })
    await wrapper.find('.icard__toggle').trigger('click')

    expect(wrapper.findComponent({ name: 'InstrumentDrilldown' }).props('fieldOptions')).toEqual({
      provider: ['Vanguard', 'iShares'],
    })
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

  it('bietet dem Waehrungspaar keinen ISIN-Editor, sondern eine Erklaerung', async () => {
    // **Codex `#5` aus Runde 5.** Eine Coin hat keine ISIN — das ist keine
    // Luecke, die jemand fuellen koennte, sondern eine Eigenschaft der Form.
    // Der Editor dort waere eine Einladung in einen Fehler: Der
    // Speicherversuch liefe gegen den `CHECK`, der fuer `pair` ausdruecklich
    // `isin IS NULL` verlangt.
    //
    // Geprueft wird beides — dass der Editor **weg** ist und dass an seiner
    // Stelle etwas steht. Ein leeres Feld saehe aus wie ein
    // Bearbeitungsfehler.
    const wrapper = mountCard({
      identity: { kind: 'pair', base: 'BTC', quote_currency: 'EUR' },
    })
    await wrapper.find('.icard__toggle').trigger('click')

    expect(wrapper.find('.isin__add').exists()).toBe(false)
    // Ein Strich wie in jeder anderen leeren Zelle, der Grund daneben.
    // Wie in der Tabelle: stiller Strich, Erklaerung am Label.
    expect(wrapper.find('.dim').text()).toBe(i18n.global.t('common.noValue'))
    expect(
      wrapper.findAllComponents(InfoHint).map((hint) => hint.props('text')),
    ).toContain(i18n.global.t('table.noIsinReason'))
  })

  /*
   * Dieselbe Regel wie in der Tabelle: Ein Papier, das nur ueber seine ISIN
   * identifiziert ist, hat kein Boersensymbol — und die Karte darf keins
   * behaupten, nur weil `instruments.symbol` dort die ISIN traegt.
   */
  it('behauptet bei einer isin_only-Identitaet kein Symbol', () => {
    const wrapper = mountCard({
      symbol: 'DE0001102531',
      identity: { kind: 'isin_only', isin: 'DE0001102531' },
    })

    expect(wrapper.find('.icard__symbol').text()).toContain(i18n.global.t('common.noValue'))
    expect(wrapper.find('.icard__symbol').text()).not.toContain('DE0001102531')
  })

  /*
   * **Die Karte hat keine Spaltenkoepfe.** Was in der Tabelle einmal ueber der
   * Spalte steht, hat hier keinen Ort — ohne diese Zeile bliebe der Strich auf
   * Touch und fuer die Tastatur unerklaert. Geprueft wird der Text aus dem
   * Katalog, nicht seine Formulierung: Beide Darstellungsformen ziehen aus
   * derselben Quelle, und genau das ist die Zusage.
   */
  it('erklaert den fehlenden Symbolstrich auch ohne Spaltenkopf', () => {
    const wrapper = mountCard({
      symbol: 'DE0001102531',
      identity: { kind: 'isin_only', isin: 'DE0001102531' },
    })

    expect(
      wrapper.findAllComponents(InfoHint).map((hint) => hint.props('text')),
    ).toContain(i18n.global.t('table.noSymbolReason'))
  })

  /*
   * Die Gegenprobe: Ein Papier **mit** Symbol traegt den Hinweis nicht. Ohne
   * sie waere der Fall darueber auch gruen, wenn die Karte ihn immer zeigte.
   */
  it('zeigt den Symbol-Hinweis nicht, wo ein Symbol steht', () => {
    const wrapper = mountCard({
      symbol: 'EUNL.DE',
      identity: { kind: 'listed', ticker: 'EUNL', mic: 'XETR', isin: 'IE00B4L5Y983' },
    })

    expect(
      wrapper.findAllComponents(InfoHint).map((hint) => hint.props('text')),
    ).not.toContain(i18n.global.t('table.noSymbolReason'))
  })

  it('zeichnet auch eine Gattung ohne eigene Farbe als Pille aus', () => {
    const wrapper = mountCard({
      symbol: 'BTC-EUR',
      type: 'crypto',
      identity: { kind: 'pair', base: 'BTC', quote_currency: 'EUR' },
    })
    const badge = wrapper.find('.icard__type')

    expect(badge.exists()).toBe(true)
    expect(badge.classes()).toContain('crypto')
  })

})
