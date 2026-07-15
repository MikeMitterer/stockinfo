import { consola } from 'consola'

/**
 * Kopiert Text in die Zwischenablage.
 *
 * Bevorzugt die Clipboard-API; die existiert aber nur in Secure Contexts
 * (https bzw. localhost). Auf http (z.B. Unraid ohne TLS) greift der
 * Legacy-Fallback über eine temporäre Textarea + execCommand('copy').
 *
 * @param text - Der zu kopierende Text.
 * @returns true wenn kopiert wurde, false wenn beide Wege scheiterten.
 */
export async function copyText(text: string): Promise<boolean> {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch (err) {
      consola.warn('copyText: Clipboard-API fehlgeschlagen — Fallback', err)
    }
  }
  return legacyCopy(text)
}

/** Legacy-Kopierweg für unsichere Kontexte: Textarea einfügen, markieren, copy. */
function legacyCopy(text: string): boolean {
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.setAttribute('readonly', '')
  // Unsichtbar, aber selektierbar — display:none würde die Selektion verhindern.
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.select()
  try {
    return document.execCommand('copy')
  } catch (err) {
    consola.error('copyText: execCommand-Fallback fehlgeschlagen', err)
    return false
  } finally {
    textarea.remove()
  }
}
