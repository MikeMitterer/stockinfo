<script setup lang="ts">
import { consola } from 'consola'
import { watchEffect } from 'vue'

import type { NavIconName } from '../types'

const KNOWN_ICONS: NavIconName[] = ['assets', 'exchanges', 'analysis', 'fx', 'settings']

const props = defineProps<{ name: NavIconName }>()

// Unbekannter Name (z.B. nach Umbenennung eines Tabs) — niemals still ignorieren.
watchEffect(() => {
  if (!KNOWN_ICONS.includes(props.name)) {
    consola.warn('NavIcon: unbekannter Icon-Name', { name: props.name })
  }
})
</script>

<template>
  <svg
    class="nav-icon"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <template v-if="name === 'assets'">
      <path d="M3 6h.01M3 12h.01M3 18h.01M8 6h13M8 12h13M8 18h13" />
    </template>
    <template v-else-if="name === 'exchanges'">
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3a14 14 0 0 1 4 9 14 14 0 0 1-4 9 14 14 0 0 1-4-9 14 14 0 0 1 4-9z" />
    </template>
    <template v-else-if="name === 'analysis'">
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4.35-4.35M11 8v3l2 2" />
    </template>
    <template v-else-if="name === 'fx'">
      <path d="M4 7h13l-3-3M20 17H7l3 3" />
    </template>
    <template v-else-if="name === 'settings'">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </template>
    <template v-else>
      <!-- Fallback für unbekannte Namen — sichtbarer Punkt statt leerem SVG -->
      <circle cx="12" cy="12" r="3" />
    </template>
  </svg>
</template>

<style scoped>
.nav-icon { width: 16px; height: 16px; flex-shrink: 0; }
</style>
