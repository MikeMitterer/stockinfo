<script setup lang="ts">
import { consola } from 'consola'
import { watchEffect } from 'vue'

import type { NavIconName } from '../types'

const KNOWN_ICONS: NavIconName[] = ['assets', 'environment', 'links', 'exchanges', 'themes']

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
    <template v-else-if="name === 'environment'">
      <path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6" />
    </template>
    <template v-else-if="name === 'links'">
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
    </template>
    <template v-else-if="name === 'exchanges'">
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3a14 14 0 0 1 4 9 14 14 0 0 1-4 9 14 14 0 0 1-4-9 14 14 0 0 1 4-9z" />
    </template>
    <template v-else-if="name === 'themes'">
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
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
