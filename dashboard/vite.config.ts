/// <reference types="vitest/config" />
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// Ziel-Backend für den Dev-Proxy (überschreibbar per Env).
const apiTarget = process.env.VITE_DEV_API_TARGET ?? 'http://localhost:8000'

// Nur diese Präfixe sind API-Routen — alles andere serviert das SPA (Hash-Routing).
const apiPrefixes = [
  '/quote',
  '/instruments',
  '/exchanges',
  '/fx',
  '/analyze',
  '/env',
  '/health',
  '/refresh',
  '/docs',
  '/redoc',
  '/openapi.json',
]

export default defineConfig({
  plugins: [vue()],

  /*
   * Das Fundament liegt als `file:`-Abhängigkeit vor — npm legt dafür einen
   * Symlink, Vite sieht also einen Pfad außerhalb des Projekts. Zwei Angaben
   * sind deshalb nötig:
   *
   * `exclude` verhindert das Vorbündeln. Das Paket liefert Quellen aus, und
   * esbuild kann mit `.vue` nichts anfangen — ohne diese Zeile bricht der
   * Dev-Server beim ersten Import ab.
   *
   * `fs.allow` erlaubt dem Dev-Server, Dateien jenseits des Projektordners
   * auszuliefern. Ohne sie antwortet er auf jede Datei des Pakets mit 403.
   *
   * Beides entfällt, sobald das Paket aus der Registry kommt.
   */
  optimizeDeps: {
    exclude: ['@mmit/ux-foundation'],
  },

  css: {
    preprocessorOptions: {
      scss: {
        /*
         * Breakpoint-Mixins und der Farb-Helfer stehen in jeder Komponente
         * zur Verfügung, ohne dass jede SFC dieselbe `@use`-Zeile trägt.
         * Die Datei erzeugt selbst kein CSS — sonst läge sie einmal je
         * Komponente im Bündel.
         */
        additionalData: '@use "@mmit/ux-foundation/styles/shared" as *;\n',
      },
    },
  },

  server: {
    port: 5173,
    // Das Fundament liegt als Symlink daneben — ohne das 403 auf jede Datei.
    fs: { allow: ['..', '../..'] },
    proxy: Object.fromEntries(
      apiPrefixes.map((prefix) => [prefix, { target: apiTarget, changeOrigin: true }]),
    ),
  },
  test: { environment: 'jsdom', setupFiles: ['tests/setup.ts'] },
})
