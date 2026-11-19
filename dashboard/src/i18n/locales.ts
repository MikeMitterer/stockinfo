import { dateDeDE, dateEnUS, deDE, enUS, type NDateLocale, type NLocale } from 'naive-ui'
import { de as dateFnsDe, enUS as dateFnsEn, type Locale as DateFnsLocale } from 'date-fns/locale'

import { LICENSE_URLS } from '../config'
import { FALLBACK_LOCALE, type LocaleKey } from './index'

/** Was eine Sprache außer ihrem Katalog braucht: Locales der Bibliotheken und Verweise. */
export interface LocaleSettings {
  /** Eingebaute Beschriftungen von Naive UI („Bestätigen“, „Abbrechen“). */
  naive: NLocale
  /** Datums- und Kalenderbeschriftungen von Naive UI. */
  naiveDate: NDateLocale
  /** Monatsnamen und Wochentage der Diagrammachse (date-fns). */
  dateFns: DateFnsLocale
  /** Lizenztext in dieser Sprache. */
  licenseUrl: string
}

/**
 * **Die eine Stelle, an der eine Sprache gewählt wird.**
 *
 * Bis T-138 stand `locale === 'de' ? … : …` an sechs Stellen. Eine weitere
 * Sprache braucht jetzt ihren Katalog (`de.ts`, `en.ts`, auch mit den
 * Datumsmustern des Diagramms unter `chart.format`) und einen Eintrag hier;
 * `satisfies` lässt keinen fehlen.
 */
const SETTINGS = {
  de: { naive: deDE, naiveDate: dateDeDE, dateFns: dateFnsDe, licenseUrl: LICENSE_URLS.de },
  en: { naive: enUS, naiveDate: dateEnUS, dateFns: dateFnsEn, licenseUrl: LICENSE_URLS.en },
} satisfies Record<LocaleKey, LocaleSettings>

/**
 * Die Einstellungen der Sprache — für eine unbekannte die der Rückfallsprache.
 *
 * @param locale - Aktuelle Sprache der Oberfläche.
 */
export function localeSettings(locale: string): LocaleSettings {
  return SETTINGS[locale as LocaleKey] ?? SETTINGS[FALLBACK_LOCALE]
}

/**
 * Die Beschriftung eines Felds aus dem Backend-Katalog in der Sprache der Oberfläche.
 *
 * Der Server liefert `label_<sprache>` je Feld; fehlt die Sprache oder ist
 * die Beschriftung leer, gilt die englische.
 *
 * @param labels - Ein Objekt mit `label_en` und weiteren `label_<sprache>`.
 * @param locale - Aktuelle Sprache der Oberfläche.
 */
export function localizedLabel(labels: { label_en: string }, locale: string): string {
  const label: unknown = (labels as Record<string, unknown>)[`label_${locale}`]
  return typeof label === 'string' && label !== '' ? label : labels.label_en
}
