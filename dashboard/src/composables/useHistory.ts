import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import type { QuotePoint } from '../types'

/** Ein Instrument, identifiziert per ISIN (falls vorhanden) oder Symbol. */
interface InstrumentRef {
  isin: string | null
  symbol: string
}

/** Lädt die Kurshistorie eines Instruments — per ISIN oder (falls keine) per Symbol. */
export function useHistory(): {
  points: Ref<QuotePoint[]>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: (item: InstrumentRef) => Promise<void>
} {
  const points = ref<QuotePoint[]>([])
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function load(item: InstrumentRef): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const path = item.isin
        ? `/quote/${item.isin}/history?limit=500`
        : `/quote/by-symbol/${encodeURIComponent(item.symbol)}/history?limit=500`
      points.value = await apiClient.get<QuotePoint[]>(path)
    } catch (err) {
      error.value = 'Historie konnte nicht geladen werden'
      consola.error('useHistory.load', err)
    } finally {
      loading.value = false
    }
  }

  return { points, loading, error, load }
}
