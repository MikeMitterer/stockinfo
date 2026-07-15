import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import { instrumentPath } from '../api/paths'
import type { InstrumentRef, QuotePoint } from '../types'
import { translate } from '../i18n'

/** Lädt die Kurshistorie eines Instruments — per ISIN oder (falls keine) per Symbol. */
export function useHistory(): {
  points: Ref<QuotePoint[]>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: (item: InstrumentRef) => Promise<void>
  clear: () => void
} {
  const points = ref<QuotePoint[]>([])
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  // Zähler gegen Races: nur die jüngste Anfrage darf die Refs beschreiben.
  let requestId = 0

  async function load(item: InstrumentRef): Promise<void> {
    const currentRequest = ++requestId
    loading.value = true
    error.value = null
    try {
      const path = instrumentPath('/quote', item, '/history?limit=500')
      const result = await apiClient.get<QuotePoint[]>(path)
      if (currentRequest !== requestId) return // veraltete Antwort verwerfen
      points.value = result
    } catch (err) {
      if (currentRequest !== requestId) return
      error.value = translate('errors.history')
      consola.error('useHistory.load', err)
    } finally {
      if (currentRequest === requestId) loading.value = false
    }
  }

  /** Setzt Historie und Fehlerzustand zurück (z.B. nach Abwahl des Instruments). */
  function clear(): void {
    requestId++ // laufende Antworten verwerfen
    points.value = []
    error.value = null
    loading.value = false
  }

  return { points, loading, error, load, clear }
}
