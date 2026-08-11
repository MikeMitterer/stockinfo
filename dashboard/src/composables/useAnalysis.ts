import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import { analyzePath } from '../api/paths'
import { translate } from '../i18n'
import type { AnalyzeResult, InstrumentRef } from '../types'

/** Führt eine On-Demand-Stage-Analyse für ein Instrument aus. */
export function useAnalysis(): {
  result: Ref<AnalyzeResult | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  analyze: (instrument: InstrumentRef) => Promise<void>
} {
  const result = ref<AnalyzeResult | null>(null)
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function analyze(instrument: InstrumentRef): Promise<void> {
    loading.value = true
    error.value = null
    try {
      result.value = await apiClient.get<AnalyzeResult>(analyzePath(instrument))
    } catch (err) {
      error.value = translate('errors.analysis')
      consola.error('useAnalysis.analyze', err)
    } finally {
      loading.value = false
    }
  }

  return { result, loading, error, analyze }
}
