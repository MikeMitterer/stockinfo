import { describe, expect, it } from 'vitest'

import { buildFieldOptions } from '../../src/utils/fieldOptions'
import type { ExchangesResponse } from '../../src/types'
import { makeInstrument } from '../fixtures/instrument'

const core = { kind: 'core' as const, id: null }

const exchanges: ExchangesResponse = {
  default_exchange: 'XETR',
  default_exchange_kind: 'exchange',
  catalog: [
    { kind: 'exchange', mic: 'XETR', alias: 'DE', name: 'Xetra', region: 'germany', currency: 'EUR', provenance: core },
    { kind: 'exchange', mic: 'XLON', alias: 'L', name: 'London', region: 'europe', currency: 'GBp', provenance: core },
  ],
}

/*
 * Diese Funktion ist der einzige Ort, an dem die vier Vorschlagslisten der
 * Detailbereich gebildet werden (Task 8, Teil 4) — `AppDashboard.vue` ruft sie
 * einmal auf, nicht jede Zeile für sich.
 */
describe('buildFieldOptions', () => {
  it('leitet die Fondswährung aus der Börsentabelle ab', () => {
    const options = buildFieldOptions([], exchanges)

    expect(options.fund_currency).toEqual(['EUR', 'GBP'])
  })

  it('leitet Anbieter, Replikationsart und Fondsdomizil aus den Instrumenten ab', () => {
    const instruments = [
      makeInstrument({ symbol: 'A', provider: 'iShares', replication: 'physisch', fund_domicile: 'IE' }),
      makeInstrument({ symbol: 'B', provider: 'Vanguard', replication: 'synthetisch', fund_domicile: 'LU' }),
    ]

    const options = buildFieldOptions(instruments, exchanges)

    expect(options.provider).toEqual(['Vanguard', 'iShares'])
    expect(options.replication).toEqual(['physisch', 'synthetisch'])
    expect(options.fund_domicile).toEqual(['IE', 'LU'])
  })

  it('liefert leere Listen ohne Instrumente oder Börsentabelle', () => {
    const options = buildFieldOptions([], null)

    expect(options).toEqual({
      provider: [],
      replication: [],
      fund_domicile: [],
      fund_currency: [],
    })
  })
})
