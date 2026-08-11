import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import { translate } from '../i18n'
import type { ExchangesResponse } from '../types'

/** Lädt die weltweite Börsentabelle inkl. konfigurierter Default-Börse. */
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
    loading.value = true
    error.value = null
    try {
      data.value = await apiClient.get<ExchangesResponse>('/exchanges')
    } catch (err) {
      error.value = translate('errors.exchanges')
      consola.error('useExchanges.load', err)
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, load }
}
