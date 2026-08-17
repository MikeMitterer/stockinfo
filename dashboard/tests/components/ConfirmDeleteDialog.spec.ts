/**
 * Tests der Rückfrage vor dem Löschen.
 *
 * Geprüft wird **Verhalten**, nicht Aufbau: Seit der Dialog auf `NModal` sitzt,
 * hängt sein Inhalt per Teleport am `body` statt im Wrapper — die Aussagen
 * darüber, was er zeigt und wann er `confirm`/`cancel` meldet, sind dieselben
 * geblieben.
 */
import { mount, type VueWrapper } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { nextTick } from 'vue'

import ConfirmDeleteDialog from '../../src/components/ConfirmDeleteDialog.vue'
import { i18n } from '../../src/i18n'
import type { InstrumentSummary } from '../../src/types'
import { makeInstrument } from '../fixtures/instrument'

/** Minimales Instrument für Tests — nur die für den Dialog relevanten Felder. */
function makeItem(overrides: Partial<InstrumentSummary> = {}): InstrumentSummary {
  return makeInstrument({
    isin: 'IE00B4L5Y983',
    symbol: 'EUNL.DE',
    exchange: 'DE',
    name: 'iShares Core MSCI World',
    type: 'ETF',
    volatility: null,
    history_count: 8,
    ...overrides,
  })
}

let wrapper: VueWrapper | null = null

/**
 * Hängt den Dialog ins Dokument.
 *
 * `attachTo` ist Pflicht: Naive teleportiert den Inhalt an den `body`, und was
 * dort landet, findet `wrapper.find()` nicht.
 */
async function mountDialog(item: InstrumentSummary | null): Promise<VueWrapper> {
  wrapper = mount(ConfirmDeleteDialog, {
    props: { item },
    attachTo: document.body,
    global: { plugins: [i18n] },
  })
  await nextTick()
  await nextTick()
  return wrapper
}

/** Der Inhalt des Dialogs, wie er tatsächlich im Dokument steht. */
function dialogText(): string {
  return document.body.textContent ?? ''
}

function findInDocument(selector: string): HTMLElement {
  const element = document.querySelector<HTMLElement>(selector)
  if (!element) throw new Error(`Nicht im Dokument: ${selector}`)
  return element
}

/** Ein echter Klick — Naive hört auf gebubbelte Ereignisse, nicht auf Vue-Handler. */
async function click(element: HTMLElement): Promise<void> {
  element.dispatchEvent(new MouseEvent('click', { bubbles: true }))
  await nextTick()
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
})

afterEach(() => {
  wrapper?.unmount()
  wrapper = null
  document.body.innerHTML = ''
})

describe('ConfirmDeleteDialog', () => {
  it('rendert nichts, wenn item null ist', async () => {
    await mountDialog(null)
    expect(document.querySelector('.confirm-delete')).toBeNull()
  })

  it('zeigt Name und Symbol des Instruments', async () => {
    await mountDialog(makeItem())
    expect(dialogText()).toContain('iShares Core MSCI World')
    expect(dialogText()).toContain('EUNL.DE')
  })

  it('zeigt den Singular-Satz bei history_count = 1', async () => {
    await mountDialog(makeItem({ history_count: 1 }))
    expect(dialogText()).toContain('1 Kurspunkt geht verloren.')
  })

  it('zeigt den Null-Satz bei history_count = 0', async () => {
    await mountDialog(makeItem({ history_count: 0 }))
    expect(dialogText()).toContain('Keine Kurspunkte gespeichert.')
  })

  it('zeigt den Plural-Satz bei history_count = 8', async () => {
    await mountDialog(makeItem({ history_count: 8 }))
    expect(dialogText()).toContain('8 Kurspunkte gehen verloren.')
  })

  it('emittiert confirm bei Klick auf Löschen', async () => {
    const dialog = await mountDialog(makeItem())
    await click(findInDocument('.confirm-delete__confirm'))
    expect(dialog.emitted('confirm')).toHaveLength(1)
  })

  it('emittiert cancel bei Klick auf Abbrechen', async () => {
    const dialog = await mountDialog(makeItem())
    await click(findInDocument('.confirm-delete__cancel'))
    expect(dialog.emitted('cancel')).toHaveLength(1)
  })

  it('emittiert cancel bei Escape', async () => {
    const dialog = await mountDialog(makeItem())
    // Naive prüft `code`, nicht `key` — im Browser stehen beide, hier nicht.
    document.dispatchEvent(
      new KeyboardEvent('keydown', { key: 'Escape', code: 'Escape', bubbles: true }),
    )
    await nextTick()
    expect(dialog.emitted('cancel')).toHaveLength(1)
  })

  it('emittiert cancel bei Klick auf die abdunkelnde Fläche', async () => {
    const dialog = await mountDialog(makeItem())
    await click(findInDocument('.n-modal-mask'))
    expect(dialog.emitted('cancel')).toHaveLength(1)
  })

  it('emittiert kein cancel bei Klick innerhalb des Dialogs', async () => {
    const dialog = await mountDialog(makeItem())
    await click(findInDocument('.confirm-delete'))
    expect(dialog.emitted('cancel')).toBeUndefined()
  })
})
