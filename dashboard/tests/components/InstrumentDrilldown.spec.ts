import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import InfoHint from '../../src/components/InfoHint.vue'
import InstrumentDrilldown from '../../src/components/InstrumentDrilldown.vue'
import { i18n } from '../../src/i18n'
import { makeInstrument } from '../fixtures/instrument'

describe('InstrumentDrilldown', () => {
  it('nennt nur Quellen der tatsächlich gelieferten Detailwerte', () => {
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n], stubs: { OpenDetails: true } },
      props: { item: makeInstrument({ source: 'risk-demo', details: {
        ter: { value: 0.2, unit: 'percent', currency: null, origin: 'provider',
          source: 'yaml-file', as_of: null, shadowed: false, manual_value: null, manual_currency: null },
        provider: { value: 'Test', unit: null, currency: null, origin: 'manual',
          source: null, as_of: null, shadowed: false, manual_value: 'Test', manual_currency: null },
      } }) },
    })
    expect(wrapper.get('.drilldown__source').text()).toContain('yaml-file')
    expect(wrapper.get('.drilldown__source').text()).not.toContain('risk-demo')
  })

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
  /*
   * Die Fläche hinter einem Feld ist kein Schmuck, sondern eine Aussage: „hier
   * lässt sich etwas eintragen". Trüge sie jedes Feld, sagte sie nichts — die
   * Quelle hat Vorrang, und wo sie liefert, ist nichts zu tun.
   */
  it('hebt nur die Felder hervor, die sich tatsächlich ändern lassen', () => {
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: {
        item: makeInstrument({
          type: 'etf',
          isin: 'IE00B4L5Y983',
          // Kommt aus der Quelle → gesperrt, also keine Fläche.
          ter: 0.2,
          provider: 'iShares',
          // Lücken der Quelle → von Hand pflegbar, also Fläche.
          fund_domicile: null,
          fund_currency: null,
          replication: null,
          fund_size: null,
          volatility: null,
          accumulating: null,
        }),
      },
    })

    const fields = wrapper.findAll('.drilldown__field')
    const editableFields = fields.filter((field) =>
      field.classes().includes('drilldown__field--editable'),
    )

    expect(fields).toHaveLength(8)
    expect(editableFields).toHaveLength(6)
  })

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
    /*
     * `(i)` statt `?`: Hier ist kein Begriff abzugrenzen — der Satz ordnet die
     * ganzen Detailbereich ein. Ein Fragezeichen kündigt ein Missverständnis an, ein
     * (i) eine Auskunft.
     */
    expect(wrapper.getComponent(InfoHint).props('icon')).toBe('info')
    // Keiner der drei Sonderfälle greift hier — ETF, mit ISIN, Quelle voll.
    expect(wrapper.text()).not.toContain(i18n.global.t('drilldown.notEtf'))
    expect(wrapper.text()).not.toContain(i18n.global.t('drilldown.noIsin'))
    expect(wrapper.text()).not.toContain(i18n.global.t('drilldown.nothingProvided'))
  })

  /*
   * Das Backend überspringt die Metadatenquelle aus zwei Gründen
   * (`app/services/quote_service.py`: `if instrument_type == "etf":` und die
   * ISIN daneben) — kein ETF, oder keine ISIN. Eine Aktie bekam vorher
   * fälschlich „hat nichts geliefert"; sie wurde nie abgefragt.
   *
   * Ein dritter Grund ist seit T-37 weg: Er prüfte über `isEuropeanIsin`
   * justETFs Zuständigkeitsregel, im Frontend nachgebaut — im CSV-Profil
   * schlicht falsch.
   */
  it('erklärt, dass eine Aktie gar nicht abgefragt wird', () => {
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: { item: makeInstrument({ type: 'stock', isin: 'DE0007164600', ter: null }) },
    })

    expect(wrapper.text()).toContain(i18n.global.t('drilldown.notEtf'))
    expect(wrapper.text()).not.toContain(i18n.global.t('drilldown.nothingProvided'))
  })

  // Alle Nicht-ETF-Gattungen teilen denselben Hinweis; keine darf darin als
  // Aktie bezeichnet werden.
  it.each(['stock', 'bond', 'crypto', 'etc', 'fund'])(
    'erklärt bei %s, ohne die Gattung zu behaupten',
    (type) => {
      const wrapper = mount(InstrumentDrilldown, {
        global: { plugins: [i18n] },
        props: { item: makeInstrument({ type, isin: 'DE0001102531', ter: null }) },
      })

      expect(wrapper.text()).toContain(i18n.global.t('drilldown.notEtf'))
      for (const locale of ['de', 'en'] as const) {
        expect(i18n.global.t('drilldown.notEtf', {}, { locale })).not.toMatch(
          /Aktie|stock/i,
        )
      }
    },
  )

  // Ein Papier ohne ISIN bekam fälschlich „Diese ISIN liegt außerhalb" — es
  // gibt gar keine ISIN, die außerhalb liegen könnte.
  it('erklärt, dass ein ETF ohne ISIN gar nicht abgefragt wird', () => {
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: { item: makeInstrument({ type: 'etf', isin: null, ter: null }) },
    })

    expect(wrapper.text()).toContain(i18n.global.t('drilldown.noIsin'))
    expect(wrapper.text()).not.toContain(i18n.global.t('drilldown.nothingProvided'))
  })

  /*
   * **Zwei Fälle, eine Aussage — und das ist seit T-37 Absicht.**
   *
   * Vorher bekam die US-ISIN „justETF deckt nur europäische UCITS-ETFs ab"
   * und die europäische „Die Quelle wurde abgefragt, hat aber nichts
   * geliefert". Der erste Satz war justETFs Zuständigkeitsregel, im Frontend
   * nachgebaut — im CSV-Profil schlicht falsch, denn `metadata-file` kennt
   * keine solche Grenze und **hätte** geantwortet. Der zweite behauptete
   * „wurde abgefragt", was die Oberfläche gar nicht weiß.
   *
   * Beide Papiere prüfen deshalb denselben Text. Dass sie es tun, ist der
   * Beleg für die Verschmelzung; eine der beiden Zeilen zu streichen hätte
   * genau das verloren.
   */
  it.each([
    ['nicht-europäische ISIN', 'US0378331005'],
    ['europäische ISIN', 'IE00B4L5Y983'],
  ])('sagt bei %s dasselbe, weil mehr niemand weiß', (_scenario, isin) => {
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: {
        item: makeInstrument({ type: 'etf', isin, ter: null, volatility: null }),
      },
    })

    expect(wrapper.text()).toContain(i18n.global.t('drilldown.nothingProvided'))
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
   * verschwinden: Gerade wer einen leeren Detailbereich vor sich hat, will wissen,
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
   * Die Spec verlangt, dass der Detailbereich nicht nur den Zeitpunkt, sondern auch
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
