import type { Ref } from 'vue'

import { apiClient } from '../api/client'
import { instrumentPath } from '../api/paths'
import type { DailyPoint, InstrumentRef } from '../types'
import { useRequest } from './useRequest'

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
  // Die Meldung nennt **Kategorie und Grund**: Das Backend nennt hier eine
  // Kennung, und „konnte nicht geladen werden" allein verschwiege, ob es die
  // Reihe nicht gibt oder eine Quelle gestört war.
  const { data, loading, error, run, reset } = useRequest<DailyPoint[], [InstrumentRef, DailyPeriod]>({
    initial: [],
    request: (item, period) =>
      apiClient.get<DailyPoint[]>(instrumentPath('/quote', item, `/daily?period=${period}`)),
    failure: 'errors.daily',
    logTag: 'useDaily.load',
    latestOnly: true,
  })
  // `clear` setzt Tageshistorie und Fehlerzustand zurück (z.B. nach Abwahl des Instruments).
  return { daily: data, loading, error, load: run, clear: reset }
}
