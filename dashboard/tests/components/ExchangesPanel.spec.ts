import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import ExchangesPanel from '../../src/components/ExchangesPanel.vue'
import { i18n } from '../../src/i18n'

const compact = ref(false)
vi.mock('@mmit/ux-foundation', async (original) => ({
  ...await original<object>(), useIsCompact: () => compact,
}))
afterEach(() => { compact.value = false })

function render(locale: 'de' | 'en' = 'de') {
  i18n.global.locale.value = locale
  return mount(ExchangesPanel, {
    global: { plugins: [i18n] },
    props: { data: {
      default_exchange: 'XBUD', default_exchange_kind: 'exchange' as const,
      unspecified_support: [{ source: 'legacy', role: 'quotes', usable: true }],
      catalog: [
        { kind: 'exchange' as const, mic: 'XBUD', alias: 'XBUD', name: 'Budapest',
          region: 'europe', currency: 'HUF', provenance: { kind: 'plugin' as const, id: 'regional' },
          declared_by: ['regional', 'shared'], support: [
            { source: 'regional', role: 'quotes', scope: 'market' as const, usable: true },
            { source: 'archive', role: 'daily', scope: 'inventory' as const, usable: false },
          ] },
        { kind: 'exchange' as const, mic: 'XNAS', alias: null, name: 'NASDAQ',
          region: 'usa', currency: 'USD', provenance: { kind: 'core' as const }, support: [] },
        { kind: 'collector' as const, code: 'US', name: 'NYSE / NASDAQ', region: 'usa',
          currency: 'USD', members: ['XNAS', 'XNYS'], provenance: { kind: 'core' as const } },
      ],
    } },
  })
}

describe('ExchangesPanel', () => {
  it.each(['de', 'en'] as const)('zeigt dynamische MICs und Rollen in %s', (locale) => {
    const wrapper = render(locale)
    expect(wrapper.text()).toContain('XBUD')
    expect(wrapper.text()).toContain('shared')
    expect(wrapper.text()).toContain(i18n.global.t('roles.quotes'))
    expect(wrapper.text()).toContain(i18n.global.t('roles.daily'))
    expect(wrapper.text()).toContain(i18n.global.t('exchanges.default'))
    const headings = wrapper.findAll('th').map(cell => cell.text())
    const suffixColumn = headings.indexOf(i18n.global.t('exchanges.colSuffix'))
    expect(suffixColumn).toBeGreaterThan(-1)
    const cells = wrapper.find('.n-data-table-tbody tr').findAll('td')
    expect(cells[suffixColumn]!.text()).toBe('.XBUD')
    expect(cells[headings.indexOf(i18n.global.t('exchanges.colExchange'))]!.text()).not.toContain('.XBUD')
    const inactive = wrapper.findAll('.exchange-support__item').find(row => row.text().includes('archive'))!
    expect(inactive.text()).toContain(i18n.global.t('exchanges.inactive'))
    expect(inactive.text()).toContain(i18n.global.t('exchanges.inventory'))
    expect(inactive.text()).not.toContain(i18n.global.t('exchanges.declared'))
    expect(wrapper.text()).toContain('legacy')
    expect(wrapper.text()).toContain(i18n.global.t('exchanges.unspecified'))
    expect(wrapper.text()).toContain(i18n.global.t('exchanges.noSupport'))
    expect(wrapper.text()).not.toContain('exchanges.regions.')
    wrapper.unmount()
  })

  it('trennt Sammelcodes, zeigt Mitglieder und findet MIC, Name und Quelle', async () => {
    const wrapper = render()
    expect(wrapper.find('.exchanges__collectors').text()).toContain('XNAS, XNYS')
    expect(wrapper.find('.n-data-table').text()).not.toContain('NYSE / NASDAQ')
    for (const query of ['xbud', 'Budapest', 'shared', 'archive']) {
      await wrapper.find('input').setValue(query)
      expect(wrapper.find('.n-data-table').text()).toContain('Budapest')
      expect(wrapper.find('.n-data-table').text()).not.toContain('NASDAQ')
    }
    await wrapper.find('input').setValue('kein-treffer')
    expect(wrapper.text()).toContain(i18n.global.t('exchanges.empty'))
    wrapper.unmount()
  })

  it('ersetzt entfernte Pluginangaben und erhält die Suche in kompakter Ansicht', async () => {
    const wrapper = render()
    compact.value = true
    await wrapper.find('input').setValue('Budapest')
    expect(wrapper.find('.n-data-table').exists()).toBe(false)
    expect(wrapper.find('.exchanges__venues').text()).toContain('regional')
    expect(wrapper.find('.exchanges__suffix strong').text()).toBe('.XBUD')
    await wrapper.setProps({ data: { default_exchange: 'US', default_exchange_kind: 'collector',
      unspecified_support: [], catalog: [wrapper.props('data')!.catalog[2]!] } })
    expect(wrapper.text()).not.toContain('regional')
    expect(wrapper.text()).not.toContain('legacy')
    await wrapper.find('input').setValue('')
    expect(wrapper.find('.exchanges__collectors').text()).toContain(i18n.global.t('exchanges.default'))
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('reload')).toHaveLength(1)
    wrapper.unmount()
  })
})
