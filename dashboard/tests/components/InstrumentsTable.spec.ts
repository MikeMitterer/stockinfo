import { mount } from '@vue/test-utils'
import { NSelect } from 'naive-ui'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import InstrumentsTable from '../../src/components/InstrumentsTable.vue'
import { useTableSort } from '../../src/composables/useTableSort'
import { i18n } from '../../src/i18n'
import { makeInstrument } from '../fixtures/instrument'

const base = makeInstrument()
const instruments = [base, makeInstrument({ symbol: 'VGWL.DE', name: 'Vanguard FTSE All-World' })]

/** Setzt die Viewport-Breite für useIsCompact. */
function stubMatchMedia(compact: boolean) {
  vi.stubGlobal('matchMedia', vi.fn().mockReturnValue({
    matches: compact, media: '',
    addEventListener: () => {}, removeEventListener: () => {},
  }))
}

function mountTable() {
  return mount(InstrumentsTable, {
    props: {
      instruments, selectedSymbol: null, refreshingSymbol: null, savingSymbol: null,
      extraetfEtfUrl: '', extraetfStockUrl: '', yahooUrl: '',
    },
    global: { plugins: [i18n] },
  })
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
  // sortKey/direction sind Modul-Level-Singletons — zwischen Tests zurücksetzen,
  // sonst hängt eine Sortierung aus einem früheren Test nach.
  useTableSort().setSortKey(null)
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('InstrumentsTable — Darstellung nach Breite', () => {
  it('zeigt ab md die Tabelle und keine Karten', () => {
    stubMatchMedia(false)
    const wrapper = mountTable()
    expect(wrapper.find('table').exists()).toBe(true)
    expect(wrapper.findAll('.icard')).toHaveLength(0)
  })

  it('zeigt unter md Karten und keine Tabelle', () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    expect(wrapper.find('table').exists()).toBe(false)
    expect(wrapper.findAll('.icard')).toHaveLength(2)
  })

  it('bietet unter md eine Sortier-Auswahl', () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    expect(wrapper.find('.tsort__select').exists()).toBe(true)
    // Richtungsknopf erst sichtbar, sobald tatsächlich sortiert wird (s.u.)
    expect(wrapper.find('.tsort__dir').exists()).toBe(false)
  })

  it('trägt einen zugänglichen Namen — ein Feld ohne Namen ist keins', () => {
    stubMatchMedia(true)
    const wrapper = mountTable()

    expect(wrapper.findComponent(NSelect).attributes('aria-label')).toBe('Sortieren nach')
  })

  it('bietet den Leerlauf als erste Wahl — sonst ließe sich Sortieren nicht abschalten', () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    const optionen = wrapper.findComponent(NSelect).props('options')!

    expect(optionen[0]).toEqual({ value: '', label: 'Ohne Sortierung' })
  })

  it('steht ohne aktive Sortierung auf dem Leerlauf', () => {
    stubMatchMedia(true)
    const wrapper = mountTable()

    expect(wrapper.findComponent(NSelect).props('value')).toBe('')
  })

  it('übernimmt die gewählte Spalte', async () => {
    stubMatchMedia(true)
    const wrapper = mountTable()

    wrapper.findComponent(NSelect).vm.$emit('update:value', 'name')
    await wrapper.vm.$nextTick()

    expect(wrapper.findComponent(NSelect).props('value')).toBe('name')
    expect(wrapper.find('.tsort__dir').exists()).toBe(true)
  })

  it('Richtungsknopf ist ohne aktive Sortierung nicht vorhanden', () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    expect(wrapper.find('.tsort__dir').exists()).toBe(false)
  })

  it('Wahl des Leerlaufs setzt eine aktive Sortierung zurück', async () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    const auswahl = wrapper.findComponent(NSelect)

    auswahl.vm.$emit('update:value', 'name')
    await wrapper.vm.$nextTick()
    expect(window.localStorage.getItem('stockinfo-sort')).not.toBeNull()

    auswahl.vm.$emit('update:value', '')
    await wrapper.vm.$nextTick()

    expect(wrapper.findComponent(NSelect).props('value')).toBe('')
    expect(wrapper.find('.tsort__dir').exists()).toBe(false)
  })

  it('reicht select aus einer Karte nach oben durch', async () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    await wrapper.find('.icard__head').trigger('click')
    expect(wrapper.emitted('select')).toHaveLength(1)
  })

  it('zeigt den Leerzustand unabhängig von der Breite', () => {
    stubMatchMedia(true)
    const wrapper = mount(InstrumentsTable, {
      props: {
        instruments: [], selectedSymbol: null, refreshingSymbol: null, savingSymbol: null,
        extraetfEtfUrl: '', extraetfStockUrl: '', yahooUrl: '',
      },
      global: { plugins: [i18n] },
    })
    expect(wrapper.find('.empty').exists()).toBe(true)
  })
})

