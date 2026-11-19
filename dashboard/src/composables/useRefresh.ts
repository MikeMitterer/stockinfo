import type { Ref } from 'vue'

import { apiClient } from '../api/client'
import type { RefreshResult } from '../types'
import { useRequest } from './useRequest'

/** Globaler Refresh aller Instrumente. */
export function useRefresh(): {
  refreshing: Ref<boolean>
  result: Ref<RefreshResult | null>
  error: Ref<string | null>
  trigger: () => Promise<void>
} {
  const { data, loading, error, run } = useRequest<RefreshResult | null>({
    initial: null,
    request: () => apiClient.post<RefreshResult>('/refresh'),
    failure: 'errors.refresh',
    logTag: 'useRefresh.trigger',
  })
  return { refreshing: loading, result: data, error, trigger: run }
}
