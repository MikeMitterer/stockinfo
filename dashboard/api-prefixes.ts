/**
 * Welche Pfad-Präfixe zur API gehören — alles andere bedient das SPA.
 *
 * **Eine eigene Datei, weil es zwei Verbraucher gibt:** `vite.config.ts` baut
 * daraus den Dev-Proxy, `tests/viteProxy.spec.ts` hält sie gegen die Pfade,
 * die App und der veröffentlichte REST-Vertrag benötigen. Der Test kann die Vite-Konfiguration
 * nicht importieren, ohne esbuild in die Testumgebung zu ziehen — und eine
 * abgeschriebene Kopie im Test belegte nur, dass zwei Listen gleich sind.
 *
 * Fehlt hier ein Präfix, liefert der Dev-Server die `index.html` statt der
 * API-Antwort: Die App bekommt HTML, wo sie JSON erwartet. Im Produktionsbau
 * ist der Fehler unsichtbar, weil dort derselbe Server alles ausliefert — er
 * liegt als `_tickets/40-done/T-04-vite-proxy-fehlende-praefixe.md` im Board.
 */
export const apiPrefixes = [
  '/quote',
  '/instruments',
  '/instrument-types',
  '/exchanges',
  '/fx',
  '/analyze',
  '/backups',
  '/env',
  '/health',
  // Die drei Wege des Identitäts-Umzugs und der Diagnose (T-21 Teil 3).
  '/migration',
  '/operational',
  '/ready',
  '/refresh',
  '/sources',
  '/fields',
  '/docs',
  '/redoc',
  '/openapi.json',
]
