import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import InfoHint from '../../src/components/InfoHint.vue'
import InstrumentDrilldown from '../../src/components/InstrumentDrilldown.vue'
import OpenDetails from '../../src/components/OpenDetails.vue'
import { i18n } from '../../src/i18n'
import type { DetailValue } from '../../src/types'
import { makeInstrument } from '../fixtures/instrument'

/** Ein Detailwert aus einer Quelle — mit den Feldern, auf die es hier ankommt. */
function fromSource(source: string, value: DetailValue['value'], asOf: string | null = null): DetailValue {
  return {
    value, unit: null, currency: null, origin: 'provider', source, as_of: asOf,
    shadowed: false, manual_value: null, manual_currency: null,
  }
}

/** Mountet den Detailbereich; `OpenDetails` ist eine Attrappe, der Feldkatalog bleibt außen vor. */
function mountDrilldown(props: InstanceType<typeof InstrumentDrilldown>['$props']) {
  return mount(InstrumentDrilldown, {
    global: { plugins: [i18n], stubs: { OpenDetails: true } },
    props,
  })
}

describe('InstrumentDrilldown', () => {
  it('nennt nur Quellen der tatsächlich gelieferten Detailwerte', () => {
    const wrapper = mountDrilldown({ item: makeInstrument({ source: 'risk-demo', details: {
      ter: fromSource('yaml-file', 0.2),
      provider: { ...fromSource('ignored', 'Test'), origin: 'manual', source: null, manual_value: 'Test' },
    } }) })

    expect(wrapper.get('.drilldown__source').text()).toContain('yaml-file')
    expect(wrapper.get('.drilldown__source').text()).not.toContain('risk-demo')
  })

  it.each([
    ['de', 'berechnet aus Tageskursen', 'Stand der Quelle: 01.10.2026'],
    ['en', 'calculated from daily closes', 'Source as of: Oct 1, 2026'],
  ])('benennt die berechnete Volatilität verständlich und mit Stand (%s)', (locale, source, asOf) => {
    const previousLocale = i18n.global.locale.value
    i18n.global.locale.value = locale as 'de' | 'en'
    const wrapper = mountDrilldown({ item: makeInstrument({ type: 'stock', meta_fetched_at: null, details: {
      volatility: fromSource('calculated', 26.11, '2026-10-01'),
    } }) })

    expect(wrapper.get('.drilldown__source .mono').text()).toBe(source)
    expect(wrapper.get('.drilldown__source').text()).toContain(asOf)
    i18n.global.locale.value = previousLocale
  })

  /*
   * Die Erklärung bleibt immer erreichbar, steht aber nicht dauerhaft im Text:
   * Sie beantwortet eine Frage, die man einmal hat und danach nicht mehr. Sie
   * sitzt im Hinweis hinter „Stand der Quelle" — die Bauform, die ux-standards
   * unter „Erklärungen in der App" dafür vorsieht.
   */
  it('hält die allgemeine Erklärung im Hinweis statt im Dauertext', () => {
    const wrapper = mountDrilldown({ item: makeInstrument({ details: { ter: fromSource('justetf', 0.2) } }) })

    expect(wrapper.getComponent(InfoHint).props('text')).toBe(i18n.global.t('drilldown.explain'))
    expect(wrapper.text()).not.toContain(i18n.global.t('drilldown.explain'))
    // `(i)` statt `?`: Der Satz ordnet den ganzen Detailbereich ein, er grenzt keinen Begriff ab.
    expect(wrapper.getComponent(InfoHint).props('icon')).toBe('info')
  })

  it('zeigt den Zeitpunkt der letzten Metadaten-Abfrage', () => {
    const wrapper = mountDrilldown({ item: makeInstrument({ meta_fetched_at: '2026-08-16T10:00:00Z' }) })

    expect(wrapper.text()).toContain(i18n.global.t('drilldown.fetchedAt'))
  })

  /*
   * Der Hinweis hängt am Zeitstempel — den gibt es aber nicht immer. Er darf
   * deshalb nicht mit der Zeile verschwinden: Gerade wer einen leeren
   * Detailbereich vor sich hat, will wissen, woher hier etwas kommen soll.
   */
  it('behält den Hinweis, auch wenn es keinen Zeitstempel gibt', () => {
    const wrapper = mountDrilldown({ item: makeInstrument({ meta_fetched_at: null, details: {} }) })

    expect(wrapper.text()).not.toContain(i18n.global.t('drilldown.fetchedAt'))
    expect(wrapper.getComponent(InfoHint).props('text')).toBe(i18n.global.t('drilldown.explain'))
  })

  // Ohne Quellenwert bleibt die Zeile weg — eine Beschriftung ohne Wert erklärt nichts.
  it('lässt die Quellenzeile weg, wenn keine Quelle etwas geliefert hat', () => {
    const wrapper = mountDrilldown({ item: makeInstrument({ details: {} }) })

    expect(wrapper.text()).not.toContain(i18n.global.t('drilldown.source'))
  })

  it('reicht ein commit-Ereignis der Felder unverändert nach oben durch', () => {
    const wrapper = mountDrilldown({ item: makeInstrument() })

    wrapper.getComponent(OpenDetails).vm.$emit('commit', { provider: 'Vanguard' })

    expect(wrapper.emitted('commit')?.[0]?.[0]).toEqual({ provider: 'Vanguard' })
  })

  it('reicht Vorschläge und Sperre an die Felder durch', () => {
    const fieldOptions = { provider: ['Vanguard', 'iShares'] }
    const wrapper = mountDrilldown({ item: makeInstrument(), busy: true, fieldOptions })

    const details = wrapper.getComponent(OpenDetails)
    expect(details.props('fieldOptions')).toEqual(fieldOptions)
    expect(details.props('busy')).toBe(true)
  })
})
