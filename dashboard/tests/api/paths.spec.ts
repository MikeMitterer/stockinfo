import { describe, expect, it } from 'vitest'

import { analyzePath, fxPath, instrumentPath, isIsin, quotePath } from '../../src/api/paths'

describe('isIsin', () => {
  it('erkennt ISINs', () => {
    expect(isIsin('IE00B3RBWM25')).toBe(true)
    expect(isIsin('VGWL.DE')).toBe(false)
    expect(isIsin('')).toBe(false)
  })
})

describe('instrumentPath', () => {
  it('baut den ISIN-Pfad', () => {
    expect(instrumentPath('/quote', { isin: 'IE00B3RBWM25', symbol: 'VGWL.DE' }, '/daily'))
      .toBe('/quote/IE00B3RBWM25/daily')
  })

  it('baut den by-symbol-Pfad ohne ISIN', () => {
    expect(instrumentPath('/refresh', { isin: null, symbol: 'VGWL.DE' }))
      .toBe('/refresh/by-symbol/VGWL.DE')
  })

  it('enkodiert ISIN und Symbol', () => {
    expect(instrumentPath('/quote', { isin: '../env', symbol: 'x' }))
      .toBe('/quote/..%2Fenv')
    expect(instrumentPath('/quote', { isin: null, symbol: 'A?b=c' }))
      .toBe('/quote/by-symbol/A%3Fb%3Dc')
  })
})

describe('quotePath', () => {
  it('nutzt die ISIN als Pfadsegment', () => {
    expect(quotePath({ isin: 'IE00B3RBWM25', symbol: 'VGWL.DE' })).toBe('/quote/IE00B3RBWM25')
  })

  it('nutzt das Symbol als Query-Parameter (enkodiert)', () => {
    expect(quotePath({ isin: null, symbol: 'GOLD.SG&x=1' })).toBe('/quote?symbol=GOLD.SG%26x%3D1')
  })
})

describe('analyzePath', () => {
  it('nutzt die ISIN als Query', () => {
    expect(analyzePath({ isin: 'IE00B4L5Y983', symbol: 'EUNL.DE' })).toBe(
      '/analyze?isin=IE00B4L5Y983',
    )
  })
  it('fällt ohne ISIN auf das Symbol zurück', () => {
    expect(analyzePath({ isin: null, symbol: 'AAPL' })).toBe('/analyze?symbol=AAPL')
  })
})

describe('fxPath', () => {
  it('baut den /fx-Pfad mit encodeURIComponent', () => {
    expect(fxPath('EUR', 'USD')).toBe('/fx?base=EUR&quote=USD')
  })
})
