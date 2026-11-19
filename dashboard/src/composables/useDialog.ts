import { ref, watch, type Ref } from 'vue'

/**
 * Der zuletzt gezeigte Inhalt eines Dialogs — er bleibt, bis die Ausblendung durch ist.
 *
 * Hinge der Inhalt direkt am Wert des Aufrufers, leerte sich der Kasten in dem
 * Moment, in dem dieser seine Auswahl zurücksetzt; ausgeblendet würde dann ein
 * leerer Rahmen mit zwei Knöpfen.
 *
 * @param source - Liest den aktuellen Wert; `null` heißt „Dialog zu".
 * @param onShow - Läuft, sobald ein neuer Wert erscheint (etwa: Inhalt laden).
 * @returns Die Kopie, die das Template anzeigt.
 */
export function useLastShown<T>(source: () => T | null, onShow?: (value: T) => void): Ref<T | null> {
  const shown = ref(null) as Ref<T | null>
  watch(source, (value) => {
    if (value === null) return
    shown.value = value
    onShow?.(value)
  }, { immediate: true })
  return shown
}

/**
 * Setzt den Fokus auf eine Naive-Komponente, etwa „Abbrechen" — damit ein
 * versehentliches Enter nichts bestätigt. Erst nach der Einblendung aufrufen,
 * vorher steht das Element noch nicht im Dokument.
 */
export function focusComponent(target: Ref<{ $el?: unknown } | null>): void {
  const element = target.value?.$el as HTMLElement | undefined
  element?.focus()
}
