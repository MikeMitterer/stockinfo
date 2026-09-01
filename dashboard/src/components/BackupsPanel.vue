<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NCheckbox, NModal } from 'naive-ui'

import { useBackups } from '../composables/useBackups'
import { formatDateTime } from '../utils/datetime'
import type { BackupEntry, BackupReason } from '../types'

/**
 * Die Sicherungen der Instanz.
 *
 * **Auch die unpassenden stehen hier**, mit ihrem Grund: Wer eine Datei im
 * Verzeichnis liegen sieht, sie in der Liste aber nicht findet, sucht den
 * Fehler bei sich. Und **der Neustart wird vor dem Klick genannt** — ihn erst
 * in der Antwort zu erwähnen hieße, ihn nach der Entscheidung mitzuteilen.
 */
const { t, n, locale } = useI18n()
const { data, loading, error, load, create, restore } = useBackups()

/** Die Sicherung, über die gerade entschieden wird. */
const chosen = ref<BackupEntry | null>(null)
/**
 * Ob der Dialog offen ist — **getrennt** von der gewählten Sicherung.
 *
 * Das Ausblenden läuft als Übergang; würde die Auswahl schon beim Schließen
 * geleert, stünde der Text während der Blende ohne seinen Namen da. Sie fällt
 * deshalb erst, wenn der Dialog weg ist.
 */
const open = ref<boolean>(false)
/** Das ausdrückliche Übergehen einer abweichenden Quellenlage. */
const force = ref<boolean>(false)

/**
 * Gesperrt, solange eine bekannt unpassende Sicherung nicht ausdrücklich
 * übergangen wurde: Der Aufruf liefe sonst gegen einen `409`, und der Benutzer
 * erführe aus einer Fehlermeldung, was der Dialog schon wusste.
 */
const blocked = computed<boolean>(() => chosen.value !== null && !chosen.value.compatible && !force.value)

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

/**
 * Der Passungsgrund als Satz — gebildet aus Kennung und Werten.
 *
 * Der Server nennt `code`, `params` und die abweichenden Felder; ein fertiger
 * Text von dort stünde auch in der englischen Oberfläche deutsch da.
 */
function describeReason(reason: BackupReason): string {
  const head = t(`backups.reason.${reason.code}`, reason.params)
  if (reason.differences.length === 0) return head
  const lines = reason.differences.map((item) =>
    t('backups.reason.line', {
      field: item.field === 'packages' ? t('backups.reason.packages') : t(`roles.${item.field}`),
      theirs: item.theirs.join(', ') || t('backups.reason.none'),
      ours: item.ours.join(', ') || t('backups.reason.none'),
    }),
  )
  return `${head} — ${lines.join('; ')}`
}

/** Bytes in etwas Lesbares — die Größe ist ein Anhaltspunkt, keine Messgröße. */
function humanSize(bytes: number): string {
  return `${n(Math.max(1, Math.round(bytes / 1024)))} kB`
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
            <td>{{ formatDateTime(entry.created_at, locale) }}</td>
            <td class="num">{{ humanSize(entry.size) }}</td>
            <td>
              <span v-if="entry.compatible">{{ t('backups.fits') }}</span>
              <span v-else class="backups__reason">{{ describeReason(entry.reason!) }}</span>
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
      :positive-button-props="{ disabled: blocked }"
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
        {{ t('backups.forceLabel', { reason: describeReason(chosen.reason!) }) }}
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
