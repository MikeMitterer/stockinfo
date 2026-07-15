import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({
  consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() },
}))

import { copyText } from '../../src/utils/clipboard'

afterEach(() => vi.unstubAllGlobals())

describe('copyText', () => {
  it('nutzt die Clipboard-API wenn verfügbar (Secure Context)', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', { clipboard: { writeText } })

    expect(await copyText('hello')).toBe(true)
    expect(writeText).toHaveBeenCalledWith('hello')
  })

  it('fällt ohne Clipboard-API auf execCommand zurück (http-Kontext)', async () => {
    vi.stubGlobal('navigator', {}) // kein clipboard — wie auf http://unraid:8000
    const execCommand = vi.fn().mockReturnValue(true)
    document.execCommand = execCommand

    expect(await copyText('fallback')).toBe(true)
    expect(execCommand).toHaveBeenCalledWith('copy')
    // Die temporäre Textarea darf nicht im DOM zurückbleiben.
    expect(document.querySelector('textarea')).toBeNull()
  })

  it('fällt auch bei einem Clipboard-API-Fehler auf execCommand zurück', async () => {
    vi.stubGlobal('navigator', {
      clipboard: { writeText: vi.fn().mockRejectedValue(new Error('denied')) },
    })
    document.execCommand = vi.fn().mockReturnValue(true)

    expect(await copyText('retry')).toBe(true)
  })

  it('liefert false wenn beide Wege scheitern', async () => {
    vi.stubGlobal('navigator', {})
    document.execCommand = vi.fn().mockReturnValue(false)

    expect(await copyText('nope')).toBe(false)
  })
})
