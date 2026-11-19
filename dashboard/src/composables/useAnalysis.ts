import type { Ref } from 'vue'

import { apiClient } from '../api/client'
import { analyzePath } from '../api/paths'
import type { AnalyzeResult, InstrumentRef } from '../types'
import { useRequest } from './useRequest'

/** Führt eine On-Demand-Stage-Analyse für ein Instrument aus. */
export function useAnalysis(): {
  result: Ref<AnalyzeResult | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  analyze: (instrument: InstrumentRef) => Promise<void>
} {
  const { data, loading, error, run } = useRequest<AnalyzeResult | null, [InstrumentRef]>({
    initial: null,
    request: (instrument) => apiClient.get<AnalyzeResult>(analyzePath(instrument)),
    failure: 'errors.analysis',
    logTag: 'useAnalysis.analyze',
  })
  return { result: data, loading, error, analyze: run }
}
