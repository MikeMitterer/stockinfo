/**
 * Wächter: kein eigenes CSS auf einer Naive-Komponente.
 *
 * Der Anlass ist eine Reihe von Fehlern, die alle gleich aussahen und einzeln
 * gemeldet werden mussten: Knöpfe im Lösch-Dialog zu groß, das ✕ in der
 * Kartenansicht nicht rot, der Richtungsknopf höher als die Auswahl daneben.
 * Dieselbe Ursache jedes Mal — eine `class` an einem `N…`-Element, dazu eine
 * scoped-Regel, die Fläche, Farbe oder Größe setzt. Das addiert sich zu dem,
 * was die Bibliothek ohnehin mitbringt, und macht aus einem Knopf zwei Sorten.
 *
 * **Es gibt eine Sorte Knopf.** Wer die Größe ändern will, nimmt `size`; wer
 * die Bedeutung ändern will, `type`. Was bleibt und hier erlaubt ist: wo ein
 * Element sitzt und wie breit es sein darf (`flex`, `width`, `gap`,
 * `align-*`) — Layout ist Sache der Seite, nicht der Komponente.
 */

import { readdirSync, readFileSync } from 'node:fs'
import { join, relative, resolve } from 'node:path'

import { describe, expect, it } from 'vitest'

const SRC = resolve(process.cwd(), 'src')

/** Was eine Komponentenbibliothek selbst mitbringt — hier also tabu. */
const COMPONENT_PROPERTIES = [
  'background',
  'border',
  'border-radius',
  'padding',
  'color',
  'font-size',
  'font-weight',
  'min-height',
  'min-width',
  'height',
  'box-shadow',
  'margin',
]

/** Alle `.vue`-Dateien unter `src/`, rekursiv. */
function vueFiles(dir: string = SRC): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name)
    if (entry.isDirectory()) return vueFiles(path)
    return entry.name.endsWith('.vue') ? [path] : []
  })
}

interface StyleOverride {
  file: string
  className: string
  properties: string[]
}

/** Sucht Klassen, die an einer Naive-Komponente hängen und eigenes CSS tragen. */
function findOverrides(source: string, file: string): StyleOverride[] {
  const template = source.split('<template>')[1]?.split('<style')[0] ?? ''
  const style = source.split('<style')[1] ?? ''

  const classNames = new Set<string>()
  for (const match of template.matchAll(/<N[A-Za-z]+\b[^>]*?\sclass="([^"]+)"/gs)) {
    for (const name of (match[1] ?? '').split(/\s+/)) classNames.add(name)
  }

  const findings: StyleOverride[] = []
  for (const className of classNames) {
    const rule = new RegExp(`\\.${className.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\{((?:[^{}]|\\{[^{}]*\\})*)\\}`, 'g')
    for (const match of style.matchAll(rule)) {
      const block = match[1] ?? ''
      const properties = COMPONENT_PROPERTIES.filter((name) => {
        const declarations = block.matchAll(new RegExp(`(?<![\\w-])${name}\\s*:\\s*([^;}]+)`, 'g'))
        // Null erlaubt einem Flex-Element zu schrumpfen; feste Mindestbreiten bleiben verboten.
        return [...declarations].some((declaration) => name !== 'min-width' || declaration[1]?.trim() !== '0')
      })
      if (properties.length > 0) findings.push({ file, className, properties })
    }
  }
  return findings
}

describe('Layout-Ausnahme für schrumpfende Flex-Elemente', () => {
  it.each([
    ['min-width: 0;', false],
    ['min-width: 12rem;', true],
    ['min-width: 0; min-width: 12rem;', true],
    ['padding: 0;', true],
  ])('%s bleibt korrekt eingeordnet', (declaration, forbidden) => {
    const source = `<template><NSelect class="probe" /></template><style>.probe { ${declaration} }</style>`
    expect(findOverrides(source, 'probe.vue').length > 0).toBe(forbidden)
  })
})

describe('Eigenes CSS auf Naive-Komponenten', () => {
  it('gibt es nicht — Größe über `size`, Bedeutung über `type`', () => {
    const allFindings = vueFiles().flatMap((path) =>
      findOverrides(readFileSync(path, 'utf8'), relative(process.cwd(), path)),
    )

    const report = allFindings
      .map((f) => `${f.file} → .${f.className}: ${f.properties.join(', ')}`)
      .join('\n')

    expect(allFindings, `Eigenes CSS auf einer Naive-Komponente:\n${report}`).toEqual([])
  })

  it('findet überhaupt Komponenten — sonst prüft der Wächter nichts', () => {
    const withNaive = vueFiles().filter((path) => /<N[A-Za-z]+/.test(readFileSync(path, 'utf8')))

    expect(withNaive.length).toBeGreaterThan(8)
  })
})
