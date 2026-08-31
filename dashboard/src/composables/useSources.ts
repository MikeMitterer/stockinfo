import { consola } from 'consola'
import { computed, ref, type ComputedRef, type Ref } from 'vue'

import { apiClient } from '../api/client'
import type { SourcesInfo } from '../types'

/**
 * Die konfigurierten Quellenketten.
 *
 * **Ein Nebenabruf, kein tragender.** Antwortet `/sources` nicht, fehlt die
 * Angabe; es gibt kein `error` nach außen.
 */
export function useSources(): {
  sources: Ref<SourcesInfo | null>
  quoteChain: ComputedRef<string[]>
  load: () => Promise<void>
} {
  const sources = ref<SourcesInfo | null>(null)

  /**
   * Die einsatzbereiten Quellen der Rolle `quotes`, in ihrer Rangfolge.
   *
   * **Die Kette, nicht ihr Kopf.** `/sources` beschreibt, wer gefragt wird —
   * nicht, wer eine bestimmte gespeicherte Quote geliefert hat; die Herkunft
   * einer einzelnen Antwort führt weder das REST-Modell noch die Tabelle. Ein
   * einzelner Name wäre deshalb eine Aussage, die diese Daten nicht decken.
   *
   * Nicht einsatzbereite Quellen fehlen: Sie werden beim Bau aus der
   * Laufzeitkette entfernt und können daher nicht antworten.
   */
  const quoteChain = computed<string[]>(() =>
    (sources.value?.sources ?? [])
      .filter((entry) => entry.role === 'quotes' && entry.configured)
      .sort((first, second) => first.position - second.position)
      .map((entry) => entry.name),
  )

  async function load(): Promise<void> {
    try {
      sources.value = await apiClient.get<SourcesInfo>('/sources')
    } catch (err) {
      sources.value = null
      consola.warn('useSources.load', err)
    }
  }

  return { sources, quoteChain, load }
}
