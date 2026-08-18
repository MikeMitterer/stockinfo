import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import InfoHint from '../../src/components/InfoHint.vue'
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

  /*
   * Die Erklärung bleibt immer erreichbar, steht aber nicht mehr dauerhaft im
   * Text: Sie beantwortet eine Frage, die man einmal hat und danach nicht mehr,
   * und nahm als Dauertext mehr Platz ein als die Kennzahlen darüber. Sie sitzt
   * jetzt im Fragezeichen hinter „Stand der Quelle" — genau die Bauform, die
   * ux-standards unter „Erklärungen in der App" dafür vorsieht.
   */
  it('hält die allgemeine Erklärung im Hinweis statt im Dauertext', () => {
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: {
        item: makeInstrument({
          type: 'etf',
          isin: 'IE00B4L5Y983',
          ter: 0.2,
          volatility: 12,
          accumulating: true,
          provider: 'iShares',
          replication: 'physisch',
          fund_size: 100,
          fund_domicile: 'IE',
          fund_currency: 'EUR',
        }),
      },
    })

    expect(wrapper.getComponent(InfoHint).props('text')).toBe(i18n.global.t('drilldown.explain'))
    expect(wrapper.text()).not.toContain(i18n.global.t('drilldown.explain'))
    // Keiner der vier Sonderfälle greift hier — ETF, europäisch, Quelle voll.
    expect(wrapper.text()).not.toContain(i18n.global.t('drilldown.notEtf'))
    expect(wrapper.text()).not.toContain(i18n.global.t('drilldown.noIsin'))
    expect(wrapper.text()).not.toContain(i18n.global.t('drilldown.noEuropeanSource'))
    expect(wrapper.text()).not.toContain(i18n.global.t('drilldown.sourceEmpty'))
  })

  /*
   * Nacharbeit Sichtprüfung, I2 (Gesamtprüfung): Das Backend überspringt
   * justETF aus drei Gründen (`app/services/quote_service.py:137`:
   * `if instrument_type == "etf" and isin:`) — kein ETF, keine ISIN, oder
   * nicht-europäische ISIN. Die Schublade kannte bisher nur den dritten.
   * Eine Aktie mit deutscher (europäischer) ISIN bekam fälschlich „Die Quelle
   * wurde abgefragt, hat aber nichts geliefert" — sie wurde nie abgefragt.
   */
  it('erklärt, dass eine Aktie gar nicht bei justETF abgefragt wird', () => {
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: { item: makeInstrument({ type: 'stock', isin: 'DE0007164600', ter: null }) },
    })

    expect(wrapper.text()).toContain(i18n.global.t('drilldown.notEtf'))
    expect(wrapper.text()).not.toContain(i18n.global.t('drilldown.sourceEmpty'))
  })

  // Ein Papier ohne ISIN bekam fälschlich „Diese ISIN liegt außerhalb" — es
  // gibt gar keine ISIN, die außerhalb liegen könnte.
  it('erklärt, dass ein ETF ohne ISIN gar nicht abgefragt wird', () => {
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: { item: makeInstrument({ type: 'etf', isin: null, ter: null }) },
    })

    expect(wrapper.text()).toContain(i18n.global.t('drilldown.noIsin'))
    expect(wrapper.text()).not.toContain(i18n.global.t('drilldown.noEuropeanSource'))
  })

  it('erklärt, warum die Quelle nichts beigesteuert hat', () => {
    // Nicht-europäisches Domizil wird bewusst übersprungen — genau diese
    // Erklärung fehlte dem Nutzer vor Task 8.
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: { item: makeInstrument({ type: 'etf', isin: 'US0378331005', ter: null }) },
    })

    expect(wrapper.text()).toContain(i18n.global.t('drilldown.noEuropeanSource'))
  })

  it('erklärt eine leere Quelle bei europäischem Domizil', () => {
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: {
        item: makeInstrument({ type: 'etf', isin: 'IE00B4L5Y983', ter: null, volatility: null }),
      },
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

  /*
   * Der Hinweis hängt am Zeitstempel — den gibt es aber nicht immer (ein
   * Papier, das noch nie abgefragt wurde). Er darf deshalb nicht mit der Zeile
   * verschwinden: Gerade wer eine leere Schublade vor sich hat, will wissen,
   * woher hier etwas herkommen soll.
   */
  it('behält den Hinweis, auch wenn es keinen Zeitstempel gibt', () => {
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: { item: makeInstrument({ meta_fetched_at: null }) },
    })

    expect(wrapper.text()).not.toContain(i18n.global.t('drilldown.fetchedAt'))
    expect(wrapper.getComponent(InfoHint).props('text')).toBe(i18n.global.t('drilldown.explain'))
  })

  /*
   * Die Spec verlangt, dass die Schublade nicht nur den Zeitpunkt, sondern auch
   * die **Quelle** nennt: `yfinance` allein heißt „justETF war nicht dabei",
   * `yfinance+justetf` heißt „die ETF-Extras kommen von dort". Ohne das ist der
   * Zeitstempel eine Zahl ohne Absender.
   */
  it('nennt die Quelle, aus der die Metadaten stammen', () => {
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: { item: makeInstrument({ source: 'yfinance+justetf' }) },
    })

    expect(wrapper.text()).toContain(i18n.global.t('drilldown.source'))
    expect(wrapper.text()).toContain('yfinance+justetf')
  })

  // Ohne gespeicherte Quelle (Instrument aus einer Datenbank vor der Migration)
  // bleibt die Zeile weg — eine Beschriftung ohne Wert erklärt nichts.
  it('lässt die Quellenzeile weg, wenn nichts gespeichert ist', () => {
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: { item: makeInstrument({ source: null }) },
    })

    expect(wrapper.text()).not.toContain(i18n.global.t('drilldown.source'))
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
