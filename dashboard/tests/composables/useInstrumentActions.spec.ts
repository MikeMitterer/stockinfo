import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({
  consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() },
}))

import { i18n } from '../../src/i18n'

import { useInstrumentActions } from '../../src/composables/useInstrumentActions'

afterEach(() => vi.unstubAllGlobals())

describe('useInstrumentActions', () => {
  it.each(['de', 'en'] as const)('nennt bei Fehlern die getrimmte Eingabe auf %s', async (locale) => {
    const previousLocale = i18n.global.locale.value
    i18n.global.locale.value = locale
    try {
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('Testgrund', { status: 400 })))
      const { add, error } = useInstrumentActions()
      await add('  KEINPAPIER.XX  ')
      expect(error.value).toContain('KEINPAPIER.XX')
      expect(error.value).not.toContain('  KEINPAPIER.XX  ')
      expect(error.value).toBe(i18n.global.t('errors.addIdentifier', { identifier: 'KEINPAPIER.XX' }))
    } finally {
      i18n.global.locale.value = previousLocale
    }
  })

  describe.each(['de', 'en'] as const)('Fehlerpfad auf %s', (locale) => {
    it.each(['raw', 'broken', 'empty', 'primitive', 'array', 'legacy', 'read', 'network', 'known', 'unknown'])('%s', async (scenario) => {
      const previousLocale = i18n.global.locale.value
      i18n.global.locale.value = locale
      try {
        const identifier = 'DEMO.XBUD'
        const bodies: Record<string, string> = {
          raw: 'Internal Server Error', broken: '{"detail":', empty: '',
          primitive: '"Internal Server Error"', array: '[{"detail":"internal"}]',
          legacy: '{"detail":"Internal Server Error"}',
          known: JSON.stringify({ code: 'instrument_not_found', params: { identifier }, detail: 'untranslated' }),
          unknown: JSON.stringify({ code: 'new_plugin_error', detail: 'untranslated' }),
        }
        const response = new Response(bodies[scenario] ?? '', { status: 502, statusText: 'Bad Gateway' })
        if (scenario === 'read') vi.spyOn(response, 'text').mockRejectedValue(new Error('stream aborted'))
        vi.stubGlobal('fetch', scenario === 'network'
          ? vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
          : vi.fn().mockResolvedValue(response))
        const { add, error, busy } = useInstrumentActions()
        await add(identifier)
        let expected = i18n.global.t('errors.addIdentifier', { identifier })
        if (scenario === 'known') expected += ` — ${i18n.global.t('errors.reason.instrument_not_found', { identifier })}`
        if (scenario === 'unknown') expected += ` — ${i18n.global.t('errors.reason.unknown', { code: 'new_plugin_error' })}`
        expect(error.value).toBe(expected)
        expect(busy.value).toBe(false)
      } finally {
        i18n.global.locale.value = previousLocale
      }
    })
  })

  it('add ruft /quote/{isin} bei ISIN', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{}', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    await useInstrumentActions().add('IE00B3RBWM25')
    expect(fetchMock.mock.calls[0][0]).toContain('/quote/IE00B3RBWM25')
  })

  it('add ruft /quote?symbol bei Symbol', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{}', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    await useInstrumentActions().add('VGWL.DE')
    expect(fetchMock.mock.calls[0][0]).toContain('/quote?symbol=VGWL.DE')
  })

  it('setIsin ruft PUT und toleriert 204', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)
    const { error, setIsin } = useInstrumentActions()
    await setIsin('VGWL.DE', 'IE00B3RBWM25')
    expect(fetchMock.mock.calls[0][0]).toContain('/instruments/by-symbol/VGWL.DE/isin')
    expect((fetchMock.mock.calls[0][1] as RequestInit).method).toBe('PUT')
    expect(error.value).toBeNull()
  })

  it('setIsin setzt error bei Fehler', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('boom', { status: 500 })))
    const { error, setIsin } = useInstrumentActions()
    await setIsin('VGWL.DE', 'IE00B3RBWM25')
    expect(error.value).not.toBeNull()
  })

  it('remove nutzt den by-symbol-Pfad ohne ISIN', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)
    await useInstrumentActions().remove({ isin: null, symbol: 'GOLD.SG' })
    expect(fetchMock.mock.calls[0][0]).toContain('/instruments/by-symbol/GOLD.SG')
  })
})
