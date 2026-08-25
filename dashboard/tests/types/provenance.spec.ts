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
  /**
   * Beide Formen, die der OpenAPI-Vertrag zulässt.
   *
   * `alias` steht nicht in `required`, also darf das Feld **fehlen**; sein Typ
   * ist `anyOf: [string(minLength 1), null]`, also darf es `null` sein. Ein
   * TypeScript-Typ, der nur eine der beiden Formen kennt, lehnt gültige
   * Antworten ab — genau das war der Befund aus Runde 26.
   *
   * Den verbotenen Leerstring prüft TypeScript **nicht**: Ein Stringtyp kann
   * „mindestens ein Zeichen" nicht ausdrücken. Diese Zusage liegt im Backend
   * (`ExchangeEntry.alias` mit `min_length=1`) und wird dort geprüft, samt der
   * Gegenprobe am ausgelieferten OpenAPI-Schema.
   */
  it('erlaubt den fehlenden Alias als null und als weggelassenes Feld', () => {
    const explicitlyNull: ExchangeEntry = {
      kind: 'exchange',
      mic: 'XNAS',
      alias: null,
      name: 'NASDAQ',
      region: 'usa',
      currency: 'USD',
      provenance: { kind: 'core' },
    }
    const omitted: ExchangeEntry = {
      kind: 'exchange',
      mic: 'XNYS',
      name: 'NYSE',
      region: 'usa',
      currency: 'USD',
      provenance: { kind: 'core' },
    }

    expect(explicitlyNull.alias).toBeNull()
    expect(omitted.alias).toBeUndefined()
  })

  it('verlangt die Felder, die der Vertrag als required führt', () => {
    // @ts-expect-error — `mic` steht in `required`, anders als `alias`.
    const withoutMic: ExchangeEntry = {
      kind: 'exchange',
      name: 'NASDAQ',
      region: 'usa',
      currency: 'USD',
      provenance: { kind: 'core' },
    }

    expect(withoutMic.name).toBe('NASDAQ')
  })
})
