import { describe, expect, it } from 'vitest'

import { isEuropeanIsin } from '../../src/utils/isin'

/*
 * Spiegel von `is_european_isin` im Backend (`app/providers/justetf_provider.py`,
 * getestet in `tests/test_providers.py::test_is_european_isin`) — dieselben
 * Fälle, damit Frontend und Backend nicht auseinanderlaufen.
 */
describe('isEuropeanIsin', () => {
  it('erkennt ein irisches Fondsdomizil', () => {
    expect(isEuropeanIsin('IE00B4L5Y983')).toBe(true)
  })

  it('erkennt ein luxemburgisches Fondsdomizil', () => {
    expect(isEuropeanIsin('LU0274208692')).toBe(true)
  })

  it('ist unabhängig von Groß-/Kleinschreibung', () => {
    expect(isEuropeanIsin('ie00b4l5y983')).toBe(true)
  })

  it('lehnt eine US-ISIN ab', () => {
    expect(isEuropeanIsin('US78462F1030')).toBe(false)
  })

  it('lehnt eine kanadische ISIN ab', () => {
    expect(isEuropeanIsin('CA0679011084')).toBe(false)
  })

  it('lehnt eine leere ISIN ab', () => {
    expect(isEuropeanIsin('')).toBe(false)
  })

  it('lehnt eine fehlende ISIN ab', () => {
    expect(isEuropeanIsin(null)).toBe(false)
  })
})
