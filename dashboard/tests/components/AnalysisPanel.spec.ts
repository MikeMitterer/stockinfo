import { mount } from '@vue/test-utils'
import { NSelect } from 'naive-ui'
import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

vi.mock('../../src/composables/useAnalysis', () => ({
  useAnalysis: () => ({
    result: ref({
      symbol: 'EUNL.DE',
      isin: 'IE00B4L5Y983',
      total: 1.2,
      stages: [
        { role: 'quotes', source: 'yaml-file', seconds: 0.5, status: 'ok', detail: null },
        { role: 'daily', source: 'yaml-file', seconds: 0, status: 'skipped', detail: null },
      ],
    }),
    loading: ref(false),
    error: ref(null),
    analyze: vi.fn(),
  }),
}))

import AnalysisPanel from '../../src/components/AnalysisPanel.vue'
import { i18n } from '../../src/i18n'

describe('AnalysisPanel', () => {
  it('rendert die Stages eines Ergebnisses', () => {
    const wrapper = mount(AnalysisPanel, {
      global: { plugins: [i18n] },
      props: { instruments: [] },
    })
    expect(wrapper.text()).toContain('yaml-file')
    expect(wrapper.text()).toContain('0.50')
    expect(wrapper.text()).toContain('1.20')
  })

  /*
   * Die Rolle wird übersetzt, der Quellenname nicht. Er soll in `sources.yaml`
   * wiederzufinden sein — ein übersetztes „Datei" führte beim Suchen ins Leere.
   */
  it('übersetzt Rolle und Status, lässt den Quellennamen roh', () => {
    const text = mount(AnalysisPanel, {
      global: { plugins: [i18n] },
      props: { instruments: [] },
    }).text()

    expect(text).toContain('Quote')
    expect(text).toContain('Daily series')
    expect(text).toContain('not asked')
    expect(text).not.toContain('analysis.role.')
  })

  /*
   * **Der Platzhalter hängt am `null`, nicht am Leerstring.** Naive zeigt ihn
   * nur, solange kein Wert gesetzt ist; ein `''` *ist* ein Wert. Im Browserlauf
   * zu T-50 stand das Feld deshalb leer und ohne Beschriftung da und trug ein
   * Löschsymbol für eine Auswahl, die niemand getroffen hatte.
   *
   * Geprüft wird der Wert, den die Komponente an das Auswahlfeld reicht — der
   * gerenderte Text belegte nichts: Naive malt den Platzhalter erst im
   * echten Popover-Layout, das `jsdom` nicht aufbaut.
   */
  it('reicht dem Auswahlfeld kein leeres Symbol als Auswahl', () => {
    const wrapper = mount(AnalysisPanel, {
      global: { plugins: [i18n] },
      props: { instruments: [] },
    })

    expect(wrapper.findComponent(NSelect).props('value')).toBeNull()
  })

  /*
   * Die Gegenprobe zur Zeile darüber, und sie ist der Grund für die
   * Wächterzeile: Ein Papier **ohne** Börsensymbol trägt `null`. Ohne Wächter
   * trifft die leere Auswahl genau darauf, `target` wird wahr — und die
   * Schaltfläche gibt sich frei, obwohl niemand etwas gewählt hat.
   *
   * **Beobachtet wird die Schaltfläche, nicht der Text.** Der erste Anlauf
   * dieses Tests prüfte, ob der Name des Papiers auftaucht; er tut es nie,
   * egal wie die Auswahl steht. Der Test war grün und hat den Mutanten
   * durchgelassen.
   */
  it('gibt die Schaltfläche ohne Auswahl nicht frei, auch nicht bei einem Papier ohne Symbol', () => {
    const wrapper = mount(AnalysisPanel, {
      global: { plugins: [i18n] },
      props: {
        instruments: [
          {
            symbol: null,
            name: 'Bundesrepublik Deutschland',
            identity: { kind: 'isin_only', isin: 'DE0001102531' },
          } as never,
        ],
      },
    })

    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
  })
})
