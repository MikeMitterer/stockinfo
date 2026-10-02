// Browser-Gesamtprüfung von StockInfo — `make visual-check`.
//
// Startet eine eigene Instanz mit temporärer Datenbank und den Offline-Daten
// aus `examples/`, klickt die Hauptwege im sichtbaren Chrome durch und prüft
// Inhalte, nicht Pixel. Jeder Weg nennt die Konsolen- und HTTP-Fehler, die er
// erwartet; jeder andere lässt ihn scheitern. Ergebnis: eine Zeile je Weg,
// `report.md` und Screenshots unter `.tmp/visual-check/<Zeitstempel>/`.
//
// Umgebungsvariablen: HEADLESS=1 (unsichtbar), ONLY=W2,W3 (Auswahl),
// CHROME=<Pfad> (anderes Chrome).
import { spawn, spawnSync } from 'node:child_process'
import { cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs'
import { createServer } from 'node:net'
import { tmpdir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import { chromium } from 'playwright-core'

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..')
const STAMP = new Date().toISOString().replace(/[:.]/g, '-')
const OUT = join(ROOT, '.tmp', 'visual-check', STAMP)
const CHROME = process.env.CHROME ?? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const ONLY = process.env.ONLY ? new Set(process.env.ONLY.split(',')) : null
const VIEWPORT = { width: 1512, height: 860 }

class CheckFailed extends Error {}

/** Bricht den laufenden Weg mit einer lesbaren Begründung ab. */
function check(condition, message) {
  if (!condition) throw new CheckFailed(message)
}

// ─── Instanz ──────────────────────────────────────────────────────────────

function freePort() {
  return new Promise((done) => {
    const server = createServer()
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address()
      server.close(() => done(port))
    })
  })
}

/** Ein frisches Datenverzeichnis mit Offline-Profil — nie das Projekt-`data/`. */
function offlineDataDir() {
  const directory = mkdtempSync(join(tmpdir(), 'stockinfo-visual-'))
  check(!resolve(directory).startsWith(join(ROOT, 'data')), `${directory} liegt im Projekt-data/`)
  const assets = join(directory, 'assets-standalone.yaml')
  cpSync(join(ROOT, 'examples', 'assets-standalone.yaml'), assets)
  const sources = readFileSync(join(ROOT, 'examples', 'sources-standalone.yaml'), 'utf8')
  check(sources.includes('/data/assets-standalone.yaml'), 'Quellenvorlage nennt den erwarteten Pfad nicht mehr')
  // `replaceAll`: Der Pfad steht auch im Kommentarkopf der Vorlage.
  writeFileSync(join(directory, 'sources.yaml'), sources.replaceAll('/data/assets-standalone.yaml', assets))
  return directory
}

/** Baut das Dashboard einmal in den Ausgabeordner. */
function buildDashboard() {
  const dist = join(OUT, 'dist')
  const result = spawnSync('npx', ['vite', 'build', '--outDir', dist, '--emptyOutDir'], {
    cwd: join(ROOT, 'dashboard'),
    stdio: 'inherit',
  })
  check(result.status === 0, 'Dashboard-Build gescheitert')
  return dist
}

/**
 * Startet `uvicorn` auf eigenem Port; nur dieser Prozess wird später beendet.
 *
 * Wartet auf `/health`, nicht auf `/ready`: Mit ausstehendem Umzug bleibt
 * `/ready` absichtlich `503`, und genau diesen Zustand prüft der
 * Migrationsweg.
 */
async function startServer(dataDir, dist) {
  const port = await freePort()
  const log = join(OUT, `server-${port}.log`)
  const child = spawn(join(ROOT, '.venv', 'bin', 'uvicorn'), ['app.main:app', '--host', '127.0.0.1', '--port', String(port)], {
    cwd: ROOT,
    env: { ...process.env, DATABASE_PATH: join(dataDir, 'stockinfo.db'), STATIC_DIR: dist },
    stdio: ['ignore', 'pipe', 'pipe'],
  })
  const lines = []
  child.stdout.on('data', (chunk) => lines.push(String(chunk)))
  child.stderr.on('data', (chunk) => lines.push(String(chunk)))
  child.on('exit', () => writeFileSync(log, lines.join('')))
  const base = `http://127.0.0.1:${port}`
  for (let attempt = 0; attempt < 60; attempt += 1) {
    try {
      if ((await fetch(`${base}/health`)).ok) return { base, child, lines }
    } catch {
      // Server startet noch.
    }
    await new Promise((done) => setTimeout(done, 500))
  }
  child.kill('SIGTERM')
  throw new CheckFailed(`Server auf ${port} kam nicht hoch`)
}

