<script setup lang="ts">
import { API_BASE_URL } from '../config'

interface ApiLink {
  label: string
  url: string
}

const links: ApiLink[] = [
  { label: 'API-Wurzel', url: `${API_BASE_URL}/` },
  { label: 'Swagger-UI (/docs)', url: `${API_BASE_URL}/docs` },
  { label: 'ReDoc (/redoc)', url: `${API_BASE_URL}/redoc` },
  { label: 'OpenAPI (JSON)', url: `${API_BASE_URL}/openapi.json` },
  { label: 'Health', url: `${API_BASE_URL}/health` },
]
</script>

<template>
  <section class="links">
    <h2>API &amp; Links</h2>
    <p class="base">Basis: <code>{{ API_BASE_URL }}</code></p>
    <ul>
      <li v-for="link in links" :key="link.url">
        <a :href="link.url" target="_blank" rel="noopener">{{ link.label }} ↗</a>
      </li>
    </ul>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.links {
  background: $color-surface;
  border-radius: $radius;
  padding: 1rem;
  margin: 1rem 0;

  .base { color: $color-muted; margin: 0.25rem 0 0.75rem; }
  code { color: $color-text; }
  ul {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem 1.25rem;
  }
  a {
    color: $color-accent;
    text-decoration: none;
    &:hover { text-decoration: underline; }
  }
}
</style>
