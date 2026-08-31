import { consola } from 'consola'
import { computed, ref, type ComputedRef, type Ref } from 'vue'

import { apiClient } from '../api/client'
import type { SourcesInfo } from '../types'

/**
 * Woher die angezeigten Kurse kommen.
 *
 * **Ein Nebenabruf, kein tragender.** Die Statuszeile ist eine Auskunft; wenn
 * `/sources` nicht antwortet, bleibt sie ohne diese Angabe stehen, statt einen
 * Fehler zu melden. Deshalb gibt es hier kein `error` nach außen — ein
 * Fehlschlag ist im Protokoll sichtbar und im UI schlicht die fehlende Angabe.
 */
export function useSources(): {
  sources: Ref<SourcesInfo | null>
  quoteSource: ComputedRef<string | null>
  load: () => Promise<void>
} {
  const sources = ref<SourcesInfo | null>(null)

  /**
   * Die **erste einsatzbereite** Quelle der Rolle `quotes`.
   *
   * Nicht einfach die erste konfigurierte: Eine Quelle, die nicht arbeiten
   * kann, liefert auch keinen Kurs — sie zu nennen wäre die genaue Umkehrung
   * dessen, wofür diese Zeile da ist. Ist keine bereit, steht dort nichts;
   * eine Zeile, die eine Quelle behauptet, wo keine antwortet, ist schlechter
   * als eine ohne Angabe.
   */
  const quoteSource = computed<string | null>(() => {
    const entries = (sources.value?.sources ?? [])
      .filter((entry) => entry.role === 'quotes' && entry.configured)
      .sort((first, second) => first.position - second.position)
    return entries[0]?.name ?? null
  })

  async function load(): Promise<void> {
    try {
      sources.value = await apiClient.get<SourcesInfo>('/sources')
    } catch (err) {
      sources.value = null
      consola.warn('useSources.load', err)
    }
  }

  return { sources, quoteSource, load }
}
