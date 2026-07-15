import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import { instrumentPath } from '../api/paths'
import type { DailyPoint, InstrumentRef } from '../types'

/** Zeitraum-Kürzel für die EOD-Historie. */
export type DailyPeriod = '1w' | '1m' | '3m' | '1y' | 'max'

/** Lädt echte Tages-Schlusskurse (EOD) über einen Zeitraum (inkrementell gecacht). */
export function useDaily(): {
  daily: Ref<DailyPoint[]>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: (item: InstrumentRef, period: DailyPeriod) => Promise<void>
  clear: () => void
} {
  const daily = ref<DailyPoint[]>([])
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  // Zähler gegen Races: nur die jüngste Anfrage darf die Refs beschreiben.
  let requestId = 0

  async function load(item: InstrumentRef, period: DailyPeriod): Promise<void> {
    const currentRequest = ++requestId
    loading.value = true
    error.value = null
    try {
      const path = instrumentPath('/quote', item, `/daily?period=${period}`)
      const result = await apiClient.get<DailyPoint[]>(path)
      if (currentRequest !== requestId) return // veraltete Antwort verwerfen
      daily.value = result
    } catch (err) {
      if (currentRequest !== requestId) return
      error.value = 'Tageshistorie konnte nicht geladen werden'
      consola.error('useDaily.load', err)
    } finally {
      if (currentRequest === requestId) loading.value = false
    }
  }

  /** Setzt Tageshistorie und Fehlerzustand zurück (z.B. nach Abwahl des Instruments). */
  function clear(): void {
    requestId++ // laufende Antworten verwerfen
    daily.value = []
    error.value = null
    loading.value = false
  }

  return { daily, loading, error, load, clear }
}
