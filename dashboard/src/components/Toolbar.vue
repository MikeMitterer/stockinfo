<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NInput } from 'naive-ui'

/**
 * Die Leiste über der Assets-Tabelle: ein Papier hinzufügen, alle
 * aktualisieren.
 *
 * Bedienelemente kommen von Naive UI — kein nacktes `input` oder `button`
 * mehr. Die vorherige Fassung stylte ihr Feld selbst; nach dem Wegfall des
 * eigenen Farbsatzes blieb davon nur der Browser-Standard übrig, ein
 * eingelassener grauer Rahmen mitten in der Oberfläche.
 */
const { t } = useI18n()

const emit = defineEmits<{
  (event: 'refresh'): void
  (event: 'add', identifier: string): void
}>()

defineProps<{ refreshing: boolean; busy: boolean }>()

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

    <NButton
      :disabled="refreshing"
      :loading="refreshing"
      @click="emit('refresh')"
    >
      {{ refreshing ? t('toolbar.refreshing') : t('toolbar.refreshAll') }}
    </NButton>
  </div>
</template>

<style scoped lang="scss">
.toolbar {
  @include row(1rem);
  justify-content: space-between;
  flex-wrap: wrap;
  margin-bottom: 1.1rem;

  .add {
    @include row(0.5rem);
    flex: 1;
    min-width: 280px;
  }

  .add__field { flex: 1; }
}
</style>
