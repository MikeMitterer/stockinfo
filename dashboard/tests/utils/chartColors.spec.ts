import { describe, expect, it } from 'vitest'

import { accentColors } from '../../src/utils/chartColors'

describe('accentColors', () => {
  it('baut Voll- und Flächenfarbe aus einem RGB-Tripel', () => {
    const { solid, fill } = accentColors('62 227 159')
    expect(solid).toBe('rgb(62 227 159)')
    expect(fill).toBe('rgb(62 227 159 / 0.13)')
  })

  it('erlaubt eine abweichende Deckkraft', () => {
    expect(accentColors('62 227 159', 0.5).fill).toBe('rgb(62 227 159 / 0.5)')
  })

  it('werden von der CSS-Engine als gültige Farben akzeptiert (Regressionstest T-11b)', () => {
    // Genau das ist der Fehler, der durchgerutscht ist: die alte Hex-Alpha-
    // Verkettung erzeugte auf RGB-Tripeln einen String, den keine CSS-Engine
    // parst. jsdom normalisiert gültige Werte beim Setzen — ein leerer
    // Rückwert heißt „abgelehnt".
    const { solid, fill } = accentColors('62 227 159')
    const el = document.createElement('div')

    el.style.backgroundColor = solid
    expect(el.style.backgroundColor).not.toBe('')

    el.style.backgroundColor = fill
    expect(el.style.backgroundColor).not.toBe('')
  })

  it('lehnt die alte kaputte Hex-Alpha-Verkettung auf einem RGB-Tripel ab', () => {
    // Locksicherung für den ursprünglichen Bug: `${accent}22` auf einem
    // rgb(...)-Token ist kein gültiger CSS-Farbwert und wird von der
    // CSS-Engine (und von canvas.fillStyle) stillschweigend verworfen.
    const el = document.createElement('div')
    el.style.backgroundColor = 'rgb(62 227 159)22'
    expect(el.style.backgroundColor).toBe('')
  })
})
