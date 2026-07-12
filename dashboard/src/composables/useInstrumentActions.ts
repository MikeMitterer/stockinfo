import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'

/** Prüft, ob ein String das ISIN-Format hat (2 Buchstaben, 9 alphanum., 1 Ziffer). */
export function isIsin(value: string): boolean {
  return /^[A-Z]{2}[A-Z0-9]{9}[0-9]$/.test(value)
}

/** Aktionen auf einzelnen Instrumenten: hinzufügen, aktualisieren, löschen. */
export function useInstrumentActions(): {
  busy: Ref<boolean>
  error: Ref<string | null>
  add: (identifier: string) => Promise<void>
  refreshOne: (isin: string) => Promise<void>
  remove: (isin: string) => Promise<void>
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
    const path = isIsin(trimmed)
      ? `/quote/${trimmed}`
      : `/quote?symbol=${encodeURIComponent(trimmed)}`
    await run(() => apiClient.get(path), 'Hinzufügen fehlgeschlagen')
  }

  async function refreshOne(isin: string): Promise<void> {
    await run(() => apiClient.post(`/refresh/${isin}`), 'Aktualisieren fehlgeschlagen')
  }

  async function remove(isin: string): Promise<void> {
    await run(() => apiClient.del(`/instruments/${isin}`), 'Löschen fehlgeschlagen')
  }

  return { busy, error, add, refreshOne, remove }
}
