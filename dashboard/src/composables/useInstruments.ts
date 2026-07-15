import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import type { InstrumentSummary } from '../types'
import { translate } from '../i18n'

/** Lädt die Liste aller gecachten Instrumente. */
export function useInstruments(): {
  instruments: Ref<InstrumentSummary[]>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: () => Promise<void>
} {
  const instruments = ref<InstrumentSummary[]>([])
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function load(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      instruments.value = await apiClient.get<InstrumentSummary[]>('/instruments')
    } catch (err) {
      error.value = translate('errors.instruments')
      consola.error('useInstruments.load', err)
    } finally {
      loading.value = false
    }
  }

  return { instruments, loading, error, load }
}
