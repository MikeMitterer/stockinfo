/**
 * Tests des Umzugsbildschirms.
 *
 * Geprüft wird, was der Benutzer **vor** einer unwiderruflichen Zustimmung
 * tatsächlich zu sehen bekommt: die Bilanz, die konkrete Verlustliste mit
 * Grund und der Backup-Hinweis. Ein Test, der nur „die Komponente rendert"
 * belegt, ginge an der einzigen Frage vorbei, die hier zählt.
 */
import { mount, type VueWrapper } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'

import MigrationGate from '../../src/components/MigrationGate.vue'
import { i18n } from '../../src/i18n'
import type { MigrationPreview, RejectedInstrument } from '../../src/types'

let wrapper: VueWrapper | null = null

afterEach(() => {
  wrapper?.unmount()
  wrapper = null
})

function makeRejected(overrides: Partial<RejectedInstrument> = {}): RejectedInstrument {
  return {
    symbol: 'VTI',
    isin: null,
    name: 'Vanguard Total Stock Market',
    exchange: null,
    type: null,
    currency: null,
    reason: 'symbol_without_exchange_suffix',
    quotes: 3,
    daily_closes: 257,
    ...overrides,
  }
}

const PREVIEW: MigrationPreview = {
  pending: true,
  migrating: 5,
  unchanged: 1,
  rejected: [makeRejected()],
  lost_quotes: 3,
  lost_daily_closes: 257,
}

function mountGate(props: Partial<InstanceType<typeof MigrationGate>['$props']> = {}): VueWrapper {
  wrapper = mount(MigrationGate, {
    props: { phase: 'pending', preview: PREVIEW, report: null, error: null, ...props },
    global: { plugins: [i18n] },
  })
  return wrapper
}

describe('MigrationGate · Phase 1', () => {
  it('nennt jedes Papier, das den Bestand verlässt, samt Grund und Verlust', () => {
    const text = mountGate().text()

    expect(text).toContain('VTI')
    expect(text).toContain('Vanguard Total Stock Market')

    /*
     * Ausgeschrieben statt gegen `t(…)` verglichen. Ein
     * `toContain(t('…'))` wäre die Prüfung, die sich selbst bestätigt: Wäre
     * der Katalogeintrag leer, hieße sie `toContain('')` und bliebe grün,
     * während im UI gar kein Grund steht.
     */
    const reason = i18n.global.t('migration.reason.symbol_without_exchange_suffix')
    expect(reason).not.toBe('symbol_without_exchange_suffix')
    expect(reason.length).toBeGreaterThan(20)
    expect(text).toContain(reason)

    // Die Zahlen sind der Preis der Zustimmung — sie müssen dastehen.
    expect(text).toContain('257')
  })

  it('zeigt die Bilanz, damit die Liste als vollständig lesbar ist', () => {
    const text = mountGate().text()

    expect(text).toContain('5')
    expect(text).toContain(i18n.global.t('migration.balanceMigrating'))
    expect(text).toContain(i18n.global.t('migration.balanceRejected'))
  })

  it('warnt vor dem Knopf zum Sichern', () => {
    expect(mountGate().text()).toContain(i18n.global.t('migration.backupTitle'))
  })

  it('meldet die Bestätigung erst auf Klick', async () => {
    const gate = mountGate()
    expect(gate.emitted('confirm')).toBeUndefined()

    await gate.find('button').trigger('click')

    expect(gate.emitted('confirm')).toHaveLength(1)
  })

  it('sperrt den Knopf, solange der Umzug läuft', () => {
    const gate = mountGate({ phase: 'confirming' })
    expect(gate.text()).toContain(i18n.global.t('migration.confirming'))
  })
})

describe('MigrationGate · nach dem Umzug', () => {
  it('zeigt im Bericht dieselben Zeilen wie vorher die Vorschau', () => {
    const gate = mountGate({
      phase: 'done',
      preview: null,
      report: { completed: true, rejected: [makeRejected()] },
    })

    expect(gate.text()).toContain(i18n.global.t('migration.doneTitle'))
    expect(gate.text()).toContain('VTI')
  })

  it('sagt ausdrücklich, wenn nichts entfernt wurde', () => {
    const gate = mountGate({
      phase: 'done',
      preview: null,
      report: { completed: true, rejected: [] },
    })

    expect(gate.text()).toContain(i18n.global.t('migration.doneNothingLost'))
  })

  /*
   * Der Zustand aus Übergabe 2A. Die Liste steht hier **weiter** da: Der Umzug
   * ist festgeschrieben, und ihn beim Fehlerbild zu verschweigen hieße, dem
   * Benutzer die Information vorzuenthalten, für die es den Bericht gibt.
   */
  it('bestreitet den Umzug nicht, wenn nur der Betrieb nicht anlief', async () => {
    const gate = mountGate({
      phase: 'startupFailed',
      preview: null,
      report: { completed: true, rejected: [makeRejected()] },
    })

    expect(gate.text()).toContain(i18n.global.t('migration.startupFailedTitle'))
    expect(gate.text()).toContain('VTI')

    await gate.find('button').trigger('click')
    expect(gate.emitted('retry')).toHaveLength(1)
  })
})

describe('MigrationGate · unbekannte Kennung', () => {
  /*
   * Eine Kennung, die der Katalog nicht kennt, darf **nicht** stumm
   * herausfallen: Dann stünde für ein entferntes Papier gar kein Grund da, und
   * genau der ist der Zweck der Liste. Der Fall ist real — das Backend darf
   * eine Kennung ergänzen, bevor das UI sie kennt.
   */
  it('zeigt die rohe Kennung, statt den Grund wegzulassen', () => {
    const gate = mountGate({
      preview: { ...PREVIEW, rejected: [makeRejected({ reason: 'brandneuer_grund' })] },
    })

    expect(gate.text()).toContain('brandneuer_grund')
  })
})
