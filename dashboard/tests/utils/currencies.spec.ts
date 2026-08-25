import { describe, expect, it } from 'vitest'

import { currenciesFromExchanges } from '../../src/utils/currencies'

const core = { kind: 'core' as const }

const data = {
  default_exchange: 'XETR',
  default_exchange_kind: 'exchange' as const,
  catalog: [
    { kind: 'exchange' as const, mic: 'XETR', alias: 'DE', name: 'Xetra', region: 'germany', currency: 'EUR', provenance: core },
    { kind: 'exchange' as const, mic: 'XLON', alias: 'L', name: 'London', region: 'europe', currency: 'GBp', provenance: core },
    { kind: 'exchange' as const, mic: 'XNAS', alias: null, name: 'NASDAQ', region: 'usa', currency: 'USD', provenance: core },
    { kind: 'exchange' as const, mic: 'XFRA', alias: 'F', name: 'Frankfurt', region: 'germany', currency: 'EUR', provenance: core },
    // Der Sammelcode zählt für die Währungsauswahl mit — er trägt eine, auch
    // wenn er kein Handelsplatz ist.
    { kind: 'collector' as const, code: 'US', name: 'NYSE / NASDAQ', region: 'usa', currency: 'USD', members: ['XNAS'], provenance: core },
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
