import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import type { DailyPoint } from '../types'

/** Ein Instrument, identifiziert per ISIN (falls vorhanden) oder Symbol. */
interface InstrumentRef {
  isin: string | null
  symbol: string
}

/** Zeitraum-Kürzel für die EOD-Historie. */
export type DailyPeriod = '1w' | '1m' | '3m' | '1y' | 'max'

/** Lädt echte Tages-Schlusskurse (EOD) über einen Zeitraum (inkrementell gecacht). */
export function useDaily(): {
  daily: Ref<DailyPoint[]>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: (item: InstrumentRef, period: DailyPeriod) => Promise<void>
} {
  const daily = ref<DailyPoint[]>([])
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function load(item: InstrumentRef, period: DailyPeriod): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const base = item.isin
        ? `/quote/${item.isin}/daily`
        : `/quote/by-symbol/${encodeURIComponent(item.symbol)}/daily`
      daily.value = await apiClient.get<DailyPoint[]>(`${base}?period=${period}`)
    } catch (err) {
      error.value = 'Tageshistorie konnte nicht geladen werden'
      consola.error('useDaily.load', err)
    } finally {
      loading.value = false
    }
  }

  return { daily, loading, error, load }
}
