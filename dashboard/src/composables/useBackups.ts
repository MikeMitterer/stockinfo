import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import type { BackupList, RestoreAccepted } from '../types'

/**
 * Die Sicherungen einer Instanz — laden, anlegen, wiederherstellen.
 *
 * **Nach jeder Handlung wird neu geladen.** Anlegen verdrängt die älteste,
 * Wiederherstellen setzt einen ausstehenden Neustart: Beides ändert den
 * Serverzustand, und eine Ansicht, die ihren eigenen Stand fortschreibt, zeigt
 * danach etwas anderes als die Instanz.
 */
export function useBackups(): {
  data: Ref<BackupList | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: () => Promise<void>
  create: () => Promise<void>
  restore: (name: string, force: boolean) => Promise<boolean>
} {
  const data = ref<BackupList | null>(null)
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function load(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      data.value = await apiClient.get<BackupList>('/backups')
    } catch (err) {
      error.value = String(err)
      consola.warn('useBackups.load', err)
    } finally {
      loading.value = false
    }
  }

  async function create(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      await apiClient.post<unknown>('/backups')
    } catch (err) {
      error.value = String(err)
      consola.warn('useBackups.create', err)
    } finally {
      loading.value = false
    }
    await load()
  }

  /**
   * Merkt eine Sicherung zum Einspielen vor.
   *
   * @param name Der Dateiname aus der Liste.
   * @param force Eine abweichende Quellenlage übergehen. Das entscheidet
   *   ausdrücklich der Benutzer im Dialog — eine unpassende Sicherung wird
   *   sonst mit `409` abgelehnt.
   * @returns Ob die Absicht angenommen wurde.
   */
  async function restore(name: string, force: boolean): Promise<boolean> {
    loading.value = true
    error.value = null
    let accepted = false
    try {
      await apiClient.post<RestoreAccepted>(
        `/backups/${encodeURIComponent(name)}/restore${force ? '?force=true' : ''}`,
      )
      accepted = true
    } catch (err) {
      error.value = String(err)
      consola.warn('useBackups.restore', err)
    } finally {
      loading.value = false
    }
    await load()
    return accepted
  }

  return { data, loading, error, load, create, restore }
}
