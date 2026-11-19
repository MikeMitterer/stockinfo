import type { Ref } from 'vue'

import { apiClient } from '../api/client'
import type { DetailDefinition } from '../types'
import { useRequest } from './useRequest'

/**
 * Lädt den Katalog der Detailfelder (`GET /fields`): Art, Einheit, Grenzen, Beschriftung.
 *
 * Bewusst ohne Zwischenspeicher: Nach einem Neustart des Backends mit anderen
 * Quellen gilt ein anderer Katalog, und eine offene Seite soll ihn beim
 * nächsten Öffnen des Detailbereichs kennen.
 */
export function useFieldCatalog(): {
  definitions: Ref<DetailDefinition[]>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: () => Promise<void>
} {
  const { data, loading, error, run } = useRequest<DetailDefinition[]>({
    initial: [],
    request: async () => (await apiClient.get<{ details: DetailDefinition[] }>('/fields')).details,
    failure: 'details.loadFailed',
    logTag: 'useFieldCatalog.load',
  })
  return { definitions: data, loading, error, load: run }
}
