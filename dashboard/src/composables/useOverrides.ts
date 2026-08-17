import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import { translate } from '../i18n'
import type { InstrumentOverrides, InstrumentSummary, OverrideField } from '../types'

/**
 * Von Hand nachgetragene Kennzahlen schreiben (T-09).
 *
 * Für Papiere, die nicht über justETF/extraETF laufen, bleiben TER,
 * Volatilität und Thesaurierung leer. Hier lassen sie sich eintragen — die
 * Vorrang-Regel wendet das Backend an: Was die Quelle liefert, gewinnt; ein
 * manueller Wert füllt nur Lücken.
 *
 * Geschrieben wird immer der **vollständige Satz**. Ein einzelnes Feld zu
 * schicken hieße, dass die anderen „unverändert" bedeuten — dann könnte man
 * einen Wert nie wieder löschen.
 */
export function useOverrides(): {
  saving: Ref<string | null>
  error: Ref<string | null>
  save: (item: InstrumentSummary, patch: Partial<InstrumentOverrides>) => Promise<void>
} {
  /** Symbol des Papiers, das gerade gespeichert wird — für die Zeilen-Anzeige. */
  const saving = ref<string | null>(null)
  const error = ref<string | null>(null)

  async function save(
    item: InstrumentSummary,
    patch: Partial<InstrumentOverrides>,
  ): Promise<void> {
    const payload: InstrumentOverrides = {
      ter: item.manual_ter,
      volatility: item.manual_volatility,
      accumulating: item.manual_accumulating,
      provider: item.manual_provider,
      replication: item.manual_replication,
      fund_size: item.manual_fund_size,
      fund_domicile: item.manual_fund_domicile,
      fund_currency: item.manual_fund_currency,
      ...patch,
    }

    saving.value = item.symbol
    error.value = null
    try {
      const pfad = `/instruments/by-symbol/${encodeURIComponent(item.symbol)}/overrides`
      await apiClient.put(pfad, payload)
    } catch (err) {
      error.value = translate('errors.overrides')
      consola.error('useOverrides.save', item.symbol, err)
    } finally {
      saving.value = null
    }
  }

  return { saving, error, save }
}

/**
 * Woher der angezeigte Wert kommt — für die Kennzeichnung in der Zeile.
 *
 * `'manual'`   Der Wert stammt aus der Eingabe; die Quelle hat keinen.
 * `'shadowed'` Es gibt eine Eingabe, aber die Quelle liefert etwas und gewinnt.
 * `null`       Nichts Manuelles im Spiel.
 */
export function overrideState(
  item: InstrumentSummary,
  field: OverrideField,
): 'manual' | 'shadowed' | null {
  if (item.manual_fields.includes(field)) return 'manual'
  if (item.shadowed_fields.includes(field)) return 'shadowed'
  return null
}

/**
 * Der von Hand gepflegte Rohwert einer Kennzahl.
 *
 * Ohne Verzweigung über die acht Felder: `manual_<field>` heißt für jedes
 * Feld exakt so wie sein Gegenstück in `InstrumentSummary`, der Zugriff ist
 * also generisch möglich statt in acht gleichförmigen Zweigen.
 */
export function manualValue(
  item: InstrumentSummary,
  field: OverrideField,
): number | boolean | string | null {
  return item[`manual_${field}`]
}

/**
 * Liefert die Quelle einen Wert für dieses Feld — nicht nur die Eingabe?
 *
 * Die Vorrang-Regel in einer Funktion statt dreimal (Nacharbeit Sichtprüfung,
 * I4): `MetricValue.vue`, `MetricEditor.vue` und `InstrumentDrilldown.vue`
 * formulierten bislang unabhängig voneinander dieselbe Prüfung — heute
 * gleichbedeutend, aus drei verschiedenen Tasks entstanden und beim nächsten
 * Feinschliff ein Kandidat zum Auseinanderlaufen.
 *
 * `item[field]` ist bereits der **wirksame** Wert (das Backend löst die
 * Vorrang-Regel auf); „nicht null" allein reicht deshalb nicht — im Zustand
 * `manual` ist der wirksame Wert der eingetragene, nicht der der Quelle.
 */
export function sourceProvides(item: InstrumentSummary, field: OverrideField): boolean {
  return overrideState(item, field) !== 'manual' && item[field] !== null
}
