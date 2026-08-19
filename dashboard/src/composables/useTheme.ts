/**
 * Das aktive Theme.
 *
 * Die Paletten, ihre Kennungen und die Vorgaben liegen im Fundament — hier
 * bleibt nur, was diese App darüber weiß: unter welchem Schlüssel sie die Wahl
 * speichert.
 *
 * Bewusst im `localStorage` und nicht in einer Datenbank: Die Wahl muss beim
 * allerersten Bildaufbau feststehen, sonst blitzt kurz das falsche Theme auf.
 */
import { ref, type Ref } from 'vue'
import {
  DEFAULT_DARK_THEME,
  DEFAULT_LIGHT_THEME,
  isThemeId,
  safeStorage,
  THEMES,
  THEME_IDS,
  type ThemeId,
} from '@mmit/ux-foundation'

const STORAGE_KEY = 'stockinfo-theme'

// Modul-Level-Singleton — alle Konsumenten teilen sich den Zustand.
const current = ref<ThemeId>(DEFAULT_DARK_THEME)

/**
 * Fragt das Betriebssystem, ob es dunkel eingestellt ist.
 *
 * Ältere Umgebungen und die Testumgebung kennen `matchMedia` nicht — dort gilt
 * dunkel, weil die Sammlung überwiegend dunkle Themes mitbringt.
 */
function prefersDark(): boolean {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return true
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

/** Vorgabe für den allerersten Start — richtet sich nach dem System. */
export function systemTheme(): ThemeId {
  return prefersDark() ? DEFAULT_DARK_THEME : DEFAULT_LIGHT_THEME
}

/** Setzt das Theme am Wurzelelement und merkt es sich. */
function apply(theme: ThemeId): void {
  current.value = theme
  document.documentElement.dataset.theme = theme
  // Naive UI und Formularelemente richten sich nach `color-scheme`.
  document.documentElement.style.colorScheme = THEMES[theme].isDark ? 'dark' : 'light'
  safeStorage.write(STORAGE_KEY, theme)
}

/**
 * Liest die gespeicherte Wahl.
 *
 * Die App hatte früher acht eigene Paletten; vier ihrer Namen (`earth`,
 * `night`, `sunset`, `neon`) gibt es im Fundament nicht. Eine solche Wahl
 * fällt hier auf die Systemvorgabe zurück — ohne diese Prüfung stünde ein
 * ungültiges `data-theme` am Wurzelelement und die App wäre farblos.
 */
export function readStoredTheme(): ThemeId {
  const gespeichert = safeStorage.read(STORAGE_KEY)
  return isThemeId(gespeichert) ? gespeichert : systemTheme()
}

/** Theme-Verwaltung: aktuelles Theme, Liste, Setzen und Initialisieren. */
export function useTheme(): {
  current: Ref<ThemeId>
  themes: readonly ThemeId[]
  setTheme: (theme: ThemeId) => void
  init: () => void
} {
  function init(): void {
    apply(readStoredTheme())
  }

  return { current, themes: THEME_IDS, setTheme: apply, init }
}
