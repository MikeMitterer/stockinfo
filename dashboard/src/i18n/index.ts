import { createI18n } from 'vue-i18n'

import { de } from './de'
import { en } from './en'

export type MessageSchema = typeof de

/** Alle Message-Keys in Punktnotation (z.B. 'errors.refresh') — compile-geprüft. */
type DottedKeys<T, Prefix extends string = ''> = {
  [K in keyof T & string]: T[K] extends string
    ? `${Prefix}${K}`
    : DottedKeys<T[K], `${Prefix}${K}.`>
}[keyof T & string]
export type MessageKey = DottedKeys<MessageSchema>

/** Verfügbare Sprachen (Anzeige-Labels kommen aus dem Katalog: language.*). */
export const LOCALES = ['de', 'en'] as const
export type LocaleKey = (typeof LOCALES)[number]

const STORAGE_KEY = 'stockinfo-lang'
const FALLBACK_LOCALE: LocaleKey = 'en'

/** Ermittelt die Startsprache: localStorage → Browser-Sprache → Fallback (en). */
export function detectLocale(): LocaleKey {
  let saved: string | null = null
  try {
    saved = window.localStorage.getItem(STORAGE_KEY)
  } catch {
    saved = null
  }
  if (LOCALES.some((locale) => locale === saved)) return saved as LocaleKey
  return navigator.language.toLowerCase().startsWith('de') ? 'de' : FALLBACK_LOCALE
}

export const i18n = createI18n({
  legacy: false,
  locale: detectLocale(),
  fallbackLocale: FALLBACK_LOCALE,
  messages: { de, en },
})

/** Setzt die Sprache, persistiert sie und aktualisiert das lang-Attribut. */
export function setLanguage(locale: LocaleKey): void {
  i18n.global.locale.value = locale
  document.documentElement.lang = locale
  try {
    window.localStorage.setItem(STORAGE_KEY, locale)
  } catch {
    // localStorage nicht verfügbar — Sprache gilt nur zur Laufzeit.
  }
}

/** Initialisiert das lang-Attribut passend zur erkannten Startsprache. */
export function initLanguage(): void {
  document.documentElement.lang = i18n.global.locale.value
}

/** Übersetzt außerhalb von Komponenten (Composables) über die globale Instanz. */
export function translate(key: MessageKey): string {
  return i18n.global.t(key)
}
