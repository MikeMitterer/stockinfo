/**
 * Der Herkunfts-Typ als Vertrag — geprüft vom Typprüfer, nicht zur Laufzeit.
 *
 * `vue-tsc` prüft `tests` mit (siehe `tsconfig.json`), deshalb sind die
 * `@ts-expect-error`-Zeilen echte Zusicherungen: Verschwindet die Trennung
 * zwischen Core und Plugin, wird der erwartete Fehler nicht mehr gemeldet und
 * der Build schlägt fehl.
 *
 * Vorher war `Provenance` ein Interface mit `id: string | null`. Es konnte
 * beide ungültigen Kombinationen ausdrücken — `plugin` ohne ID und `core` mit
 * einer —, also genau die, die T-30 beim Merge auseinanderhalten muss.
 */

import { describe, expect, it } from 'vitest'

import type { ExchangeEntry, Provenance } from '../../src/types'

describe('Provenance', () => {
  it('trennt Core ohne ID von Plugin mit ID', () => {
    const core: Provenance = { kind: 'core' }
    const plugin: Provenance = { kind: 'plugin', id: 'at-boersen' }

    // `kind` trägt das Narrowing: Nur im Plugin-Zweig gibt es überhaupt ein `id`.
    expect(plugin.kind === 'plugin' && plugin.id).toBe('at-boersen')
    expect(core.kind).toBe('core')
  })

  it('kennt weder ein Plugin ohne ID noch einen Core mit ID', () => {
    // @ts-expect-error — „irgendein Plugin" ist keine verwertbare Herkunft.
    const withoutId: Provenance = { kind: 'plugin' }
    // @ts-expect-error — der Core stammt aus keinem Plugin.
    const coreWithId: Provenance = { kind: 'core', id: 'demo' }

    expect([withoutId, coreWithId]).toHaveLength(2)
  })
})

describe('ExchangeEntry', () => {
  it('drückt den fehlenden Alias als null aus, nicht als Leerstring', () => {
    const nasdaq: ExchangeEntry = {
      kind: 'exchange',
      mic: 'XNAS',
      alias: null,
      name: 'NASDAQ',
      region: 'usa',
      currency: 'USD',
      provenance: { kind: 'core' },
    }

    expect(nasdaq.alias).toBeNull()
  })
})
