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

function render(locale: 'de' | 'en' = 'de', attached = false) {
  i18n.global.locale.value = locale
  return mount(ExchangesPanel, {
    attachTo: attached ? document.body : undefined,
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
          region: 'usa', currency: 'USD', provenance: { kind: 'core' as const }, support: [
            { source: 'metadata-only', role: 'etf_meta', scope: 'market' as const, usable: true },
            { source: 'offline', role: 'quotes', scope: 'market' as const, usable: false },
          ] },

      ],
    } },
  })
}

describe('ExchangesPanel', () => {
  it.each(['de', 'en'] as const)('zeigt MIC, Suffix und kompakte Kursquelle in %s', async (locale) => {
    const wrapper = render(locale)
    await wrapper.find('[role=switch]').trigger('click')
    expect(wrapper.text()).toContain('XBUD')
    expect(wrapper.text()).toContain(i18n.global.t('exchanges.default'))
    const headings = wrapper.findAll('th').map(cell => cell.text())
    const suffixColumn = headings.indexOf(i18n.global.t('exchanges.colSuffix'))
    expect(suffixColumn).toBeGreaterThan(-1)
    const cells = wrapper.find('.n-data-table-tbody tr').findAll('td')
    expect(cells[suffixColumn]!.text()).toBe('.XBUD')
    expect(cells[headings.indexOf(i18n.global.t('exchanges.colExchange'))]!.text()).not.toContain('.XBUD')
    expect(wrapper.findAll('.exchanges__hint strong').map(item => item.text())).toEqual(['SAP.DE', 'SAP.XETR'])
    expect(headings).toEqual([
      i18n.global.t('exchanges.mic'), i18n.global.t('exchanges.colSuffix'),
      i18n.global.t('exchanges.colExchange'), i18n.global.t('exchanges.support'),
    ])
    expect(cells[3]!.text()).toBe('regional')
    expect(wrapper.text()).not.toContain('archive')
    expect(wrapper.text()).not.toContain(i18n.global.t('roles.daily'))
    expect(wrapper.find('.n-data-table-tbody tr').classes()).not.toContain('exchanges__uncovered')
    expect(wrapper.findAll('.n-data-table-tbody tr')[1]!.classes()).toContain('exchanges__uncovered')
    const nasdaq = wrapper.findAll('.n-data-table-tbody tr')[1]!.findAll('td')
    expect(nasdaq[1]!.text()).toBe('.XNAS')
    expect(wrapper.text()).toContain('legacy')
    expect(wrapper.text()).toContain(i18n.global.t('exchanges.unspecified'))
    expect(wrapper.text()).toContain(i18n.global.t('exchanges.noSupport'))
    expect(wrapper.text()).not.toContain('exchanges.regions.')
    wrapper.unmount()
  })

  it('findet Handelsplätze anhand von MIC, Name und Quelle', async () => {
    const wrapper = render()
    await wrapper.find('[role=switch]').trigger('click')
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
    await wrapper.find('[role=switch]').trigger('click')
    compact.value = true
    await wrapper.find('input').setValue('Budapest')
    expect(wrapper.find('.n-data-table').exists()).toBe(false)
    expect(wrapper.find('.exchanges__venues .n-list-item').classes()).not.toContain('exchanges__uncovered')
    expect(wrapper.find('.exchanges__venues').text()).toContain('regional')
    expect(wrapper.find('.exchanges__suffix strong').text()).toBe('.XBUD')
    await wrapper.setProps({ data: { default_exchange: 'XBUD', default_exchange_kind: 'unknown',
      unspecified_support: [], catalog: [] } })
    expect(wrapper.text()).not.toContain('regional')
    expect(wrapper.text()).not.toContain('legacy')
    await wrapper.find('input').setValue('')
    expect(wrapper.text()).toContain(i18n.global.t('exchanges.empty'))
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('reload')).toHaveLength(1)
    wrapper.unmount()
  })
})