function stopServer(server) {
  return new Promise((done) => {
    if (server.child.exitCode !== null) return done()
    server.child.once('exit', () => done())
    server.child.kill('SIGTERM')
  })
}

async function api(server, path, options = {}) {
  const response = await fetch(server.base + path, options)
  const body = response.headers.get('content-type')?.includes('json') ? await response.json() : await response.text()
  return { status: response.status, body }
}

// ─── Wege ─────────────────────────────────────────────────────────────────

const results = []

/**
 * Führt einen Weg aus und wertet erwartete und unerwartete Fehler aus.
 *
 * `expect.http`: Liste von `{ status, url }` (Teilstring) — muss jeweils
 * mindestens einmal kommen. `expect.console`: Liste regulärer Ausdrücke für
 * Konsolenfehler, die kommen müssen. Alles andere ab 400 und jeder andere
 * Konsolenfehler lässt den Weg scheitern.
 */
async function way(id, title, expect, body) {
  if (ONLY && !ONLY.has(id)) return
  const context = await browser.newContext({ viewport: VIEWPORT, colorScheme: 'dark', locale: 'en-US' })
  const httpErrors = []
  const consoleErrors = []
  context.on('response', (response) => {
    if (response.status() >= 400) httpErrors.push({ status: response.status(), url: response.url() })
  })
  context.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text())
  })
  const shots = []
  const ctx = {
    context,
    async page(path = '/') {
      const page = await context.newPage()
      await page.goto(state.server.base + path)
      await settle(page)
      return page
    },
    async shot(page, name) {
      await page.mouse.move(2, 2)
      await page.waitForTimeout(250)
      const file = `${id}-${name}.png`
      await page.screenshot({ path: join(OUT, file), fullPage: false })
      shots.push(file)
    },
  }
  const started = Date.now()
  let failure = null
  try {
    await body(ctx)
    const wantedHttp = expect.http ?? []
    const wantedConsole = expect.console ?? []
    for (const wanted of wantedHttp) {
      check(httpErrors.some((seen) => seen.status === wanted.status && seen.url.includes(wanted.url)),
        `erwartete Antwort ${wanted.status} auf ${wanted.url} kam nicht`)
    }
    for (const pattern of wantedConsole) {
      check(consoleErrors.some((text) => pattern.test(text)), `erwarteter Konsolenfehler ${pattern} kam nicht`)
    }
    const unexpectedHttp = httpErrors.filter((seen) => !wantedHttp.some(
      (wanted) => seen.status === wanted.status && seen.url.includes(wanted.url)))
    check(unexpectedHttp.length === 0, `unerwartete Antworten: ${JSON.stringify(unexpectedHttp)}`)
    const unexpectedConsole = consoleErrors.filter((text) => !wantedConsole.some((pattern) => pattern.test(text))
      // Der Browser meldet jede Antwort ab 400 zusätzlich als Konsolenfehler;
      // die HTTP-Prüfung oben hat sie schon eingeordnet.
      && !/Failed to load resource: the server responded with a status of/.test(text))
    check(unexpectedConsole.length === 0, `unerwartete Konsolenfehler: ${JSON.stringify(unexpectedConsole)}`)
  } catch (error) {
    failure = error instanceof CheckFailed ? error.message : `${error.name}: ${error.message.split('\n')[0]}`
  } finally {
    await context.close()
  }
  const seconds = ((Date.now() - started) / 1000).toFixed(1)
  results.push({ id, title, ok: !failure, failure, seconds, shots })
  console.log(`${failure ? 'FAIL' : 'OK  '} ${id} ${title} (${seconds} s)${failure ? ` — ${failure}` : ''}`)
}

async function settle(page) {
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(600)
}

function row(page, text) {
  return page.locator('tbody tr', { hasText: text }).first()
}

// Die fünf Papiere der Offline-Vorlage, mit der Eingabe, über die sie
// aufgenommen werden.
const PAPERS = [
  { input: 'IE00B4L5Y983', symbol: 'EUNL.DE', kind: 'listed', type: 'etf' },
  { input: 'US0378331005', symbol: 'APC.DE', kind: 'listed', type: 'stock' },
  { input: 'BTC-EUR', symbol: 'BTC-EUR', kind: 'pair', type: 'crypto' },
  { input: 'DE0001102531', symbol: 'DE0001102531', kind: 'isin_only', type: 'bond' },
  { input: 'DE0009848119', symbol: 'DE0009848119', kind: 'isin_only', type: 'fund' },
]

// ─── Ablauf ───────────────────────────────────────────────────────────────

