#!/usr/bin/env node
//------------------------------------------------------------------------------
// T-83-browser.mjs — Datenhinweis unter der Assets-Übersicht im Browser messen
//
// Misst bei 1440 × 900 und 390 × 844, ob genau ein Hinweis direkt unter der
// Assets-Karte steht, links bündig mit ihr, in 12 px und ohne waagrechtes
// Scrollen. Wechselt breit DE → EN → DE ohne Neuladen und speichert je Breite
// einen Bildausschnitt. Voraussetzung: laufendes Dashboard mit Test-API
// (Startweg im Ticket T-83 unter „Belege“) und playwright-core aus dashboard/.
//
// Verwendung:
//   node _tickets/40-done/T-83-browser.mjs --run [URL]
//   node _tickets/40-done/T-83-browser.mjs --help
//
// Optionen:
//   -r | --run [URL]   Messung starten (Standard-URL: http://localhost:15183/#assets)
//   -h | --help        Diese Hilfe anzeigen; auch ohne Argumente
//
// Umgebung:
//   CHROMIUM_PATH      Vorhandener Chromium, falls playwright-core seinen
//                      eigenen Browser nicht findet
//   SHOT_DIR           Zielordner der Bildausschnitte (Standard: Temp-Ordner)
//------------------------------------------------------------------------------
import { createRequire } from 'node:module'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { basename, dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptPath = fileURLToPath(import.meta.url)
const defaultUrl = 'http://localhost:15183/#assets'
const viewports = [['wide', 1440, 900], ['narrow', 390, 844]]
const options = [
  ['-r', '--run [URL]', `Messung starten (Standard-URL: ${defaultUrl})`],
  ['-h', '--help', 'Diese Hilfe anzeigen; auch ohne Argumente'],
]

/**
 * Gibt die Hilfe mit fest ausgerichteten Optionsspalten aus.
 *
 * @returns Kein Rückgabewert; die Hilfe erscheint auf stdout.
 */
function printHelp() {
  const longWidth = Math.max(...options.map(([, long]) => long.length))
  console.log(`\nVerwendung: node ${basename(scriptPath)} --run [URL] | --help\n`)
  console.log('Optionen:')
  for (const [short, long, text] of options) {
    console.log(`    ${short} | ${long.padEnd(longWidth)}   ${text}`)
  }
  console.log('\nUmgebung: CHROMIUM_PATH (vorhandener Chromium), SHOT_DIR (Bildordner)\n')
}

/**
 * Liest die Befehlszeile.
 *
 * @param args - Argumente nach dem Skriptnamen.
 * @returns `{ action: 'help' }` oder `{ action: 'run', url }`.
 */
function parseArgs(args) {
  const [first, second, ...rest] = args
  if (first === undefined || first === '-h' || first === '--help') return { action: 'help' }
  if ((first === '-r' || first === '--run') && rest.length === 0) {
    return { action: 'run', url: second ?? defaultUrl }
  }
  return { action: 'error', message: `Unbekannter Aufruf: ${args.join(' ')}` }
}

/**
 * Misst Lage und Schriftbild des Hinweises im aktuellen Browserdokument.
 *
 * @returns Messwerte oder die Kennung für einen fehlenden Hinweis.
 */
function measureNotice() {
  const notice = document.querySelector('.table-notice')
  if (!notice) return { notice: false }
  const card = notice.previousElementSibling
  const style = getComputedStyle(notice)
  const noticeBox = notice.getBoundingClientRect()
  const cardBox = card.getBoundingClientRect()
  return {
    notice: true,
    count: document.querySelectorAll('.table-notice').length,
    previousIsCard: card.matches('.table.card'),
    insideCard: card.contains(notice),
    gapBelowCardPx: Math.round(noticeBox.top - cardBox.bottom),
    leftOffsetPx: Math.round(noticeBox.left - cardBox.left),
    widthDifferencePx: Math.round(noticeBox.width - cardBox.width),
    fontSize: style.fontSize,
    lineHeight: style.lineHeight,
    horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
  }
}

/**
 * Wechselt die Sprache ohne Neuladen und liest den sichtbaren Hinweis an.
 *
 * @param page - Geöffnete Browserseite.
 * @param locale - Gewünschte Sprache.
 * @returns Anfang des sichtbaren Hinweistextes.
 */
async function switchLocale(page, locale) {
  await page.evaluate((value) => {
    document.querySelector('#app').__vue_app__.config.globalProperties.$i18n.locale = value
  }, locale)
  await page.waitForTimeout(200)
  return page.evaluate(() => document.querySelector('.table-notice')?.textContent.slice(0, 45))
}

/**
 * Misst beide Breiten und speichert die Bildausschnitte.
 *
 * @param targetUrl - Adresse der Assets-Übersicht.
 * @returns Kein Rückgabewert; Messwerte erscheinen auf stdout.
 */
async function runMeasurement(targetUrl) {
  const rootDir = resolve(dirname(scriptPath), '../..')
  const require = createRequire(join(rootDir, 'dashboard/package.json'))
  const { chromium } = require('playwright-core')
  const shotDir = process.env.SHOT_DIR ?? mkdtempSync(join(tmpdir(), 't83-browser-'))

  const browser = await chromium.launch(
    process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {},
  )
  try {
    for (const [label, width, height] of viewports) {
      const page = await browser.newPage({ viewport: { width, height }, locale: 'de-DE' })
      await page.goto(targetUrl)
      await page.waitForSelector('.table.card')
      await page.waitForTimeout(800)
      console.log(label, JSON.stringify(await page.evaluate(measureNotice)))
      if (label === 'wide') {
        for (const locale of ['de', 'en', 'de']) {
          console.log(`locale ${locale}`, JSON.stringify(await switchLocale(page, locale)))
        }
      }
      const notice = page.locator('.table-notice')
      await notice.scrollIntoViewIfNeeded()
      const box = await notice.boundingBox()
      const shotPath = join(shotDir, `t83-${label}.png`)
      await page.screenshot({
        path: shotPath,
        clip: { x: 0, y: Math.max(0, box.y - 260), width, height: Math.min(360, height) },
      })
      console.log(`screenshot ${shotPath}`)
      await page.close()
    }
  } finally {
    await browser.close()
  }
}

const command = parseArgs(process.argv.slice(2))
if (command.action === 'help') {
  printHelp()
} else if (command.action === 'error') {
  console.error(command.message)
  printHelp()
  process.exitCode = 2
} else {
  await runMeasurement(command.url)
}
