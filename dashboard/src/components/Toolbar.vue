<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NInput } from 'naive-ui'

/**
 * Die Leiste über der Assets-Tabelle: ein Papier hinzufügen.
 *
 * „Alle aktualisieren" stand hier einmal rechts daneben und ist in die
 * Kopfzeile gezogen — dorthin gehört die eine Handlung, die überall gilt, und
 * das obere rechte Eck des Inhalts bleibt damit frei für Meldungen.
 *
 * Bedienelemente kommen von Naive UI — kein nacktes `input` oder `button`
 * mehr. Die vorherige Fassung stylte ihr Feld selbst; nach dem Wegfall des
 * eigenen Farbsatzes blieb davon nur der Browser-Standard übrig, ein
 * eingelassener grauer Rahmen mitten in der Oberfläche.
 */
const { t } = useI18n()

const emit = defineEmits<{
  (event: 'add', identifier: string): void
}>()

defineProps<{ busy: boolean }>()

const identifier = ref<string>('')

function submit(): void {
  const value = identifier.value.trim()
  if (value) {
    emit('add', value)
    identifier.value = ''
  }
}
</script>

<template>
  <div class="toolbar">
    <form class="add" @submit.prevent="submit">
      <NInput
        v-model:value="identifier"
        class="add__field"
        :placeholder="t('toolbar.placeholder')"
        clearable
        @keyup.enter="submit"
      />
      <NButton
        type="primary"
        attr-type="submit"
        :disabled="busy"
        :loading="busy"
      >
        {{ t('toolbar.add') }}
      </NButton>
    </form>
  </div>
</template>

<style scoped lang="scss">
.toolbar {
  margin-bottom: 1.1rem;

  /*
   * Feld und Knopf gehören zusammen und stehen links. Vorher zog sich die
   * Zeile über die volle Breite, weil rechts noch „Alle aktualisieren" saß —
   * ohne den Knopf bliebe sonst ein Eingabefeld von 1200 px für eine ISIN.
   */
  .add {
    @include row(0.5rem);
    max-width: 34rem;
  }

  .add__field { flex: 1; }
}
</style>
