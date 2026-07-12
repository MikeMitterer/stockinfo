import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError, apiClient } from '../src/api/client'

afterEach(() => vi.unstubAllGlobals())

describe('apiClient', () => {
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
