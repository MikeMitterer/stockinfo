import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import { translate } from '../i18n'
import type { ExchangesResponse } from '../types'

/** Lädt den aktiven Börsenkatalog samt deklarierter Quellenunterstützung. */
export function useExchanges(): {
  data: Ref<ExchangesResponse | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: () => Promise<void>
} {
  const data = ref<ExchangesResponse | null>(null)
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function load(): Promise<void> {
    if (loading.value) return
    loading.value = true
    error.value = null
    try {
      data.value = await apiClient.get<ExchangesResponse>('/exchanges')
    } catch (err) {
      data.value = null
      error.value = translate('errors.exchanges')
      consola.error('useExchanges.load', err)
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, load }
}
