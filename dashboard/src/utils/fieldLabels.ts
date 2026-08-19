import type { OverrideField } from '../types'

/**
 * Katalog-Schlüssel der Beschriftung je Kennzahl — die eine Karte dafür.
 *
 * `InstrumentDrilldown.vue` beschriftet damit die acht Felder, `MetricEditor.vue`
 * setzt denselben Text als Platzhalter in ein leeres Auswahlfeld. Beide führten
 * bis zur Gesamtprüfung eine eigene Tabelle, mit vier deckungsgleichen
 * Einträgen; läuft eine davon weg, heißt dasselbe Feld in der Beschriftung
 * anders als im Platzhalter direkt darunter.
 *
 * Die drei Tabellenspalten borgen sich die Beschriftung vom Spaltenkopf
 * (`table.col*`) — dieselbe Kennzahl soll in Tabelle und Detailbereich nicht
 * verschieden heißen. Die restlichen fünf haben eigene Einträge aus T-07.
 */
export const FIELD_LABEL_KEY: Record<OverrideField, string> = {
  ter: 'table.colTer',
  volatility: 'table.colVola',
  accumulating: 'table.colAccumulating',
  provider: 'overrides.fields.provider',
  replication: 'overrides.fields.replication',
  fund_size: 'overrides.fields.fundSize',
  fund_domicile: 'overrides.fields.fundDomicile',
  fund_currency: 'overrides.fields.fundCurrency',
}
