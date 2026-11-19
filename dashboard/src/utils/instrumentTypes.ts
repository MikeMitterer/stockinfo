import { i18n } from '../i18n'

/**
 * Die Gattung eines Papiers in der Sprache der Oberfläche.
 *
 * Die Gattungen des Core stehen im Katalog unter `instrumentTypes`. Eine
 * Gattung, die nur ein Plugin meldet, hat dort keinen Eintrag; sie erscheint
 * unverändert, weil die Kennung selbst lesbar ist (etwa `warrant`) — ein
 * Katalogschlüssel wäre es nicht.
 *
 * @param type - Gattung, wie das Backend sie liefert.
 */
export function instrumentTypeLabel(type: string): string {
  const key = `instrumentTypes.${type}`
  return i18n.global.te(key) ? i18n.global.t(key) : type
}
