import type { Ref } from 'vue'

import { apiClient } from '../api/client'
import type { ExchangesResponse } from '../types'
import { useRequest } from './useRequest'

/** Lädt den aktiven Börsenkatalog samt deklarierter Quellenunterstützung. */
export function useExchanges(): {
  data: Ref<ExchangesResponse | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: () => Promise<void>
} {
  const { data, loading, error, run } = useRequest<ExchangesResponse | null>({
    initial: null,
    request: () => apiClient.get<ExchangesResponse>('/exchanges'),
    failure: 'errors.exchanges',
    logTag: 'useExchanges.load',
    // Ein veralteter Katalog wäre irreführender als keiner.
    clearOnError: true,
    skipWhileLoading: true,
  })
  return { data, loading, error, load: run }
}
