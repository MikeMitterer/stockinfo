const HIDE_DELAY_MS = 1000

/**
 * Blendet Scrollbars Mac-like nur während des Scrollens ein.
 *
 * Setzt beim Scrollen (Seite oder innere Container — Capture-Phase, scroll
 * bubbelt nicht) die Klasse `scrolling` auf <html> und entfernt sie nach der
 * Ruhezeit. Das zugehörige CSS in base.scss zeigt den Scrollbar-Thumb nur bei
 * `html.scrolling` oder Container-Hover.
 *
 * @param delayMs - Ruhezeit in ms, nach der die Scrollbar ausgeblendet wird.
 */
export function initScrollbarAutoHide(delayMs: number = HIDE_DELAY_MS): void {
  let hideTimer: number | undefined

  window.addEventListener(
    'scroll',
    () => {
      document.documentElement.classList.add('scrolling')
      window.clearTimeout(hideTimer)
      hideTimer = window.setTimeout(() => {
        document.documentElement.classList.remove('scrolling')
      }, delayMs)
    },
    { capture: true, passive: true },
  )
}
