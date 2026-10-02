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
import { DatabaseSync } from 'node:sqlite'
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

/** Zählt in der Datenbank der Instanz — nur lesend. */
function readOnlyCount(dataDir, sql) {
  const database = new DatabaseSync(join(dataDir, 'stockinfo.db'), { readOnly: true })
  try {
    return Number(database.prepare(sql).get().n)
  } finally {
    database.close()
  }
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
    // Bei Playwright-Fehlern die Zeile mit dem gesuchten Element mitnehmen —
    // die erste Zeile sagt nur „Timeout“.
    const lines = String(error.message).split('\n')
    const target = lines.find((line) => line.includes('waiting for'))?.trim()
    failure = error instanceof CheckFailed ? error.message : `${error.name}: ${lines[0]}${target ? ` (${target})` : ''}`
    // Was im Moment des Scheiterns zu sehen war — sonst bleibt nur der Text.
    for (const [index, open] of context.pages().entries()) {
      const file = `${id}-failure-${index + 1}.png`
      await open.screenshot({ path: join(OUT, file) }).then(() => shots.push(file), () => {})
    }
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

/** Das Papier aus `GET /instruments` — per Symbol oder ISIN (steht in `identity`). */
async function paper(key) {
  const list = (await api(state.server, '/instruments')).body
  return list.find((item) => item.symbol === key || item.identity?.isin === key)
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

  await way('W4', 'Detailbereich', {}, async (ctx) => {
    const page = await ctx.page('/')
    const expectations = {
      'EUNL.DE': ['iShares', 'Ireland', '0.2 %', 'yaml-file'],
      'BTC-EUR': [],
      DE0001102531: [],
      DE0009848119: ['Fund provider'],
    }
    for (const [key, texts] of Object.entries(expectations)) {
      await row(page, key).locator('td.caret-col button').click()
      await settle(page)
      const detail = page.locator('.drilldown').first()
      check(await detail.isVisible(), `${key}: Detailbereich öffnet nicht`)
      const text = await detail.innerText()
      for (const expected of texts) check(text.includes(expected), `${key}: „${expected}“ fehlt im Detailbereich`)
      if (text.includes('Source as of')) {
        check(/[A-Z][a-z]{2} \d{1,2}, \d{4}/.test(text), `${key}: Datum nicht im englischen Format`)
      }
      await ctx.shot(page, key.replace(/[^A-Za-z0-9]/g, ''))
      await row(page, key).locator('td.caret-col button').click()
      await settle(page)
    }
  })

  await way('W5', 'Kursverlauf', {}, async (ctx) => {
    const page = await ctx.page('/')
    await row(page, 'DE0001102531').locator('td.name button').first().click()
    await settle(page)
    const dock = page.locator('.chart-dock')
    check(await dock.isVisible(), 'Kursverlauf öffnet nicht')
    // Der Verlauf der Vorlage endet am 2026-08-27; „Max“ zeigt ihn sicher.
    await dock.getByText('Max', { exact: true }).first().click()
    await settle(page)
    check(await dock.locator('canvas').count() > 0, 'kein Chart gezeichnet')
    const daily = (await api(state.server, '/quote/DE0001102531/daily?period=max')).body
    check(Array.isArray(daily) && daily.length === 3 && daily.at(-1).close === 99.42,
      `Tagesreihe der Anleihe stimmt nicht: ${JSON.stringify(daily).slice(0, 120)}`)
    await ctx.shot(page, 'bond-max')
  })

  await way('W6', 'Manuelle Eingabe', {}, async (ctx) => {
    const fund = 'DE0009848119'
    const open = async () => {
      const page = await ctx.page('/')
      await row(page, fund).locator('td.caret-col button').click()
      await settle(page)
      return page
    }
    const field = (page, label) => page.locator('.drilldown dl > div', { hasText: label })
    let page = await open()
    await field(page, 'Fund provider').locator('.detail-editor__text').click()
    await page.keyboard.type('Sichtpruefung KVG')
    await page.keyboard.press('Enter')
    await settle(page)
    await page.close()
    page = await open()
    check((await field(page, 'Fund provider').innerText()).includes('Sichtpruefung KVG'),
      'manueller Anbieter übersteht das Neuladen nicht')
    const stored = await paper(fund)
    check(stored?.details?.provider?.origin === 'manual', 'API meldet den Anbieter nicht als manuell')
    await ctx.shot(page, 'entered')
    await field(page, 'Fund provider').getByTitle('Remove your entry').click()
    await settle(page)
    const cleared = await paper(fund)
    check(cleared?.details?.provider?.manual_value === null, 'Eingabe lässt sich nicht entfernen')
    await ctx.shot(page, 'removed')

    // Zahl: die TER des Fonds, die die Datei nicht liefert.
    // Die Zahl ist selbst der Knopf; „Edit …“ steht in seinem `title`.
    await field(page, 'Total expense ratio').getByTitle(/^Edit/).click()
    await page.keyboard.type('0.65')
    await page.keyboard.press('Enter')
    await settle(page)
    check((await paper(fund))?.details?.ter?.manual_value === 0.65, 'manuelle TER nicht gespeichert')
    await ctx.shot(page, 'number')
    await field(page, 'Total expense ratio').getByTitle('Remove your entry').click()
    await settle(page)
    check((await paper(fund))?.details?.ter?.manual_value === null, 'manuelle TER lässt sich nicht entfernen')
    // Ein Ja/Nein-Feld gibt es im Offline-Profil nicht: Welche Felder es gibt,
    // deklariert die Quelle, und das YAML-Plugin kennt keines.
  })

  await way('W7', 'Aktualisieren', {}, async (ctx) => {
    const fetchedAt = async (key) => (await paper(key))?.latest_fetched_at
    const page = await ctx.page('/')
    const before = await fetchedAt('EUNL.DE')
    await page.waitForTimeout(1100)
    await row(page, 'EUNL.DE').getByTitle('Refresh').click()
    await settle(page)
    const afterOne = await fetchedAt('EUNL.DE')
    check(afterOne > before, `Zeilen-Refresh: Abrufzeitpunkt rückt nicht vor (${before} → ${afterOne})`)
    const othersBefore = await fetchedAt('APC.DE')
    await page.waitForTimeout(1100)
    await page.getByRole('button', { name: 'Refresh all' }).click()
    await page.waitForTimeout(1500)
    await settle(page)
    const othersAfter = await fetchedAt('APC.DE')
    check(othersAfter > othersBefore, `„Alle aktualisieren“: Abrufzeitpunkt rückt nicht vor (${othersBefore} → ${othersAfter})`)
    await ctx.shot(page, 'refreshed')
  })

  await way('W8', 'Löschen', {}, async (ctx) => {
    const page = await ctx.page('/')
    const target = 'APC.DE'
    await row(page, target).getByTitle('Delete').click()
    await page.waitForTimeout(400)
    const dialog = page.getByRole('dialog')
    check((await dialog.innerText()).includes('price point'), 'Löschdialog nennt die Kurspunkte nicht')
    await ctx.shot(page, 'dialog')
    await dialog.getByRole('button', { name: 'Cancel' }).click()
    await settle(page)
    check(await row(page, target).count() === 1, 'Abbrechen hat gelöscht')
    await row(page, target).getByTitle('Delete').click()
    await page.waitForTimeout(400)
    await page.getByRole('dialog').getByRole('button', { name: 'Delete' }).click()
    await settle(page)
    check(await row(page, target).count() === 0, 'Bestätigen hat nicht gelöscht')
    const left = (await api(state.server, '/instruments')).body
    check(left.length === PAPERS.length - 1 && !left.some((item) => item.symbol === target),
      'API zeigt das gelöschte Papier noch')
    // Nur lesend in die Datei sehen: Ein Abruf über die API legte das
    // gelöschte Papier auf Anfrage neu an (`ensure_instrument`).
    const orphans = readOnlyCount(state.dataDir,
      'SELECT COUNT(*) AS n FROM quotes WHERE instrument_id NOT IN (SELECT id FROM instruments)')
    check(orphans === 0, `${orphans} Kurspunkte ohne Papier übrig`)
    await ctx.shot(page, 'deleted')
  })

  await way('W9', 'Börsen', {}, async (ctx) => {
    const page = await ctx.page('/#/exchanges')
    const rows = page.locator('tbody tr')
    // Das Offline-Profil deckt nur XETR ab; erst mit den nicht abgedeckten
    // Börsen gibt es eine Liste, die der Filter verkleinern kann.
    check(await rows.count() === 1, `Offline-Profil sollte genau eine Börse abdecken (${await rows.count()})`)
    check((await page.locator('main').innerText()).includes('Trading venues'), 'Überschrift fehlt')
    await page.getByRole('switch', { name: 'Show exchanges not covered' }).click()
    await settle(page)
    const all = await rows.count()
    check(all > 1, 'nicht abgedeckte Börsen erscheinen nicht')
    await page.getByPlaceholder('Search MIC, venue or source').fill('XETR')
    await settle(page)
    const filtered = await rows.count()
    check(filtered > 0 && filtered < all, `Filter wirkt nicht (${all} → ${filtered})`)
    check((await rows.first().innerText()).includes('XETR'), 'gefilterte Zeile nennt XETR nicht')
    await ctx.shot(page, 'filtered')
  })

  await way('W10', 'Analyse', {}, async (ctx) => {
    const page = await ctx.page('/#/analysis')
    await page.getByPlaceholder('ISIN or symbol (e.g. EUNL.DE)').fill('IE00B4L5Y983')
    await page.getByRole('button', { name: 'Analyze' }).click()
    await page.waitForTimeout(1500)
    await settle(page)
    const text = await page.locator('main').innerText()
    check(text.includes('answered'), 'keine Quelle mit Status „answered“')
    check(text.includes('yaml-file'), 'gemessene Quelle yaml-file fehlt')
    await ctx.shot(page, 'measured')
  })

  await way('W11', 'Devisen', {
    http: [{ status: 404, url: '/fx' }],
    console: [/fx|rate/i],
  }, async (ctx) => {
    const page = await ctx.page('/#/fx')
    // Per Tastatur wählen: Die Liste zeichnet nur sichtbare Einträge, und
    // geschlossene Menüs bleiben im DOM. Pfeiltaste bis zur Währung, dann Enter.
    const choose = async (label, currency) => {
      await page.getByLabel(label, { exact: true }).click()
      await page.waitForTimeout(200)
      const pending = page.locator('.n-base-select-menu:visible .n-base-select-option--pending')
      const atCurrency = async () => (await pending.count()) > 0 && (await pending.first().innerText()).trim() === currency
      // Erst abwärts, dann aufwärts: Die Liste springt am Ende nicht zurück.
      for (const key of ['ArrowDown', 'ArrowUp']) {
        for (let step = 0; step < 120 && !(await atCurrency()); step += 1) await page.keyboard.press(key)
        if (await atCurrency()) break
      }
      check((await pending.first().innerText()).trim() === currency, `${currency} nicht in der Auswahl ${label}`)
      await page.keyboard.press('Enter')
      await page.waitForTimeout(300)
    }
    await choose('Base', 'CAD')
    await choose('Quote', 'EUR')
    await page.getByRole('button', { name: 'Convert' }).click()
    await settle(page)
    const text = await page.locator('main').innerText()
    // Die Oberfläche zeigt drei Nachkommastellen; den genauen Wert sagt die API.
    check(text.includes('1 CAD = 0.641 EUR'), 'CAD→EUR zeigt nicht 0,641')
    check(text.includes('yaml-file'), 'Quelle des Kurses fehlt')
    const rate = (await api(state.server, '/fx?base=CAD&quote=EUR')).body
    check(rate.rate === 0.6412, `API liefert ${rate.rate} statt 0,6412`)
    await ctx.shot(page, 'cad-eur')
    const shownTime = text
    // Ein Paar, das die Offline-Datei nicht führt.
    await choose('Base', 'EUR')
    await choose('Quote', 'USD')
    await page.getByRole('button', { name: 'Convert' }).click()
    await page.waitForTimeout(1200)
    check((await page.locator('body').innerText()).includes('None of the configured sources carries the rate EUR/USD'),
      'keine verständliche Meldung für ein unbekanntes Paar')
    await ctx.shot(page, 'unknown-pair')
    // Zuletzt, damit die Schritte davor laufen: Die Datei pflegt den Kurs mit
    // `as_of: 2026-08-27T17:30+02:00`. Gezeigt werden muss dieser Zeitpunkt,
    // nicht der des Abrufs.
    check(rate.quote_time.startsWith('2026-08-27') && shownTime.includes('Aug 27, 2026'),
      `Kurszeitpunkt ist der Abruf (${rate.quote_time}), nicht as_of der Quelle — App-Fehler, Folgeticket`)
  })

  await way('W12', 'Einstellungen', {}, async (ctx) => {
    let page = await ctx.page('/#/settings?tab=appearance')
    const theme = page.locator('.ux-themepicker__tile', { hasText: 'Paper' })
    await theme.click()
    await settle(page)
    const chosen = await page.locator('html').getAttribute('data-theme')
    await page.reload()
    await settle(page)
    check(await page.locator('.ux-themepicker__tile', { hasText: 'Paper' }).getAttribute('aria-pressed') === 'true',
      'gewähltes Thema übersteht das Neuladen nicht')
    check(await page.locator('html').getAttribute('data-theme') === chosen, 'Thema nach Neuladen anders')
    await ctx.shot(page, 'theme')
    await page.locator('.ux-themepicker__tile', { hasText: 'MangoLila' }).click()
    await settle(page)

    await page.goto(`${state.server.base}/#/settings?tab=language`)
    await settle(page)
    await page.getByRole('button', { name: 'German' }).click()
    await settle(page)
    await page.reload()
    await settle(page)
    check((await page.locator('nav, header').first().innerText()).includes('Einstellungen'), 'Deutsch übersteht das Neuladen nicht')
    await ctx.shot(page, 'language-de')
    await page.getByRole('button', { name: 'Englisch' }).click()
    await settle(page)
    check((await page.locator('nav, header').first().innerText()).includes('Settings'), 'zurück auf Englisch klappt nicht')

    page = await ctx.page('/#/settings?tab=environment')
    check((await page.locator('main').innerText()).includes(join(state.dataDir, 'stockinfo.db')),
      'Umgebung nennt den Datenbankpfad der Instanz nicht')
    await ctx.shot(page, 'environment')
    page = await ctx.page('/#/settings?tab=links')
    check(await page.getByRole('link', { name: 'Swagger UI (/docs)' }).count() === 1, 'Link zur Swagger UI fehlt')
    await ctx.shot(page, 'links')
    page = await ctx.page('/#/settings?tab=about')
    const version = (await api(state.server, '/health')).body.version
    check((await page.locator('body').innerText()).includes(version), `Über/Fußzeile nennt die Version ${version} nicht`)
    await ctx.shot(page, 'about')
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
