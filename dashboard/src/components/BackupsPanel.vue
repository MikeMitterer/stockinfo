<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NCheckbox, NModal } from 'naive-ui'

import { useBackups } from '../composables/useBackups'
import type { BackupEntry } from '../types'

/**
 * Die Sicherungen der Instanz.
 *
 * **Auch die unpassenden stehen hier** — mit ihrem Grund, nicht ausgeblendet.
 * Wer eine Datei im Verzeichnis liegen sieht, sie in der Liste aber nicht
 * findet, sucht den Fehler bei sich.
 *
 * **Der Neustart wird vor dem Klick genannt.** Er ist die eigentliche Folge
 * des Wiederherstellens; ihn erst in der Antwort zu erwähnen hieße, ihn nach
 * der Entscheidung mitzuteilen.
 */
const { t, n, locale } = useI18n()
const { data, loading, error, load, create, restore } = useBackups()

/** Die Sicherung, über die gerade entschieden wird. */
const chosen = ref<BackupEntry | null>(null)
/**
 * Ob der Dialog offen ist — **getrennt** von der gewählten Sicherung.
 *
 * Das Ausblenden läuft als Übergang. Würde die Auswahl schon beim Schließen
 * geleert, stünde der Text während der Blende ohne seinen Namen da: „… wird
 * beim nächsten Start eingespielt", ohne zu sagen, was. Die Auswahl fällt
 * deshalb erst, wenn der Dialog wirklich weg ist.
 */
const open = ref<boolean>(false)
/** Das ausdrückliche Übergehen einer abweichenden Quellenlage. */
const force = ref<boolean>(false)

onMounted(load)

function ask(entry: BackupEntry): void {
  chosen.value = entry
  force.value = false
  open.value = true
}

async function confirm(): Promise<void> {
  const entry = chosen.value
  if (!entry) return
  open.value = false
  await restore(entry.name, force.value)
}

/** Bytes in etwas Lesbares — die Größe ist ein Anhaltspunkt, keine Messgröße. */
function humanSize(bytes: number): string {
  return `${n(Math.max(1, Math.round(bytes / 1024)))} kB`
}

/**
 * Ein ISO-Zeitpunkt in der Sprache des Benutzers; roh, wenn er nicht taugt.
 *
 * `toLocaleString` und nicht `d()`: Letzteres braucht ein benanntes Format in
 * `datetimeFormats`, das dieser Katalog nicht führt — es lieferte eine leere
 * Zelle, und die Spalte stand im Browser blank da.
 */
function when(iso: string): string {
  const parsed = new Date(iso)
  return Number.isNaN(parsed.valueOf()) ? iso : parsed.toLocaleString(locale.value)
}
</script>

<template>
  <section class="backups card">
    <h2>{{ t('backups.title') }}</h2>
    <p class="hint">{{ t('backups.hint', { keep: 10 }) }}</p>

    <p v-if="data?.restore_error" class="backups__state backups__state--error">
      {{ t('backups.failed', { reason: data.restore_error }) }}
    </p>
    <p v-else-if="data?.pending_restore" class="backups__state backups__state--pending">
      {{ t('backups.pending', { name: data.pending_restore }) }}
    </p>

    <NButton :loading="loading" type="primary" @click="create">
      {{ t('backups.create') }}
    </NButton>

    <p v-if="error" class="backups__state backups__state--error">{{ error }}</p>

    <div class="backups__scroll">
      <table v-if="data?.backups.length" class="backups__table">
        <thead>
          <tr>
            <th>{{ t('backups.colCreated') }}</th>
            <th>{{ t('backups.colSize') }}</th>
            <th>{{ t('backups.colFit') }}</th>
            <th />
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in data.backups" :key="entry.name">
            <td>{{ when(entry.created_at) }}</td>
            <td class="num">{{ humanSize(entry.size) }}</td>
            <td>
              <span v-if="entry.compatible">{{ t('backups.fits') }}</span>
              <span v-else class="backups__reason">{{ entry.reason }}</span>
            </td>
            <td>
              <NButton size="small" @click="ask(entry)">{{ t('backups.restore') }}</NButton>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="hint">{{ t('backups.empty') }}</p>
    </div>

    <NModal
      :show="open"
      preset="dialog"
      :title="t('backups.confirmTitle')"
      :positive-text="t('backups.confirmYes')"
      :negative-text="t('backups.confirmNo')"
      @positive-click="confirm"
      @negative-click="open = false"
      @close="open = false"
      @after-leave="chosen = null"
    >
      <p>{{ t('backups.confirmBody', { name: chosen?.name }) }}</p>
      <!-- Der Neustart steht **vor** der Entscheidung, nicht in der Antwort. -->
      <p class="backups__restart">{{ t('backups.confirmRestart') }}</p>
      <NCheckbox v-if="chosen && !chosen.compatible" v-model:checked="force">
        {{ t('backups.forceLabel', { reason: chosen.reason }) }}
      </NCheckbox>
    </NModal>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.backups__scroll { overflow-x: auto; }
.backups__table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
.backups__table th, .backups__table td { padding: 0.35rem 0.6rem; text-align: left; white-space: nowrap; }
.num { text-align: right; }
.backups__reason { white-space: normal; }
.backups__state { margin: 0.5rem 0; }
.backups__state--pending { font-weight: 600; }
.backups__state--error { color: $color-danger; }
.backups__restart { font-weight: 600; }
</style>
