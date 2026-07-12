import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import type { EnvInfo } from '../types'

/** Lädt den sichtbaren Ausschnitt der Backend-Konfiguration. */
export function useEnvironment(): {
  env: Ref<EnvInfo | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: () => Promise<void>
} {
  const env = ref<EnvInfo | null>(null)
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function load(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      env.value = await apiClient.get<EnvInfo>('/env')
    } catch (err) {
      error.value = 'Environment konnte nicht geladen werden'
      consola.error('useEnvironment.load', err)
    } finally {
      loading.value = false
    }
  }

  return { env, loading, error, load }
}
