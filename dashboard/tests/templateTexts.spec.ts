/**
 * Wächter: kein sichtbarer Text fest in einem Template.
 *
 * Sichtbarer Text kommt aus dem Katalog (`src/i18n`), sonst steht er in der
 * englischen Oberfläche deutsch da oder umgekehrt. T-138 hat die letzten
 * Reste entfernt („+ ISIN“, „JSON“, die Einheit „s“ der Analyse). Geprüft
 * werden Textknoten und die Attribute, die ein Mensch liest: `title`,
 * `aria-label`, `placeholder`, `label`. Gebundene Ausdrücke (`{{ t(…) }}`,
 * `:title`) zählen nicht — sie laufen über `t()`.
 *
 * Was keine Sprache hat, darf stehen: Ziffern, Satzzeichen, Pfeile und
 * Rechenzeichen, dazu die Kennungen in `LANGUAGE_FREE_TEXTS`.
 */

import { readdirSync, readFileSync } from 'node:fs'
import { join, relative, resolve } from 'node:path'

import { parse } from '@vue/compiler-sfc'
import { describe, expect, it } from 'vitest'

const SRC = resolve(process.cwd(), 'src')

/** Attribute, deren Wert ein Mensch liest. */
const READ_ATTRIBUTES = new Set(['title', 'aria-label', 'placeholder', 'label'])

/** Zeichen ohne Sprache: Ziffern, Satz- und Rechenzeichen, Pfeile, Leerraum. */
const SYMBOLS_ONLY = /^[\s\d.,:;·•—–\-+=×✕✓↻↺←→↑↓⇄↗▲▼▸▾…%/()[\]|*#&]*$/u

/** Text, der in jeder Sprache gleich bleibt — mit Grund. */
const LANGUAGE_FREE_TEXTS = new Set([
  '.env.example', // Dateiname im Repo (EnvironmentPanel)
  'SAP.DE', // Beispielkennung: Ticker mit App-Suffix (ExchangesPanel)
  'SAP.XETR', // Beispielkennung: Ticker mit MIC (ExchangesPanel)
])

interface Finding {
  where: string
  text: string
}

/** Alle `.vue`-Dateien unter `dir`, rekursiv. */
function vueFiles(dir: string = SRC): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name)
    if (entry.isDirectory()) return vueFiles(path)
    return entry.name.endsWith('.vue') ? [path] : []
  })
}

function isLanguageFree(text: string): boolean {
  return SYMBOLS_ONLY.test(text) || LANGUAGE_FREE_TEXTS.has(text)
}

/** Sucht feste Texte im Template einer Single-File-Component. */
function fixedTexts(source: string, file: string): Finding[] {
  const { descriptor } = parse(source, { filename: file })
  const findings: Finding[] = []
  // Knotentypen des Vue-Compilers: 1 = Element, 2 = Text, 6 = statisches Attribut.
  const visit = (node: { type: number; content?: string; props?: unknown[]; children?: unknown[]; loc: { start: { line: number } } }): void => {
    if (node.type === 2) {
      const text = (node.content ?? '').trim()
      if (text && !isLanguageFree(text)) findings.push({ where: `${file}:${node.loc.start.line}`, text })
    }
    for (const prop of (node.props ?? []) as { type: number; name: string; value?: { content: string }; loc: { start: { line: number } } }[]) {
      if (prop.type === 6 && READ_ATTRIBUTES.has(prop.name) && prop.value && !isLanguageFree(prop.value.content)) {
        findings.push({ where: `${file}:${prop.loc.start.line}`, text: `${prop.name}="${prop.value.content}"` })
      }
    }
    for (const child of (node.children ?? []) as Parameters<typeof visit>[0][]) visit(child)
  }
  if (descriptor.template?.ast) visit(descriptor.template.ast as unknown as Parameters<typeof visit>[0])
  return findings
}

describe('Templates ohne festen Text', () => {
  it('findet in src/ keinen sichtbaren Text außerhalb des Katalogs', () => {
    const findings = vueFiles().flatMap((file) =>
      fixedTexts(readFileSync(file, 'utf8'), relative(process.cwd(), file)),
    )

    expect(findings).toEqual([])
  })

  it('erkennt festen Text, eine sprachfreie Kennung aber nicht (Gegenprobe)', () => {
    // Ohne diese Probe wäre ein grüner Lauf oben wertlos: Er hieße auch dann
    // „nichts gefunden“, wenn der Scan gar nichts erkennt.
    const source = `<template>
      <button title="Speichern">+ ISIN</button>
      <span>12 %</span>
      <code>SAP.DE</code>
      <span>{{ t('table.jsonShort') }}</span>
    </template>`

    expect(fixedTexts(source, 'probe.vue').map((finding) => finding.text)).toEqual([
      'title="Speichern"',
      '+ ISIN',
    ])
  })
})
