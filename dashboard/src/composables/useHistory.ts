import type { Ref } from 'vue'

import { apiClient } from '../api/client'
import { instrumentPath } from '../api/paths'
import type { InstrumentRef, QuotePoint } from '../types'
import { useRequest } from './useRequest'

/** Lädt die Kurshistorie eines Instruments — per ISIN oder (falls keine) per Symbol. */
export function useHistory(): {
  points: Ref<QuotePoint[]>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: (item: InstrumentRef) => Promise<void>
  clear: () => void
} {
  const { data, loading, error, run, reset } = useRequest<QuotePoint[], [InstrumentRef]>({
    initial: [],
    request: (item) => apiClient.get<QuotePoint[]>(instrumentPath('/quote', item, '/history?limit=500')),
    failure: 'errors.history',
    logTag: 'useHistory.load',
    latestOnly: true,
  })
  // `clear` setzt Historie und Fehlerzustand zurück (z.B. nach Abwahl des Instruments).
  return { points: data, loading, error, load: run, clear: reset }
}
