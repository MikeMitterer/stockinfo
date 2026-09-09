import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import { describeFailure } from '../api/reason'
import { instrumentPath, isIsin } from '../api/paths'
import { i18n, translate } from '../i18n'
import type { InstrumentRef, InstrumentSummary, IntakeConfirmation, PendingIntake } from '../types'

export { isIsin }

/** Aktionen auf einzelnen Instrumenten: hinzufügen, aktualisieren, löschen. */
export function useInstrumentActions(): {
  busy: Ref<boolean>
  error: Ref<string | null>
  pendingIntake: Ref<PendingIntake | null>
  add: (identifier: string) => Promise<boolean>
  confirmAdd: () => Promise<boolean>
  cancelAdd: () => void
  refreshOne: (item: InstrumentRef) => Promise<void>
  remove: (item: InstrumentRef) => Promise<void>
  setIsin: (symbol: string, isin: string) => Promise<void>
} {
  const busy = ref<boolean>(false)
  const error = ref<string | null>(null)
  const pendingIntake = ref<PendingIntake | null>(null)

  async function run(action: () => Promise<unknown>, message: string): Promise<void> {
    busy.value = true
    error.value = null
    try {
      await action()
    } catch (err) {
      // **Die Kategorie allein genügt nicht.** Bis T-35 stand hier nur
      // `message`, und der eigentliche Grund landete ausschließlich in der
      // Konsole: Wer eine unauflösbare ISIN eintippte, las „Hinzufügen
      // fehlgeschlagen" und erfuhr nie, dass es das Papier nicht gibt.
      error.value = describeFailure(message, err)
      consola.error('useInstrumentActions', message, err)
    } finally {
      busy.value = false
    }
  }

  /** Fordert die Aufnahme an; true bedeutet tatsächlich gespeichert. */
  async function submitIntake(identifier: string, confirmed?: IntakeConfirmation['identity']): Promise<boolean> {
    if (busy.value) return false
    let stored = false
    await run(async () => {
      const result = await apiClient.post<InstrumentSummary | IntakeConfirmation>('/instruments/intake', {
        identifier, check_exchange: true, ...(confirmed ? { confirmed_listing: confirmed } : {}),
      })
      if ('status' in result && result.status === 'confirmation_required') {
        pendingIntake.value = { identifier, decision: result }
      } else {
        pendingIntake.value = null
        stored = true
      }
    }, i18n.global.t('errors.addIdentifier', { identifier }))
    return stored
  }

  /** Ein offener Dialog behält seine Eingabe bis zur Entscheidung. */
  async function add(identifier: string): Promise<boolean> {
    if (pendingIntake.value) return false
    return submitIntake(identifier.trim())
  }

  /** Bestätigt nur das zuletzt angezeigte Listing. */
  async function confirmAdd(): Promise<boolean> {
    const pending = pendingIntake.value
    return pending ? submitIntake(pending.identifier, pending.decision.identity) : false
  }

  /** Abbrechen ist lokal und schreibt nichts. Während des Speicherns gesperrt. */
  function cancelAdd(): void {
    if (!busy.value) pendingIntake.value = null
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

  return { busy, error, pendingIntake, add, confirmAdd, cancelAdd, refreshOne, remove, setIsin }
}
