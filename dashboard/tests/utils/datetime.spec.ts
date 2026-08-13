import { describe, expect, it } from 'vitest'

import { formatDateTime } from '../../src/utils/datetime'

describe('formatDateTime', () => {
  it('formatiert einen ISO-String lokalisiert (kein roher ISO-String)', () => {
    const out = formatDateTime('2026-08-13T07:41:13.759837+00:00', 'de')
    expect(out).not.toContain('T')       // kein 'YYYY-MM-DDTHH:...'
    expect(out).toMatch(/2026/)          // Jahr enthalten
  })

  it('gibt bei ungültigem Input den Rohwert zurück', () => {
    expect(formatDateTime('nope', 'de')).toBe('nope')
  })
})
