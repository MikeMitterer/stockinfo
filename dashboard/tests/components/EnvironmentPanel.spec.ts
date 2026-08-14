import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'

import EnvironmentPanel from '../../src/components/EnvironmentPanel.vue'
import { i18n } from '../../src/i18n'

const env = {
  version: '0.5.0',
  database_path: 'data/stockinfo.db',
  cache_ttl_hours: 6,
  refresh_interval_hours: 6,
  metadata_ttl_days: 7,
  default_exchange: 'XETR',
  strict_exchange: false,
  host: '0.0.0.0',
  port: 8000,
  openfigi_key_set: false,
  extraetf_etf_url: 'https://extraetf.com/de/etf-profile/{isin}',
  extraetf_stock_url: 'https://extraetf.com/de/stock-profile/{isin}',
  yahoo_url: 'https://de.finance.yahoo.com/quote/{symbol}/',
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
})

describe('EnvironmentPanel', () => {
  it('verlinkt .env.example ins GH-Repo (neuer Tab, noopener)', () => {
    const wrapper = mount(EnvironmentPanel, { props: { env }, global: { plugins: [i18n] } })
    const link = wrapper.find('.source-note a')
    expect(link.exists()).toBe(true)
    expect(link.text()).toBe('.env.example')
    expect(link.attributes('href')).toContain('/MikeMitterer/stockinfo/blob/master/.env.example')
    expect(link.attributes('target')).toBe('_blank')
    expect(link.attributes('rel')).toContain('noopener')
  })

  it('erklärt die Strikte Börse (Fehler statt Fallback)', () => {
    const wrapper = mount(EnvironmentPanel, { props: { env }, global: { plugins: [i18n] } })
    expect(wrapper.find('.fieldnote').text()).toContain('404')
  })
})
