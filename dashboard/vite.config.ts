/// <reference types="vitest/config" />
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// Ziel-Backend für den Dev-Proxy (überschreibbar per Env).
const apiTarget = process.env.VITE_DEV_API_TARGET ?? 'http://localhost:8000'

// Nur diese Präfixe sind API-Routen — alles andere serviert das SPA (Hash-Routing).
const apiPrefixes = ['/quote', '/instruments', '/env', '/health', '/refresh']

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: Object.fromEntries(
      apiPrefixes.map((prefix) => [prefix, { target: apiTarget, changeOrigin: true }]),
    ),
  },
  test: { environment: 'jsdom' },
})