/*
 * Konflikt gelöst wie im Plan festgehalten: Die Zeile öffnet weiterhin das
 * Chart (`@click`), nur Symbol und Name klinken sich mit `@click.stop` aus und
 * öffnen stattdessen die Schublade.
 */
describe('InstrumentsTable — Schublade', () => {
  it('öffnet die Schublade beim Klick auf das Symbol, ohne das Chart zu öffnen', async () => {
    stubMatchMedia(false)
    const wrapper = mountTable()

    await wrapper.get('.row-toggle').trigger('click')

    expect(wrapper.emitted('select')).toBeUndefined()
    expect(wrapper.findComponent({ name: 'InstrumentDrilldown' }).exists()).toBe(true)
  })

  it('öffnet die Schublade auch beim Klick auf den Namen', async () => {
    stubMatchMedia(false)
    const wrapper = mountTable()

    await wrapper.get('.name .row-toggle').trigger('click')

    expect(wrapper.emitted('select')).toBeUndefined()
    expect(wrapper.findComponent({ name: 'InstrumentDrilldown' }).exists()).toBe(true)
  })

  /*
   * Sichtprüfung: Symbol und Name öffnen die Zeile zwar, aber ohne sichtbares
   * Merkmal sieht man ihnen das nicht an — „Klick auf das Symbol ist zu wenig
   * intuitiv". Der Pfeil steht deshalb vorne in der Zeile, wie ihn die
   * Kartenliste unter `md` längst zeigt (`InstrumentCard.vue`).
   */
  it('zeigt vorne in der Zeile einen Pfeil, der den Zustand der Schublade spiegelt', async () => {
    stubMatchMedia(false)
    const wrapper = mountTable()

    expect(wrapper.get('.row-toggle__caret').classes()).not.toContain('row-toggle__caret--open')

    await wrapper.get('.row-toggle').trigger('click')

    expect(wrapper.get('.row-toggle__caret').classes()).toContain('row-toggle__caret--open')
  })

  it('markiert den geöffneten Zustand am Knopf', async () => {
    stubMatchMedia(false)
    const wrapper = mountTable()
    const toggle = wrapper.get('.row-toggle')

    expect(toggle.attributes('aria-expanded')).toBe('false')
    await toggle.trigger('click')
    expect(toggle.attributes('aria-expanded')).toBe('true')
  })

  it('schließt die Schublade beim erneuten Klick', async () => {
    stubMatchMedia(false)
    const wrapper = mountTable()
    const toggle = wrapper.get('.row-toggle')

    await toggle.trigger('click')
    await toggle.trigger('click')

    expect(wrapper.findComponent({ name: 'InstrumentDrilldown' }).exists()).toBe(false)
  })

  /*
   * Die Teststrategie der Spec verlangt Escape als Ausweg. Bisher gab es
   * keinen Tastatur-Handler: Wer die Schublade per Tastatur geöffnet hatte,
   * kam nur wieder heraus, indem er zum selben Knopf zurücktabbte.
   */
  it('schließt die Schublade mit Escape', async () => {
    stubMatchMedia(false)
    const wrapper = mountTable()

    await wrapper.get('.row-toggle').trigger('click')
    expect(wrapper.findComponent({ name: 'InstrumentDrilldown' }).exists()).toBe(true)

    await wrapper.get('.table').trigger('keydown.esc')

    expect(wrapper.findComponent({ name: 'InstrumentDrilldown' }).exists()).toBe(false)
  })

  /*
   * Escape aus einem Bedienelement heraus, das die Taste selbst schon
   * verarbeitet hat (`UxInlineNumber` verwirft damit seinen Entwurf), darf die
   * Schublade **nicht** zusätzlich zuklappen — sonst verliert man mit einem
   * Tastendruck zwei Dinge auf einmal. Erkannt an `defaultPrevented`.
   */
  it('lässt die Schublade offen, wenn ein Bedienelement Escape schon verarbeitet hat', async () => {
    stubMatchMedia(false)
    const wrapper = mountTable()

    await wrapper.get('.row-toggle').trigger('click')

    // Nachgestellt wie in echt: Das Bedienelement in der Schublade ist das Ziel
    // und ruft `preventDefault()`, bevor das Ereignis zur Tabelle hochsteigt.
    const drawer = wrapper.get('.drawer-row').element
    drawer.addEventListener('keydown', (event) => event.preventDefault())
    drawer.dispatchEvent(
      new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }),
    )
    await nextTick()

    expect(wrapper.findComponent({ name: 'InstrumentDrilldown' }).exists()).toBe(true)
  })

  it('öffnet weiterhin das Chart bei einem Klick außerhalb von Symbol und Name', async () => {
    stubMatchMedia(false)
    const wrapper = mountTable()

    await wrapper.get('tbody tr').trigger('click')

    expect(wrapper.emitted('select')).toHaveLength(1)
    expect(wrapper.findComponent({ name: 'InstrumentDrilldown' }).exists()).toBe(false)
  })

  it('spannt die Schublade über alle Spalten der Kopfzeile', async () => {
    stubMatchMedia(false)
    const wrapper = mountTable()

    await wrapper.get('.row-toggle').trigger('click')

    const headCount = wrapper.findAll('thead th').length
    expect(wrapper.get('.drawer-row td').attributes('colspan')).toBe(String(headCount))
  })

  it('reicht ein override aus der Schublade mit dem betroffenen Instrument nach oben durch', async () => {
    stubMatchMedia(false)
    const wrapper = mountTable()
    await wrapper.get('.row-toggle').trigger('click')

    const drilldown = wrapper.findComponent({ name: 'InstrumentDrilldown' })
    drilldown.vm.$emit('commit', { provider: 'Vanguard' })

    expect(wrapper.emitted('override')?.[0]?.[0]).toEqual({
      item: base,
      patch: { provider: 'Vanguard' },
    })
  })

  it('reicht fieldOptions unverändert an die Schublade durch', async () => {
    stubMatchMedia(false)
    const wrapper = mount(InstrumentsTable, {
      props: {
        instruments, selectedSymbol: null, refreshingSymbol: null, savingSymbol: null,
        extraetfEtfUrl: '', extraetfStockUrl: '', yahooUrl: '',
        fieldOptions: { provider: ['Vanguard', 'iShares'] },
      },
      global: { plugins: [i18n] },
    })
    await wrapper.get('.row-toggle').trigger('click')

    expect(wrapper.findComponent({ name: 'InstrumentDrilldown' }).props('fieldOptions')).toEqual({
      provider: ['Vanguard', 'iShares'],
    })
  })

  /*
   * Fix-Runde 1: `fieldOptions` kam an die Tabellen-Schublade an, aber nicht
   * an die Karten — der `InstrumentCard`-Aufruf im kompakten Zweig hatte
   * keine `field-options`-Bindung. Der Test oben hätte das nie auffangen
   * können, weil er ausschließlich Desktop (`stubMatchMedia(false)`) prüft.
   * Dieser Test führt denselben Nachweis **durch `InstrumentsTable` im
   * kompakten Zustand** — der einzige Weg, den fehlenden Draht zu sehen.
   */
  it('reicht fieldOptions auch über die Kartenliste bis zur Schublade durch (mobil)', async () => {
    stubMatchMedia(true)
    const wrapper = mount(InstrumentsTable, {
      props: {
        instruments, selectedSymbol: null, refreshingSymbol: null, savingSymbol: null,
        extraetfEtfUrl: '', extraetfStockUrl: '', yahooUrl: '',
        fieldOptions: { provider: ['Vanguard', 'iShares'] },
      },
      global: { plugins: [i18n] },
    })

    await wrapper.get('.icard__toggle').trigger('click')

    expect(wrapper.findComponent({ name: 'InstrumentDrilldown' }).props('fieldOptions')).toEqual({
      provider: ['Vanguard', 'iShares'],
    })
  })

  it('verknüpft den Symbol-Knopf per aria-controls mit der tatsächlichen Schubladen-Zeile', async () => {
    stubMatchMedia(false)
    const wrapper = mountTable()
    const toggle = wrapper.get('.row-toggle')

    await toggle.trigger('click')

    // Attribut-Selektor statt `#id`: Das Symbol enthält einen Punkt
    // („APC.DE"), den ein `#id`-Selektor als Klassentrenner läse.
    const controlsId = toggle.attributes('aria-controls')
    expect(controlsId).toBeTruthy()
    expect(wrapper.find(`[id="${controlsId}"]`).classes()).toContain('drawer-row')
  })
})
