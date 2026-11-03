/// <reference types="vitest/config" />
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// Die Liste steht in `api-prefixes.ts` — sie hat zwei Verbraucher, und der
// Test kommt an diese Datei hier nicht heran, ohne esbuild in die
// Testumgebung zu ziehen.
import { apiPrefixes } from './api-prefixes'

// Ziel-Backend für den Dev-Proxy. `make dev-up` setzt VITE_DEV_API_TARGET in
// Procfile.dev aus `.dev-ports.conf.sh`, der einzigen Quelle der Dev-Ports. Der
// Rückfall gilt nur für `npm run dev` ohne `make dev-up`. 127.0.0.1 statt
// localhost: Das Backend lauscht per Vorgabe nur auf IPv4, und Node löst
// localhost womöglich zuerst als ::1 auf.
const apiTarget = process.env.VITE_DEV_API_TARGET ?? 'http://127.0.0.1:8000'

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
    // Rückfall für `npm run dev`; `make dev-up` übergibt DASHBOARD_PORT aus
    // `.dev-ports.conf.sh` mit `--port` (Procfile.dev).
    port: 5173,
    // Das Fundament liegt als Symlink daneben — ohne das 403 auf jede Datei.
    fs: { allow: ['..', '../..'] },
    proxy: Object.fromEntries(
      apiPrefixes.map((prefix) => [prefix, { target: apiTarget, changeOrigin: true }]),
    ),
  },
  test: { environment: 'jsdom', setupFiles: ['tests/setup.ts'] },
})
