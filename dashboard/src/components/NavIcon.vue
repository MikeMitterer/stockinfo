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
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3a14 14 0 0 1 4 9 14 14 0 0 1-4 9 14 14 0 0 1-4-9 14 14 0 0 1 4-9z" />
    </template>
    <template v-else-if="name === 'exchanges'">
      <path d="M3 21h18M5 21V10M19 21V10M9 21v-6h6v6M2 10l10-7 10 7" />
    </template>
    <template v-else-if="name === 'analysis'">
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4.35-4.35M11 8v3l2 2" />
    </template>
    <template v-else-if="name === 'fx'">
      <path d="M4 7h13l-3-3M20 17H7l3 3" />
    </template>
    <template v-else-if="name === 'settings'">
      <path d="M4 6h16M4 12h16M4 18h16" />
      <circle cx="9" cy="6" r="2" fill="currentColor" />
      <circle cx="15" cy="12" r="2" fill="currentColor" />
      <circle cx="7" cy="18" r="2" fill="currentColor" />
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
