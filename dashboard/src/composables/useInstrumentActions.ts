import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'

/** Prüft, ob ein String das ISIN-Format hat (2 Buchstaben, 9 alphanum., 1 Ziffer). */
export function isIsin(value: string): boolean {
  return /^[A-Z]{2}[A-Z0-9]{9}[0-9]$/.test(value)
}

/** Ein Instrument, identifiziert per ISIN (falls vorhanden) oder Symbol. */
interface InstrumentRef {
  isin: string | null
  symbol: string
}

/** Aktionen auf einzelnen Instrumenten: hinzufügen, aktualisieren, löschen. */
export function useInstrumentActions(): {
  busy: Ref<boolean>
  error: Ref<string | null>
  add: (identifier: string) => Promise<void>
  refreshOne: (item: InstrumentRef) => Promise<void>
  remove: (item: InstrumentRef) => Promise<void>
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

  async function refreshOne(item: InstrumentRef): Promise<void> {
    const path = item.isin
      ? `/refresh/${item.isin}`
      : `/refresh/by-symbol/${encodeURIComponent(item.symbol)}`
    await run(() => apiClient.post(path), 'Aktualisieren fehlgeschlagen')
  }

  async function remove(item: InstrumentRef): Promise<void> {
    const path = item.isin
      ? `/instruments/${item.isin}`
      : `/instruments/by-symbol/${encodeURIComponent(item.symbol)}`
    await run(() => apiClient.del(path), 'Löschen fehlgeschlagen')
  }

  return { busy, error, add, refreshOne, remove }
}
