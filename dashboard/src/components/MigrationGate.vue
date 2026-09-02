<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NAlert, NButton, NSpin } from 'naive-ui'

import MigrationRejectedList from './MigrationRejectedList.vue'
import type { MigrationPhase } from '../composables/useMigration'
import type { MigrationPreview, MigrationReport, RejectedInstrument } from '../types'

/**
 * Der Pflichtablauf des Identitäts-Umzugs — vorrechnen, bestätigen, berichten.
 *
 * **Warum es diesen Bildschirm gibt:** Der Umzug entfernt Papiere, deren Symbol
 * sich nicht eindeutig in Ticker und Börse zerlegen lässt, samt ihren
 * Kurspunkten. Das ist unwiderruflich. Niemand darf davon erfahren, indem er
 * hinterher etwas vermisst.
 *
 * **Die Komponente kennt die App nicht.** Zustand, Vorschau und Bericht kommen
 * als Props herein, die beiden Handlungen gehen als Events hinaus — kein
 * Composable, kein Store, kein Router. Damit ist sie prüfbar, ohne einen Server
 * zu starten.
 *
 * Sie bleibt trotzdem in dieser App: Der Umzug ist ein Fachthema von StockInfo,
 * kein hausweites Muster. Keine zweite App hat einen Identitäts-Umzug.
 */
const props = defineProps<{
  phase: MigrationPhase
  preview: MigrationPreview | null
  report: MigrationReport | null
  error: string | null
  /** Läuft gerade eine Sicherung? Sie verriegelt beide Handlungen. */
  backingUp?: boolean
  /** Warum die Sicherung scheiterte — fertiger Satz aus dem Katalog. */
  backupError?: string | null
  /** Wurde in dieser Sitzung schon gesichert? */
  backupDone?: boolean
}>()

const emit = defineEmits<{
  (event: 'backup'): void
  (event: 'confirm'): void
  (event: 'retry'): void
  (event: 'continue'): void
}>()

const { t } = useI18n()

/** Die Liste, die gerade gilt: vorher die Vorschau, nachher der Bericht. */
const rejected = computed<RejectedInstrument[]>(() =>
  props.phase === 'pending' || props.phase === 'confirming'
    ? (props.preview?.rejected ?? [])
    : (props.report?.rejected ?? []),
)

/**
 * Läuft gerade ein `POST /migration/confirm`?
 *
 * Beide Vorgänge sperren ihren Knopf — aber sie zeigen **verschiedene**
 * Bildschirme. Das war der Befund aus Runde 35: Solange der Retry über
 * `confirming` lief, sprang die Oberfläche dabei auf die Vorschau zurück.
 */
const busy = computed(() => props.phase === 'confirming' || props.phase === 'restarting')

/**
 * Beide Handlungen sperren einander, solange eine läuft.
 *
 * Nicht aus Vorsicht, sondern weil sie einander widersprechen: Eine Sicherung
 * hält den Stand **vor** dem Umzug fest. Startete der Umzug daneben, wäre
 * hinterher offen, welchen der beiden Stände die Kopie trägt.
 */
const locked = computed(() => busy.value || props.backingUp === true)

/** Der Umzug ist durch, der Betrieb nicht — inklusive laufender Wiederholung. */
const startupFailed = computed(
  () => props.phase === 'startupFailed' || props.phase === 'restarting',
)
</script>

