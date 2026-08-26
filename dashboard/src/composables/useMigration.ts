import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { ApiError, apiClient } from '../api/client'
import type { MigrationPreview, MigrationReport, ReadinessResponse } from '../types'

/**
 * Die Lage, in der das UI den Dienst vorfindet.
 *
 * **Bewusst dieselben Lagen wie `GateState` im Backend** (`app/migration_guard.py`).
 * Eine eigene Einteilung hier wäre eine zweite Zustandsquelle für dieselbe
 * Frage — und die Erfahrung aus den Runden 30 bis 34 ist genau die: Sobald
 * zwei Stellen den Zustand getrennt zusammensetzen, entstehen Kombinationen,
 * die niemand entworfen hat.
 *
 * `checking` und `confirming` sind die beiden Lagen, die es nur hier gibt —
 * sie beschreiben, was der **Browser** gerade tut, nicht der Server.
 */
export type MigrationPhase =
  | 'checking'
  | 'pending'
  | 'confirming'
  | 'starting'
  | 'restarting'
  | 'done'
  | 'startupFailed'
  | 'databaseDown'
  | 'serving'

/** Der erste Abstand, bis ein anlaufender Betrieb erneut gefragt wird. */
const STARTING_RETRY_MS = 1000

/**
 * Der längste Abstand zwischen zwei Nachfragen.
 *
 * Der Abstand verdoppelt sich bis hierher. Ein hängender Start bleibt
 * serverseitig **dauerhaft** `starting` — ohne Deckel liefe also für immer
 * eine Anfrage pro Sekunde gegen `/ready`, und die zählt jedes Mal die
 * Instrumente in der Datenbank.
 */
const STARTING_RETRY_MAX_MS = 10_000

export interface UseMigration {
  phase: Ref<MigrationPhase>
  preview: Ref<MigrationPreview | null>
  report: Ref<MigrationReport | null>
  error: Ref<string | null>
  check: () => Promise<void>
  confirm: () => Promise<void>
  retry: () => Promise<void>
}

/**
 * Erkennt den Betriebszustand und führt den Pflichtablauf des Umzugs.
 *
 * **Gefragt wird `/ready`, nicht `/migration`.** Der Grund ist der vierte
 * Zustand aus Übergabe 2A: Ein Umzug kann festgeschrieben und der Betrieb
 * trotzdem nicht angelaufen sein. `/migration` sagt dann `pending: false` —
 * das UI zeigte den normalen Dashboard-Betrieb, und dass der
 * Hintergrund-Refresh tot ist, merkte niemand. `/ready` trägt beide Angaben,
 * und `(status, database)` zusammen sind eindeutig.
 *
 * Beide Wege stehen in der Allowlist des Guards und antworten deshalb auch,
 * während alles andere gesperrt ist.
 */
