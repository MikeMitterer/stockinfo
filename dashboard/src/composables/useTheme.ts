import { ref, type Ref } from 'vue'

/** Verfügbare Themes (Namen an das MakeLib-Ökosystem angelehnt). */
export const THEMES = [
  { key: 'classic', label: 'Classic' },
  { key: 'ocean', label: 'Ocean' },
  { key: 'earth', label: 'Earth' },
  { key: 'night', label: 'Night' },
  { key: 'mono', label: 'Mono' },
  { key: 'sunset', label: 'Sunset' },
  { key: 'forest', label: 'Forest' },
  { key: 'neon', label: 'Neon' },
] as const

export type ThemeKey = (typeof THEMES)[number]['key']

const STORAGE_KEY = 'stockinfo-theme'
const DEFAULT_THEME: ThemeKey = 'classic'

// Modul-Level-Singleton — alle Konsumenten teilen sich den Zustand.
const current = ref<ThemeKey>(DEFAULT_THEME)

/** Setzt das Theme (data-theme am <html>) und persistiert es. */
function apply(theme: ThemeKey): void {
  current.value = theme
  document.documentElement.dataset.theme = theme
  try {
    window.localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    // localStorage nicht verfügbar — Theme bleibt nur zur Laufzeit gesetzt.
  }
}

/** Theme-Verwaltung: aktuelles Theme, Liste, Setzen und Initialisieren. */
export function useTheme(): {
  current: Ref<ThemeKey>
  themes: typeof THEMES
  setTheme: (theme: ThemeKey) => void
  init: () => void
} {
  function init(): void {
    let saved: string | null = null
    try {
      saved = window.localStorage.getItem(STORAGE_KEY)
    } catch {
      saved = null
    }
    const valid = THEMES.some((theme) => theme.key === saved)
    apply(valid ? (saved as ThemeKey) : DEFAULT_THEME)
  }

  return { current, themes: THEMES, setTheme: apply, init }
}
