import type { Ref } from 'vue'

import { apiClient } from '../api/client'
import type { InstrumentSummary } from '../types'
import { useRequest } from './useRequest'

/** Lädt die Liste aller gecachten Instrumente. */
export function useInstruments(): {
  instruments: Ref<InstrumentSummary[]>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: () => Promise<void>
} {
  const { data, loading, error, run } = useRequest<InstrumentSummary[]>({
    initial: [],
    request: () => apiClient.get<InstrumentSummary[]>('/instruments'),
    failure: 'errors.instruments',
    logTag: 'useInstruments.load',
  })
  return { instruments: data, loading, error, load: run }
}
