import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import type { RefreshResult } from '../types'
import { translate } from '../i18n'

/** Globaler Refresh aller Instrumente. */
export function useRefresh(): {
  refreshing: Ref<boolean>
  result: Ref<RefreshResult | null>
  error: Ref<string | null>
  trigger: () => Promise<void>
} {
  const refreshing = ref<boolean>(false)
  const result = ref<RefreshResult | null>(null)
  const error = ref<string | null>(null)

  async function trigger(): Promise<void> {
    refreshing.value = true
    error.value = null
    try {
      result.value = await apiClient.post<RefreshResult>('/refresh')
    } catch (err) {
      error.value = translate('errors.refresh')
      consola.error('useRefresh.trigger', err)
    } finally {
      refreshing.value = false
    }
  }

  return { refreshing, result, error, trigger }
}
