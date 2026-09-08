import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError, apiClient } from '../../src/api/client'

afterEach(() => {
  vi.unstubAllGlobals()
  window.localStorage.clear()
})

describe('apiClient', () => {
  it('behält den HTTP-Status bei Lesefehlern ohne statusText als Ersatzkörper', async () => {
    const response = new Response('', { status: 502, statusText: 'Bad Gateway' })
    vi.spyOn(response, 'text').mockRejectedValue(new Error('stream aborted'))
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response))
    await expect(apiClient.get('/quote?symbol=DEMO.XBUD')).rejects.toMatchObject({
      status: 502, detail: '',
    })
  })

  it('get parst JSON', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(JSON.stringify([{ symbol: 'VGWL.DE' }]), { status: 200 }),
    ))
    const data = await apiClient.get<Array<{ symbol: string }>>('/instruments')
    expect(data[0].symbol).toBe('VGWL.DE')
  })

  it('wirft ApiError bei non-2xx', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response('nope', { status: 404 }),
    ))
    await expect(apiClient.get('/quote/XX')).rejects.toBeInstanceOf(ApiError)
  })

  it('del toleriert 204', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 204 })))
    await expect(apiClient.del('/instruments/IE00B3RBWM25')).resolves.toBeUndefined()
  })
})
