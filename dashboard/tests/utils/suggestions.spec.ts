import { describe, expect, it } from 'vitest'

import { distinctFieldValues } from '../../src/utils/suggestions'
import { makeInstrument } from '../fixtures/instrument'

describe('distinctFieldValues', () => {
  it('dedupliziert und sortiert die Werte eines Textfelds', () => {
    const instruments = [
      makeInstrument({ symbol: 'A', provider: 'iShares' }),
      makeInstrument({ symbol: 'B', provider: 'Vanguard' }),
      makeInstrument({ symbol: 'C', provider: 'iShares' }),
    ]

    expect(distinctFieldValues(instruments, 'provider')).toEqual(['Vanguard', 'iShares'])
  })

  it('lässt nicht gesetzte Werte weg', () => {
    const instruments = [
      makeInstrument({ symbol: 'A', replication: null }),
      makeInstrument({ symbol: 'B', replication: 'physisch' }),
    ]

    expect(distinctFieldValues(instruments, 'replication')).toEqual(['physisch'])
  })

  it('gibt [] zurück, wenn keine Instrumente vorliegen', () => {
    expect(distinctFieldValues([], 'fund_domicile')).toEqual([])
  })
})
