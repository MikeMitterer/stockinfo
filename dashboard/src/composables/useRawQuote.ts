import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import { quotePath } from '../api/paths'
import { API_BASE_URL } from '../config'
import type { InstrumentRef } from '../types'
import { useRequest } from './useRequest'

/** Lädt die rohe /quote-Antwort eines Instruments als formatiertes JSON (für die Anzeige). */
export function useRawQuote(): {
  url: Ref<string>
  json: Ref<string>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: (item: InstrumentRef) => Promise<void>
} {
  const url = ref<string>('')
  const { data, loading, error, run, reset } = useRequest<string, [string]>({
    initial: '',
    request: async (path) => JSON.stringify(await apiClient.get<unknown>(path), null, 2),
    failure: 'errors.rawQuote',
    logTag: 'useRawQuote.load',
    latestOnly: true,
  })

  async function load(item: InstrumentRef): Promise<void> {
    const path = quotePath(item)
    // Absolute URL zum Kopieren/Teilen — bei leerem API_BASE_URL (same-origin)
    // gegen den Seiten-Origin auflösen statt nur den Pfad anzuzeigen.
    url.value = new URL(`${API_BASE_URL}${path}`, window.location.origin).toString()
    reset()
    await run(path)
  }

  return { url, json: data, loading, error, load }
}
