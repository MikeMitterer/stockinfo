import type { Ref } from 'vue'

import { apiClient } from '../api/client'
import type { EnvInfo } from '../types'
import { useRequest } from './useRequest'

/** Lädt den sichtbaren Ausschnitt der Backend-Konfiguration. */
export function useEnvironment(): {
  env: Ref<EnvInfo | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: () => Promise<void>
} {
  const { data, loading, error, run } = useRequest<EnvInfo | null>({
    initial: null,
    request: () => apiClient.get<EnvInfo>('/env'),
    failure: 'errors.environment',
    logTag: 'useEnvironment.load',
  })
  return { env: data, loading, error, load: run }
}
