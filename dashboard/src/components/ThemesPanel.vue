<script setup lang="ts">
/**
 * Die Theme-Auswahl in den Einstellungen.
 *
 * Kacheln und Vorschau liefert das Fundament (`UxThemePicker`) — hier bleibt
 * nur, wie die Paletten in dieser App heißen.
 */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { THEME_IDS, UxThemePicker, type ThemeId } from '@mmit/ux-foundation'

import { useTheme } from '../composables/useTheme'

const { current, setTheme } = useTheme()
const { t } = useI18n()

/*
 * Namen aus dem Katalog, mit der Kennung als Rückfall: Kommt im Fundament eine
 * Palette dazu, steht sie sofort zur Wahl, statt als leere Kachel zu erscheinen
 * — der Katalog zieht dann beim nächsten Durchgang nach.
 */
const labels = computed(
  () =>
    Object.fromEntries(
      THEME_IDS.map((id) => [id, t(`themes.names.${id}`, id)]),
    ) as Record<ThemeId, string>,
)
</script>

<template>
  <section class="themes card">
    <h2>{{ t('themes.title') }}</h2>
    <p class="hint">{{ t('themes.hint') }}</p>

    <UxThemePicker
      :current="current"
      :labels="labels"
      :active-label="t('themes.active')"
      @select="setTheme"
    />
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.hint {
  @include muted(0.82rem);
  margin: 0 0 1rem;
}
</style>
