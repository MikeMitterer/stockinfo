import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import ExchangesPanel from '../../src/components/ExchangesPanel.vue'
import { i18n } from '../../src/i18n'

describe('ExchangesPanel', () => {
  const core = { kind: 'core' as const, id: null }

  it('rendert Börsen und markiert die Default-Börse', () => {
    const wrapper = mount(ExchangesPanel, {
      global: { plugins: [i18n] },
      props: { data: {
        default_exchange: 'XETR',
        default_exchange_kind: 'exchange' as const,
        catalog: [
          { kind: 'exchange' as const, mic: 'XETR', alias: 'DE', name: 'Xetra', region: 'germany', currency: 'EUR', provenance: core },
          { kind: 'exchange' as const, mic: 'XNAS', alias: '', name: 'NASDAQ', region: 'usa', currency: 'USD', provenance: core },
        ],
      } },
    })
    expect(wrapper.text()).toContain('Xetra')
    expect(wrapper.text()).toContain('NASDAQ')
    expect(wrapper.find('tr.is-default').text()).toContain('Xetra')
  })

  it('zeigt einen Sammelcode als solchen, nicht als Börse', () => {
    /*
     * Bis T-21 Teil 3 kam `US` als `mic: 'US'` herein und stand ununterscheidbar
     * zwischen den Handelsplätzen. Jetzt trägt die Zeile ein eigenes Merkmal
     * und seine Mitglieder im Titel.
     */
    const wrapper = mount(ExchangesPanel, {
      global: { plugins: [i18n] },
      props: { data: {
        default_exchange: 'US',
        default_exchange_kind: 'collector' as const,
        catalog: [
          { kind: 'collector' as const, code: 'US', name: 'NYSE / NASDAQ', region: 'usa', currency: 'USD', members: ['XNAS', 'XNYS'], provenance: core },
        ],
      } },
    })

    // Gegen den Katalog geprüft, nicht gegen ein deutsches Literal: Die
    // Sprache hängt an der Browsererkennung und wäre hier kein stabiles Orakel.
    const marker = i18n.global.t('exchanges.collector')

    expect(wrapper.text()).toContain('US')
    expect(wrapper.text()).toContain(marker)
    expect(wrapper.find('.badge.warn').attributes('title')).toBe('XNAS, XNYS')
    expect(wrapper.find('tr.is-default').text()).toContain('NYSE / NASDAQ')
  })
})
