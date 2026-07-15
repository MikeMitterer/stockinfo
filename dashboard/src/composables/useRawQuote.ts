import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import { quotePath } from '../api/paths'
import { API_BASE_URL } from '../config'
import type { InstrumentRef } from '../types'

/** Lädt die rohe /quote-Antwort eines Instruments als formatiertes JSON (für die Anzeige). */
export function useRawQuote(): {
  url: Ref<string>
  json: Ref<string>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: (item: InstrumentRef) => Promise<void>
} {
  const url = ref<string>('')
  const json = ref<string>('')
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  // Zähler gegen Races: nur die jüngste Anfrage darf die Refs beschreiben.
  let requestId = 0

  async function load(item: InstrumentRef): Promise<void> {
    const currentRequest = ++requestId
    const path = quotePath(item)
    url.value = `${API_BASE_URL}${path}`
    json.value = ''
    loading.value = true
    error.value = null
    try {
      const data = await apiClient.get<unknown>(path)
      if (currentRequest !== requestId) return // veraltete Antwort verwerfen
      json.value = JSON.stringify(data, null, 2)
    } catch (err) {
      if (currentRequest !== requestId) return
      error.value = 'Abfrage fehlgeschlagen'
      consola.error('useRawQuote.load', err)
    } finally {
      if (currentRequest === requestId) loading.value = false
    }
  }

  return { url, json, loading, error, load }
}
