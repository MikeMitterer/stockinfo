import { describe, expect, it } from 'vitest'

import { currenciesFromExchanges } from '../../src/utils/currencies'

const data = {
  default_exchange: 'XETR',
  exchanges: [
    { mic: 'XETR', suffix: '.DE', name: 'Xetra', region: 'germany', currency: 'EUR' },
    { mic: 'XLON', suffix: '.L', name: 'London', region: 'europe', currency: 'GBp' },
    { mic: 'US', suffix: '', name: 'NYSE', region: 'usa', currency: 'USD' },
    { mic: 'XFRA', suffix: '.F', name: 'Frankfurt', region: 'germany', currency: 'EUR' },
  ],
}

describe('currenciesFromExchanges', () => {
  it('dedupliziert, sortiert und mappt GBp→GBP', () => {
    expect(currenciesFromExchanges(data)).toEqual(['EUR', 'GBP', 'USD'])
  })

  it('gibt [] zurück, wenn keine Daten vorliegen', () => {
    expect(currenciesFromExchanges(null)).toEqual([])
  })
})
