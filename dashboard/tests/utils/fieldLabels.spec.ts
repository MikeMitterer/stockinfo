import { describe, expect, it } from 'vitest'

import { i18n } from '../../src/i18n'
import { OVERRIDE_FIELDS } from '../../src/types'
import { FIELD_LABEL_KEY } from '../../src/utils/fieldLabels'

/*
 * Die Beschriftung einer Kennzahl gehört an genau eine Stelle.
 *
 * `InstrumentDrilldown.vue` (alle acht) und `MetricEditor.vue` (die vier
 * Textfelder, als Platzhalter im leeren Auswahlfeld) bildeten dieselben Felder
 * auf dieselben Katalog-Schlüssel ab — zwei Karten für eine Aussage. Läuft eine
 * davon weg, heißt dasselbe Feld in der Beschriftung anders als im
 * Platzhalter darunter.
 */
describe('FIELD_LABEL_KEY', () => {
  it('kennt jede der acht Kennzahlen', () => {
    expect(Object.keys(FIELD_LABEL_KEY).sort()).toEqual([...OVERRIDE_FIELDS].sort())
  })

  it.each(['de', 'en'] as const)('hat für jede Kennzahl einen Eintrag in %s', (locale) => {
    for (const field of OVERRIDE_FIELDS) {
      const key = FIELD_LABEL_KEY[field]
      // `t()` gibt bei fehlendem Eintrag den Schlüssel selbst zurück — genau
      // das darf hier nicht passieren.
      expect(i18n.global.t(key, {}, { locale })).not.toBe(key)
    }
  })
})
