import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import { describeFailure } from '../api/reason'
import { translate } from '../i18n'
import type { BackupList } from '../types'

/**
 * Die Sicherungen einer Instanz — laden, anlegen, wiederherstellen.
 *
 * **Nach einem Erfolg wird neu geladen, nach einem Fehlschlag nicht.** Beides
 * ändert den Serverzustand, und ein fortgeschriebener Eigenstand zeigte danach
 * etwas anderes als die Instanz; ein Nachladen im Fehlerfall löschte dagegen
 * die Meldung, für die der Aufruf gerade gescheitert ist.
 *
 * **Der Grund kommt aus dem Katalog**, nicht aus `String(err)` — sonst stünde
 * in der englischen Oberfläche ein deutscher Satz.
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
      error.value = describeFailure(translate('errors.backupsLoad'), err)
      consola.error('useBackups.load', err)
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
      error.value = describeFailure(translate('errors.backupCreate'), err)
      consola.error('useBackups.create', err)
      loading.value = false
      return
    }
    loading.value = false
    await load()
  }

  /**
   * Merkt eine Sicherung zum Einspielen vor.
   *
   * @param name Der Dateiname aus der Liste.
   * @param force Eine abweichende Quellenlage übergehen — das entscheidet der
   *   Benutzer ausdrücklich im Dialog.
   * @returns Ob die Absicht angenommen wurde.
   */
  async function restore(name: string, force: boolean): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await apiClient.post<unknown>(
        `/backups/${encodeURIComponent(name)}/restore${force ? '?force=true' : ''}`,
      )
    } catch (err) {
      error.value = describeFailure(translate('errors.backupRestore'), err)
      consola.error('useBackups.restore', err)
      loading.value = false
      return false
    }
    loading.value = false
    await load()
    return true
  }

  return { data, loading, error, load, create, restore }
}
