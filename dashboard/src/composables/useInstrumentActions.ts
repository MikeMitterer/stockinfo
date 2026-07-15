import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import { instrumentPath, isIsin, quotePath } from '../api/paths'
import { translate } from '../i18n'
import type { InstrumentRef } from '../types'

export { isIsin }

/** Aktionen auf einzelnen Instrumenten: hinzufügen, aktualisieren, löschen. */
export function useInstrumentActions(): {
  busy: Ref<boolean>
  error: Ref<string | null>
  add: (identifier: string) => Promise<void>
  refreshOne: (item: InstrumentRef) => Promise<void>
  remove: (item: InstrumentRef) => Promise<void>
  setIsin: (symbol: string, isin: string) => Promise<void>
} {
  const busy = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function run(action: () => Promise<unknown>, message: string): Promise<void> {
    busy.value = true
    error.value = null
    try {
      await action()
    } catch (err) {
      error.value = message
      consola.error('useInstrumentActions', message, err)
    } finally {
      busy.value = false
    }
  }

  async function add(identifier: string): Promise<void> {
    const trimmed = identifier.trim()
    const path = quotePath({ isin: isIsin(trimmed) ? trimmed : null, symbol: trimmed })
    await run(() => apiClient.get(path), translate('errors.add'))
  }

  async function refreshOne(item: InstrumentRef): Promise<void> {
    await run(() => apiClient.post(instrumentPath('/refresh', item)), translate('errors.refreshOne'))
  }

  async function remove(item: InstrumentRef): Promise<void> {
    await run(() => apiClient.del(instrumentPath('/instruments', item)), translate('errors.remove'))
  }

  async function setIsin(symbol: string, isin: string): Promise<void> {
    const path = `/instruments/by-symbol/${encodeURIComponent(symbol)}/isin`
    await run(() => apiClient.put(path, { isin }), translate('errors.setIsin'))
  }

  return { busy, error, add, refreshOne, remove, setIsin }
}
