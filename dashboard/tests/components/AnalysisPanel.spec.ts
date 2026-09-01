import { mount } from '@vue/test-utils'
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
})
