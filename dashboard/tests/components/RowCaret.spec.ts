import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import RowCaret from '../../src/components/RowCaret.vue'

describe('RowCaret', () => {
  it('zeigt den geschlossenen Zustand ohne Modifier', () => {
    const wrapper = mount(RowCaret, { props: { open: false } })

    expect(wrapper.classes()).toContain('caret')
    expect(wrapper.classes()).not.toContain('caret--open')
  })

  it('markiert den geöffneten Zustand', () => {
    const wrapper = mount(RowCaret, { props: { open: true } })

    expect(wrapper.classes()).toContain('caret--open')
  })

  /*
   * Der Grund, warum das hier ein SVG ist und kein `⌄`: Das Zeichen sitzt tief
   * in seinem Em-Quadrat, und beim Drehen um 180° kippt es nach oben — eine
   * feste optische Korrektur kann nie beide Zustände treffen. Die Form im SVG
   * liegt symmetrisch um die Kastenmitte, damit die Drehung sie nicht
   * verschiebt: x von 6 bis 18, y von 9 bis 15, Mitte also 12/12.
   */
  it('trägt eine um die Kastenmitte symmetrische Form, damit die Drehung nichts verschiebt', () => {
    const wrapper = mount(RowCaret, { props: { open: false } })

    expect(wrapper.attributes('viewBox')).toBe('0 0 24 24')
    expect(wrapper.get('path').attributes('d')).toBe('M6 9 L12 15 L18 9')
  })

  // Der Zustand steht am Knopf (`aria-expanded`); ein vorgelesener Pfeil wäre
  // dieselbe Auskunft ein zweites Mal, nur stummer.
  it('bleibt für Hilfstechnik unsichtbar', () => {
    const wrapper = mount(RowCaret, { props: { open: false } })

    expect(wrapper.attributes('aria-hidden')).toBe('true')
  })
})
