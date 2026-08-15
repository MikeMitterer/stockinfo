import { describe, expect, it } from 'vitest'

import { pctAxisBounds, periodChangePct, relChangePct } from '../../src/utils/changePct'

describe('relChangePct', () => {
  it('berechnet die prozentuale Veränderung von from auf to', () => {
    expect(relChangePct(100, 110)).toBeCloseTo(10)
    expect(relChangePct(100, 90)).toBeCloseTo(-10)
    expect(relChangePct(100, 100)).toBeCloseTo(0)
  })

  it('gibt null bei from=0 oder ungültigen Werten', () => {
    expect(relChangePct(0, 10)).toBeNull()
    expect(relChangePct(Number.NaN, 10)).toBeNull()
    expect(relChangePct(100, Number.NaN)).toBeNull()
  })
})

describe('periodChangePct', () => {
  it('nimmt ersten und letzten Punkt der Serie', () => {
    expect(periodChangePct([{ y: 200 }, { y: 210 }, { y: 250 }])).toBeCloseTo(25)
  })

  it('gibt null bei weniger als zwei Punkten', () => {
    expect(periodChangePct([])).toBeNull()
    expect(periodChangePct([{ y: 100 }])).toBeNull()
  })
})

describe('pctAxisBounds', () => {
  it('koppelt %-Grenzen an die (gepolsterten) Kursgrenzen relativ zum ersten Punkt', () => {
    // first=100, lo=100, hi=110 → pad=(10)*0.5=5 → yMin=95, yMax=115
    const b = pctAxisBounds([{ y: 100 }, { y: 110 }], 0.5)
    expect(b).not.toBeNull()
    expect(b!.yMin).toBeCloseTo(95)
    expect(b!.yMax).toBeCloseTo(115)
    expect(b!.pctMin).toBeCloseTo(-5) // (95-100)/100*100
    expect(b!.pctMax).toBeCloseTo(15) // (115-100)/100*100
  })

  it('gibt null bei <2 Punkten oder erstem Wert 0', () => {
    expect(pctAxisBounds([{ y: 100 }])).toBeNull()
    expect(pctAxisBounds([{ y: 0 }, { y: 10 }])).toBeNull()
  })
})