mkdirSync(OUT, { recursive: true })
console.log(`Ausgabe: ${OUT}`)
const dist = buildDashboard()
const state = { dataDir: offlineDataDir(), server: null }
state.server = await startServer(state.dataDir, dist)
const browser = await chromium.launch({
  executablePath: CHROME,
  headless: process.env.HEADLESS === '1',
  args: ['--no-first-run'],
})

try {
  await way('W1', 'Start', {}, async (ctx) => {
    check((await api(state.server, '/health')).status === 200, '/health nicht 200')
    check((await api(state.server, '/ready')).status === 200, '/ready nicht 200')
    const page = await ctx.page('/')
    check(await page.locator('tbody tr').count() === 0, 'Übersicht ist nicht leer')
    await ctx.shot(page, 'empty')
  })

  await way('W2', 'Aufnahme', {
    http: [{ status: 400, url: '/instruments/intake' }],
    console: [/intake|add/i],
  }, async (ctx) => {
    const page = await ctx.page('/')
    const input = page.getByPlaceholder('ISIN or symbol')
    for (const paper of PAPERS) {
      await input.fill(paper.input)
      await page.getByRole('button', { name: 'Add', exact: true }).click()
      await page.waitForTimeout(1200)
      await settle(page)
      check(await row(page, paper.symbol).count() === 1, `${paper.input}: keine Zeile ${paper.symbol}`)
    }
    const listed = (await api(state.server, '/instruments')).body
    for (const paper of PAPERS) {
      const stored = listed.find((item) => item.symbol === paper.symbol)
      check(stored?.identity.kind === paper.kind, `${paper.symbol}: Form ${stored?.identity.kind} statt ${paper.kind}`)
      check(stored?.type === paper.type, `${paper.symbol}: Gattung ${stored?.type} statt ${paper.type}`)
    }
    await ctx.shot(page, 'all-added')
    await input.fill('XX0000000000')
    await page.getByRole('button', { name: 'Add', exact: true }).click()
    await page.waitForTimeout(1500)
    const message = await page.locator('body').innerText()
    check(message.includes('None of the configured sources found a security for XX0000000000'),
      'keine verständliche Meldung für ein unbekanntes Papier')
    await ctx.shot(page, 'unknown')
    check(await page.locator('tbody tr').count() === PAPERS.length, 'Fehlversuch hat die Übersicht verändert')
  })

  await way('W3', 'Übersicht', {}, async (ctx) => {
    const page = await ctx.page('/')
    check(await page.locator('tbody tr').count() === PAPERS.length, 'nicht fünf Zeilen')
    check((await page.locator('footer').innerText()).includes(`${PAPERS.length} instruments`), 'Fußzeile nennt die Anzahl nicht')
    const first = async () => (await page.locator('tbody tr').first().innerText()).trim().split(/\s+/)[0]
    // Links in den Kopf klicken: In der Mitte sitzt das Fragezeichen, das
    // absichtlich nicht sortiert.
    const header = page.locator('th.sortable', { hasText: 'Symbol' })
    await header.click({ position: { x: 6, y: 8 } })
    await settle(page)
    check(await header.getAttribute('aria-sort') === 'ascending', 'Symbolspalte nicht aufsteigend sortiert')
    const ascending = await first()
    await header.click({ position: { x: 6, y: 8 } })
    await settle(page)
    check(await header.getAttribute('aria-sort') === 'descending', 'Symbolspalte nicht absteigend sortiert')
    const descending = await first()
    check(ascending === 'APC.DE' && descending === 'EUNL.DE',
      `Reihenfolge nach Symbol stimmt nicht (auf ${ascending}, ab ${descending})`)
    await ctx.shot(page, 'sorted')
  })
} finally {
  await browser.close()
  await stopServer(state.server)
}

const failed = results.filter((result) => !result.ok)
const lines = [
  `# StockInfo · Browser-Gesamtprüfung ${STAMP}`,
  '',
  `${results.length - failed.length} von ${results.length} Wegen bestanden.`,
  '',
  '| Weg | Titel | Ergebnis | Dauer | Bilder |',
  '|---|---|---|---|---|',
  ...results.map((result) => `| ${result.id} | ${result.title} | ${result.ok ? 'bestanden' : `**nicht bestanden:** ${result.failure}`} | ${result.seconds} s | ${result.shots.map((shot) => `[${shot}](${shot})`).join(' ')} |`),
]
writeFileSync(join(OUT, 'report.md'), lines.join('\n') + '\n')
console.log(`\n${results.length - failed.length}/${results.length} bestanden — ${join(OUT, 'report.md')}`)
if (!existsSync(join(OUT, 'report.md')) || failed.length > 0) process.exit(1)
