import { createI18n } from 'vue-i18n'
import { detectLocale, persistLocale } from '@mmit/ux-foundation'

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

/**
 * Ermittelt die Startsprache: gespeicherte Wahl → Browsersprache → Rückfall.
 *
 * Die Reihenfolge und die Abbildung `de-AT` → `de` liegen im Fundament. Die
 * frühere Fassung hier las nur `navigator.language`: Wer Englisch an erster
 * und Deutsch an zweiter Stelle führt, bekam Englisch, obwohl es den deutschen
 * Katalog gibt. Das fällt niemandem auf, es zeigt nur manchmal die falsche
 * Sprache.
 */
export function startLocale(): LocaleKey {
  return detectLocale(LOCALES, FALLBACK_LOCALE, STORAGE_KEY)
}

export const i18n = createI18n({
  legacy: false,
  locale: startLocale(),
  fallbackLocale: FALLBACK_LOCALE,
  messages: { de, en },
})

/** Setzt die Sprache, persistiert sie und aktualisiert das lang-Attribut. */
export function setLanguage(locale: LocaleKey): void {
  i18n.global.locale.value = locale
  // Schreibt die Wahl und zieht `lang` am Wurzelelement nach — ohne das trennt
  // der Browser Wörter nach den Regeln der falschen Sprache.
  persistLocale(locale, STORAGE_KEY)
}

/** Initialisiert das lang-Attribut passend zur erkannten Startsprache. */
export function initLanguage(): void {
  document.documentElement.lang = i18n.global.locale.value
}

/** Übersetzt außerhalb von Komponenten (Composables) über die globale Instanz. */
export function translate(key: MessageKey): string {
  return i18n.global.t(key)
}
