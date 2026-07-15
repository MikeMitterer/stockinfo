import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { initScrollbarAutoHide } from '../../src/utils/scrollbarActivity'

beforeEach(() => vi.useFakeTimers())
afterEach(() => {
  vi.useRealTimers()
  document.documentElement.classList.remove('scrolling')
})

describe('initScrollbarAutoHide', () => {
  it('setzt html.scrolling beim Scrollen und entfernt sie nach der Ruhezeit', () => {
    initScrollbarAutoHide(500)

    window.dispatchEvent(new Event('scroll'))
    expect(document.documentElement.classList.contains('scrolling')).toBe(true)

    vi.advanceTimersByTime(500)
    expect(document.documentElement.classList.contains('scrolling')).toBe(false)
  })

  it('verlängert die Sichtbarkeit bei fortgesetztem Scrollen', () => {
    initScrollbarAutoHide(500)

    window.dispatchEvent(new Event('scroll'))
    vi.advanceTimersByTime(400)
    window.dispatchEvent(new Event('scroll')) // Timer neu starten
    vi.advanceTimersByTime(400)
    expect(document.documentElement.classList.contains('scrolling')).toBe(true)

    vi.advanceTimersByTime(100)
    expect(document.documentElement.classList.contains('scrolling')).toBe(false)
  })

  it('erkennt auch Scrollen in inneren Containern (Capture-Phase)', () => {
    initScrollbarAutoHide(500)

    document.body.dispatchEvent(new Event('scroll'))
    expect(document.documentElement.classList.contains('scrolling')).toBe(true)
  })
})