<template>
  <section class="gate">
    <div class="gate__inner">
      <!-- Prüfen und Anlaufen: derselbe leise Zustand, zwei Gründe. -->
      <div v-if="phase === 'checking' || phase === 'starting'" class="gate__waiting">
        <NSpin size="large" />
        <p class="gate__waiting-text">
          {{ phase === 'starting' ? t('migration.starting') : t('migration.checking') }}
        </p>
      </div>

      <template v-else-if="phase === 'databaseDown'">
        <h1 class="gate__title">{{ t('migration.downTitle') }}</h1>
        <NAlert type="error" :bordered="false">{{ error ?? t('migration.downBody') }}</NAlert>
      </template>

      <template v-else-if="startupFailed">
        <h1 class="gate__title">{{ t('migration.startupFailedTitle') }}</h1>
        <NAlert type="warning" :bordered="false" class="gate__alert">
          {{ t('migration.startupFailedBody') }}
        </NAlert>

        <!--
          Der Umzug wird hier **nicht** bestritten. Er ist festgeschrieben, und
          ihn als ungeschehen darzustellen wäre die entgegengesetzte Lüge zu
          der, die dieser Zustand überhaupt abstellt.
        -->
        <template v-if="rejected.length">
          <h2 class="gate__section">{{ t('migration.removedTitle') }}</h2>
          <MigrationRejectedList :items="rejected" />
        </template>

        <div class="gate__actions">
          <NButton type="primary" :loading="busy" @click="emit('retry')">
            {{ busy ? t('migration.retrying') : t('migration.retry') }}
          </NButton>
        </div>
      </template>

      <template v-else-if="phase === 'done'">
        <h1 class="gate__title">{{ t('migration.doneTitle') }}</h1>
        <p class="gate__lead">{{ t('migration.doneLead') }}</p>

        <template v-if="rejected.length">
          <h2 class="gate__section">{{ t('migration.removedTitle') }}</h2>
          <p class="gate__note">{{ t('migration.removedNote') }}</p>
          <MigrationRejectedList :items="rejected" />
        </template>
        <p v-else class="gate__note">{{ t('migration.doneNothingLost') }}</p>

        <!--
          Der Bericht verschwindet nicht von selbst. Wer gerade erfahren hat,
          dass ihm Papiere fehlen, soll die Liste lesen können, solange er
          will — und sie steht danach unter `/migration/report` weiter bereit.
        -->
        <div class="gate__actions">
          <NButton type="primary" @click="emit('continue')">
            {{ t('migration.continue') }}
          </NButton>
        </div>
      </template>

      <!-- Phase 1: vorrechnen, warnen, bestätigen lassen. -->
      <template v-else>
        <h1 class="gate__title">{{ t('migration.title') }}</h1>
        <p class="gate__lead">{{ t('migration.lead') }}</p>

        <dl v-if="preview" class="gate__balance">
          <div class="gate__balance-item">
            <dt>{{ t('migration.balanceMigrating') }}</dt>
            <dd>{{ preview.migrating }}</dd>
          </div>
          <div class="gate__balance-item">
            <dt>{{ t('migration.balanceUnchanged') }}</dt>
            <dd>{{ preview.unchanged }}</dd>
          </div>
          <div class="gate__balance-item gate__balance-item--loss">
            <dt>{{ t('migration.balanceRejected') }}</dt>
            <dd>{{ preview.rejected.length }}</dd>
          </div>
        </dl>

        <NAlert v-if="error" type="error" :bordered="false" class="gate__alert">
          {{ error }}
        </NAlert>

        <template v-if="rejected.length">
          <h2 class="gate__section">{{ t('migration.removedTitle') }}</h2>
          <p class="gate__note">
            {{
              t('migration.lossSummary', {
                quotes: preview?.lost_quotes ?? 0,
                daily: preview?.lost_daily_closes ?? 0,
              })
            }}
          </p>
          <MigrationRejectedList :items="rejected" />
        </template>

        <!--
          Der Backup-Hinweis steht **zwischen** Liste und Knopf, nicht darüber:
          Wer bis hierher gelesen hat, weiß jetzt, was ihn der Umzug kostet —
          und liest den Hinweis mit diesem Wissen.
        -->
        <NAlert type="warning" :bordered="false" class="gate__alert">
          <strong>{{ t('migration.backupTitle') }}</strong>
          <p class="gate__backup-body">{{ t('migration.backupBody') }}</p>
          <!--
            **Die Handlung steht dort, wo der Rat steht.** Zu einer Kopie zu
            raten und den Weg dahin zu sperren war der Befund; ein Verweis auf
            die Einstellungen bliebe einer, denn die sind von hier aus nicht
            erreichbar.
          -->
          <NButton
            class="gate__backup-action"
            :loading="backingUp"
            :disabled="locked"
            @click="emit('backup')"
          >
            {{ backingUp ? t('migration.backingUp') : t('migration.backupNow') }}
          </NButton>
          <p v-if="backupError" class="gate__backup-state gate__backup-state--error">
            {{ backupError }}
          </p>
          <p v-else-if="backupDone" class="gate__backup-state">
            {{ t('migration.backupDone') }}
          </p>
        </NAlert>

        <div class="gate__actions">
          <NButton
            type="primary"
            size="large"
            :loading="busy"
            :disabled="locked"
            @click="emit('confirm')"
          >
            {{ busy ? t('migration.confirming') : t('migration.confirm') }}
          </NButton>
        </div>
      </template>
    </div>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.gate {
  display: flex;
  justify-content: center;
  min-height: 100vh;
  padding: 2rem 1rem 4rem;
  background: $color-bg;

  &__inner {
    width: 100%;
    max-width: 46rem;
  }

  &__waiting {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 6rem 0;
  }

  &__waiting-text {
    margin: 0;
    color: $color-muted;
  }

  &__title {
    margin: 0 0 0.5rem;
  }

  &__section {
    margin: 2rem 0 0.5rem;
  }

  &__lead,
  &__note {
    margin: 0 0 1rem;
    color: $color-muted;
  }

  &__alert {
    margin: 1.5rem 0;
  }

  &__backup-action { margin-top: 0.6rem; }

  &__backup-state {
    margin: 0.5rem 0 0;
    font-size: 0.9rem;

    &--error { color: $color-danger; }
  }

  &__backup-body {
    margin: 0.35rem 0 0;
  }

  &__balance {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin: 1.5rem 0;
  }

  &__balance-item {
    // `min-width: 0` an jedem Flex-Kind mit Text: Ohne es ist die
    // Mindestbreite der längste unteilbare Inhalt und sprengt die Zeile.
    flex: 1 1 8rem;
    min-width: 0;
    padding: 0.75rem 1rem;
    border-radius: $radius;
    background: $color-surface;

    dt {
      font-size: 0.8rem;
      color: $color-muted;
    }

    dd {
      margin: 0.2rem 0 0;
      font-size: 1.5rem;
      font-variant-numeric: tabular-nums;
    }

    &--loss dd {
      color: $color-danger;
    }
  }

  &__actions {
    display: flex;
    justify-content: flex-end;
    margin-top: 1.5rem;
  }
}
</style>
