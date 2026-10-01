#!/usr/bin/env node
// T-83: Datenhinweis unter der Assets-Übersicht im Browser messen.
//
// Erwartet ein laufendes Dashboard mit Test-API (Start siehe Ticket, Verify #1).
// Verwendung:
//   node _tickets/30-doing/T-83-browser.mjs [URL]
// Umgebung:
//   CHROMIUM_PATH  Pfad zu einem vorhandenen Chromium/Headless-Shell, falls
//                  playwright-core seinen eigenen Browser nicht findet.
//   SHOT_DIR       Zielordner für die Bildausschnitte (Standard: Temp-Ordner).
import { createRequire } from 'node:module'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const rootDir = resolve(dirname(fileURLToPath(import.meta.url)), '../..')
const require = createRequire(join(rootDir, 'dashboard/package.json'))
const { chromium } = require('playwright-core')

const targetUrl = process.argv[2] ?? 'http://localhost:15183/#assets'
const shotDir = process.env.SHOT_DIR ?? mkdtempSync(join(tmpdir(), 't83-browser-'))
const viewports = [['wide', 1440, 900], ['narrow', 390, 844]]

/**
 * Misst Lage und Schriftbild des Hinweises im aktuellen Browserdokument.
 *
 * @returns Messwerte oder die Kennung für einen fehlenden Hinweis.
 */
function measureNotice() {
  const notice = document.querySelector('.table__notice')
  if (!notice) return { notice: false }
  const card = notice.closest('.table.card')
  const previous = notice.previousElementSibling
  const style = getComputedStyle(notice)
  const noticeBox = notice.getBoundingClientRect()
  const previousBox = previous.getBoundingClientRect()
  const cardBox = card.getBoundingClientRect()
  return {
    notice: true,
    count: document.querySelectorAll('.table__notice').length,
    previous: previous.className,
    gapAbovePx: Math.round(noticeBox.top - previousBox.bottom),
    insideCard: noticeBox.left >= cardBox.left && noticeBox.right <= cardBox.right
      && noticeBox.bottom <= cardBox.bottom,
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
  return page.evaluate(() => document.querySelector('.table__notice')?.textContent.slice(0, 45))
}

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
    const notice = page.locator('.table__notice')
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
