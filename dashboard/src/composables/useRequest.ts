import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { describeFailure } from '../api/reason'
import { translate, type MessageKey } from '../i18n'

/** Was `useRequest` braucht: den Aufruf, den Startwert und wie ein Fehler heißt. */
export interface RequestOptions<T, A extends unknown[]> {
  /** Wert vor dem ersten Aufruf. */
  initial: T
  /** Der eigentliche API-Aufruf. */
  request: (...args: A) => Promise<T>
  /** Katalogschlüssel der Meldung, falls der Aufruf scheitert. */
  failure: MessageKey
  /** Kennung im Konsolenprotokoll, etwa `useInstruments.load`. */
  logTag: string
  /** Bei einem Fehler den bisherigen Wert verwerfen (Vorgabe: behalten). */
  clearOnError?: boolean
  /** Einen neuen Aufruf ignorieren, solange einer läuft (Vorgabe: nein). */
  skipWhileLoading?: boolean
}

/**
 * Lade- und Fehlerzustand eines API-Aufrufs — das Gerüst, das vorher in jedem
 * Composable gleich stand.
 *
 * Die Fehlermeldung nennt neben der Kategorie den Grund des Backends
 * (`describeFailure`); vorher ging er in mehreren Composables verloren.
 *
 * @returns `data`, `loading`, `error` und `run`, das den Aufruf startet.
 */
export function useRequest<T, A extends unknown[] = []>(options: RequestOptions<T, A>): {
  data: Ref<T>
  loading: Ref<boolean>
  error: Ref<string | null>
  run: (...args: A) => Promise<void>
} {
  const data = ref(options.initial) as Ref<T>
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function run(...args: A): Promise<void> {
    if (options.skipWhileLoading && loading.value) return
    loading.value = true
    error.value = null
    try {
      data.value = await options.request(...args)
    } catch (err) {
      if (options.clearOnError) data.value = options.initial
      error.value = describeFailure(translate(options.failure), err)
      consola.error(options.logTag, err)
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, run }
}