it.each(['de', 'en'] as const)('trennt Online und reines Dateiprofil in %s', async (locale) => {
  compact.value = true
  const wrapper = render(locale)
  const row = wrapper.props('data')!.catalog[0]!
  if (row.kind !== 'exchange') throw new Error('Expected exchange fixture')
  await wrapper.setProps({ data: { default_exchange: 'XBUD', default_exchange_kind: 'exchange',
    unspecified_support: [], catalog: [{ ...row, support: [
      { source: 'yaml-file', role: 'quotes', scope: 'inventory', usable: true },
      { source: 'yaml-file', role: 'daily', scope: 'inventory', usable: true },
      { source: 'online', role: 'quotes', scope: 'market', usable: true },
    ] }] } })
  expect(wrapper.find('.exchanges__venues').text()).toContain(`${i18n.global.t('exchanges.yamlFile')} · online`)
  expect(wrapper.find('.exchanges__venues').text()).not.toContain(i18n.global.t('roles.daily'))
  await wrapper.setProps({ data: { ...wrapper.props('data')!, catalog: [{ ...row, support: [
    { source: 'yaml-file', role: 'quotes', scope: 'inventory', usable: true },
  ] }] } })
  expect(wrapper.find('.exchanges__venues').text()).not.toContain('online')
  expect(wrapper.find('.exchanges__venues').text()).toContain(i18n.global.t('exchanges.yamlFile'))
  expect(wrapper.find('.exchanges__source-info').text()).toContain(i18n.global.t('exchanges.yamlRefreshInfo'))
  expect(wrapper.find('.exchanges__source-info').text()).not.toContain(i18n.global.t('exchanges.marketInfo'))
  wrapper.unmount()
})


it('verlinkt die Kursquelle zum fokussierbaren Infobereich ohne Routenwechsel', async () => {
  const wrapper = render('de', true)
  const target = wrapper.find<HTMLElement>('#exchange-source-regional')
  const scroll = vi.fn()
  target.element.scrollIntoView = scroll
  const hash = window.location.hash
  const link = wrapper.find('a[href="#/exchanges?source=regional"]')
  await link.trigger('click')
  expect(scroll).toHaveBeenCalledWith({ block: 'start' })
  expect(document.activeElement).toBe(target.element)
  expect(window.location.hash).toBe(hash)
  expect(wrapper.find('.exchanges__source-info').text()).toContain(i18n.global.t('exchanges.marketInfo'))
  wrapper.unmount()
})


it('graut auf Mobilgeräten Börsen ohne aktive Kursquelle aus', async () => {
  compact.value = true
  const wrapper = render()
  expect(wrapper.findAll('.exchanges__venues .n-list-item')).toHaveLength(1)
  await wrapper.find('[role=switch]').trigger('click')
  expect(wrapper.findAll('.exchanges__venues .n-list-item')[1]!.classes()).toContain('exchanges__uncovered')
  wrapper.unmount()
})


it('zeigt standardmäßig nur abgedeckte Börsen und bietet den vollständigen Katalog an', async () => {
  const wrapper = render()
  expect(wrapper.findAll('.n-data-table-tbody tr')).toHaveLength(1)
  await wrapper.find('[role=switch]').trigger('click')
  expect(wrapper.findAll('.n-data-table-tbody tr')).toHaveLength(2)
  await wrapper.find('[role=switch]').trigger('click')
  expect(wrapper.findAll('.n-data-table-tbody tr')).toHaveLength(1)
  wrapper.unmount()
})


it('zeigt den Schalter nur bei nicht abgedeckten Börsen', async () => {
  const wrapper = render()
  expect(wrapper.find('[role=switch]').exists()).toBe(true)
  const initial = wrapper.props('data')!
  await wrapper.setProps({ data: { ...initial, catalog: [initial.catalog[0]!] } })
  expect(wrapper.find('[role=switch]').exists()).toBe(false)
  await wrapper.setProps({ data: initial })
  expect(wrapper.find('[role=switch]').exists()).toBe(true)
  wrapper.unmount()
})
