/**
 * Was `tests/setup.ts` für alle Specs einrichtet.
 *
 * Der consola-Mock stand früher in sechzehn Specs je für sich. Steht er nur
 * noch hier, muss ein Test sagen, dass er wirkt — sonst schriebe jede Spec
 * still wieder in die Ausgabe.
 */
import { consola } from 'consola'
import { describe, expect, it, vi } from 'vitest'

describe('tests/setup.ts', () => {
  it('ersetzt consola in jeder Spec durch Attrappen', () => {
    expect(vi.isMockFunction(consola.error)).toBe(true)
    expect(vi.isMockFunction(consola.warn)).toBe(true)
    expect(vi.isMockFunction(consola.info)).toBe(true)
  })
})
