import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import type { QuotePoint } from '../types'

/** Lädt die Kurshistorie eines Instruments per ISIN. */
export function useHistory(): {
  points: Ref<QuotePoint[]>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: (isin: string) => Promise<void>
} {
  const points = ref<QuotePoint[]>([])
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function load(isin: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      points.value = await apiClient.get<QuotePoint[]>(
        `/quote/${isin}/history?limit=500`,
      )
    } catch (err) {
      error.value = 'Historie konnte nicht geladen werden'
      consola.error('useHistory.load', err)
    } finally {
      loading.value = false
    }
  }

  return { points, loading, error, load }
}