export function useMigration(): UseMigration {
  const phase = ref<MigrationPhase>('checking')
  const preview = ref<MigrationPreview | null>(null)
  const report = ref<MigrationReport | null>(null)
  const error = ref<string | null>(null)

  /** Der Abstand bis zur nächsten Nachfrage; wächst, solange `starting` gilt. */
  let retryDelay = STARTING_RETRY_MS

  /** Übersetzt die Diagnoseantwort in die Lage — **eine** Stelle, ein Mapping. */
  function phaseOf(readiness: ReadinessResponse): MigrationPhase {
    if (readiness.status === 'migration_pending') return 'pending'
    if (readiness.status === 'starting') return 'starting'
    if (readiness.status === 'ok') return 'serving'
    // `degraded`: Die Kennung allein trennt die beiden kaputten Lagen nicht.
    return readiness.database === 'ok' ? 'startupFailed' : 'databaseDown'
  }

  async function check(): Promise<void> {
    try {
      const readiness = await apiClient.probe<ReadinessResponse>('/ready')
      const next = phaseOf(readiness)

      if (next === 'pending') {
        preview.value = await apiClient.get<MigrationPreview>('/migration')
      }
      if (next === 'startupFailed' || next === 'serving') {
        // Der Umzug ist durch. Ob es überhaupt einen gab, sagt der Bericht —
        // ohne ihn stünde nach einem Neuladen nirgends mehr, was entfallen ist.
        report.value = await loadReport()
      }

      phase.value = next
      error.value = null

      if (next === 'starting') {
        /*
         * **Ein hängender Start bleibt `starting`, für immer.** Der Server
         * wechselt von sich aus *nicht* auf `degraded` — dazu müsste der
         * Rückruf ja zurückkehren. Genau deshalb wächst der Abstand: Der
         * Normalfall ist nach Millisekunden durch und wird sofort bemerkt,
         * der Ausnahmefall kostet danach nicht dauerhaft eine Anfrage pro
         * Sekunde.
         */
        window.setTimeout(() => void check(), retryDelay)
        retryDelay = Math.min(retryDelay * 2, STARTING_RETRY_MAX_MS)
      } else {
        retryDelay = STARTING_RETRY_MS
      }
    } catch (err) {
      error.value = messageOf(err)
      phase.value = 'databaseDown'
      consola.error('useMigration.check', err)
    }
  }

  /**
   * Der Umzug, auf ausdrückliche Bestätigung.
   *
   * Sichtbarer Vorgang: `confirming`. Scheitert er aus einem anderen Grund als
   * einem gescheiterten Betriebsstart, steht wieder die Vorschau da — der
   * Umzug hat dann nicht stattgefunden.
   */
  async function confirm(): Promise<void> {
    await runConfirm('confirming', 'pending')
  }

  /**
   * Der Wiederholungsweg — **nur** der Betriebsstart, nicht der Umzug.
   *
   * Derselbe HTTP-Endpunkt wie `confirm`, weil er es im Backend auch ist. Der
   * **sichtbare Vorgang** ist aber ein anderer, und das war der Befund aus
   * Runde 35: Über `confirm()` geführt, sprang die Oberfläche beim
   * Wiederholen auf `confirming` — also zurück auf die Vorschau samt
   * Backup-Warnung und „Migration läuft …". Der Umzug ist da längst
   * festgeschrieben; ihn erneut als bevorstehend zu zeigen, ist dieselbe
   * Unehrlichkeit, die Übergabe 2A im Backend abgestellt hat, nur eine Schicht
   * höher. Bei einem hängenden Start stand sie unbegrenzt.
   *
   * Scheitert der Versuch, bleibt es bei `startupFailed` — zurück auf die
   * Vorschau darf es von hier aus **nie** gehen.
   */
  async function retry(): Promise<void> {
    await runConfirm('restarting', 'startupFailed')
  }

  /**
   * Ein `POST /migration/confirm`, mit der Lage, die dabei sichtbar ist.
   *
   * @param busy - Die Lage während des Aufrufs.
   * @param failed - Die Lage, wenn er aus einem unerwarteten Grund scheitert.
   */
  async function runConfirm(busy: MigrationPhase, failed: MigrationPhase): Promise<void> {
    phase.value = busy
    error.value = null
    try {
      report.value = await apiClient.post<MigrationReport>('/migration/confirm')
      phase.value = 'done'
    } catch (err) {
      if (err instanceof ApiError && err.status === 503) {
        // Der Umzug **ist** festgeschrieben, nur der Betrieb läuft nicht an.
        // Ihn als ungeschehen darzustellen wäre die entgegengesetzte Lüge.
        report.value = await loadReport().catch(() => null)
        phase.value = 'startupFailed'
        return
      }
      if (err instanceof ApiError && err.status === 409) {
        // Ein anderer Tab war schneller, oder der Start läuft gerade. Nicht
        // raten, sondern noch einmal fragen — der Server weiß es.
        await check()
        return
      }
      error.value = messageOf(err)
      phase.value = failed
      consola.error('useMigration.confirm', err)
    }
  }

  return { phase, preview, report, error, check, confirm, retry }
}

/** Der gespeicherte Bericht, oder `null` wenn nie ein Umzug gelaufen ist. */
async function loadReport(): Promise<MigrationReport | null> {
  const stored = await apiClient.get<MigrationReport>('/migration/report')
  return stored.completed ? stored : null
}

/** Die Fehlermeldung, ohne den Aufrufer zwischen Fehlerarten unterscheiden zu lassen. */
function messageOf(err: unknown): string {
  if (err instanceof ApiError) return err.detail
  return err instanceof Error ? err.message : String(err)
}
