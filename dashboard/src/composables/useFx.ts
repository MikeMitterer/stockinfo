import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import { fxPath } from '../api/paths'
import { translate } from '../i18n'
import type { FxRate } from '../types'

/** Holt einen Wechselkurs (1 base = rate quote). */
export function useFx(): {
  result: Ref<FxRate | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  convert: (base: string, quote: string) => Promise<void>
} {
  const result = ref<FxRate | null>(null)
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function convert(base: string, quote: string): Promise<void> {
    loading.value = true
    error.value = null
    result.value = null
    try {
      result.value = await apiClient.get<FxRate>(fxPath(base, quote))
    } catch (err) {
      error.value = translate('errors.fx')
      consola.error('useFx.convert', err)
    } finally {
      loading.value = false
    }
  }

  return { result, loading, error, convert }
}
