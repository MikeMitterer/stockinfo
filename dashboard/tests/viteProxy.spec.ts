/**
 * Der Dev-Proxy kennt jeden Pfad, den die App anfordert — `#2b6i`.
 *
 * **Der Fehler ist schon einmal passiert** und liegt als
 * `_tickets/40-done/T-04-vite-proxy-fehlende-praefixe.md` im Board: Fehlt ein
 * Präfix, liefert der Dev-Server die `index.html` statt der API-Antwort. Die
 * App bekommt HTML, wo sie JSON erwartet, und der Fehler sieht aus wie ein
 * kaputtes Backend — im Produktionsbau, wo alles derselbe Server ausliefert,
 * ist er unsichtbar.
 *
 * **Geprüft wird gegen die Wirklichkeit, nicht gegen eine zweite Liste.** Der
 * Test liest die Pfade aus dem Quelltext der App und hält sie gegen die
 * Präfixe aus `vite.config.ts`. Eine hier abgeschriebene Erwartungsliste
 * belegte nur, dass zwei Listen gleich sind — und beim nächsten neuen Endpunkt
 * hätte man sie beide zu ergänzen vergessen.
 *
 * **Was er nicht kann:** Er findet nur **Zeichenketten-Literale**. Pfade, die
 * zur Laufzeit zusammengesetzt werden (`instrumentPath`, `quotePath`), stehen
 * nicht darin; sie beginnen aber mit Präfixen, die ohnehin gelistet sind.
 * Genau die Literale sind die Klasse, die in T-04 gefehlt hat.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'

import { describe, expect, it } from 'vitest'

import { apiPrefixes } from '../api-prefixes'

const SRC = join(__dirname, '..', 'src')

/** Alle Quelldateien unter `src/`, rekursiv. */
function sourceFiles(directory: string): string[] {
  return readdirSync(directory).flatMap((entry) => {
    const full = join(directory, entry)
    if (statSync(full).isDirectory()) return sourceFiles(full)
    return /\.(ts|vue)$/.test(full) ? [full] : []
  })
}

/**
 * Die Pfad-Literale, mit denen die App den `apiClient` aufruft.
 *
 * Gesucht wird am Aufruf, nicht an irgendeiner Zeichenkette mit Schrägstrich:
 * Ein `'/settings'` aus dem Hash-Routing ist kein API-Pfad und hätte den Test
 * mit einer falschen Forderung rot gemacht.
 */
function requestedPaths(): Set<string> {
  const calls = /apiClient\.(?:get|post|put|del|probe)(?:<[^>]*>)?\(\s*'([^']+)'/g
  const found = new Set<string>()

  for (const file of sourceFiles(SRC)) {
    const text = readFileSync(file, 'utf-8')
    for (const match of text.matchAll(calls)) {
      found.add(match[1].split('?')[0])
    }
  }
  return found
}

describe('Dev-Proxy', () => {
  it('deckt jeden angeforderten Pfad mit einem Präfix ab', () => {
    const paths = [...requestedPaths()]

    // Ohne diese Zusicherung wäre ein kaputter Regex ein grüner Test über
    // einer leeren Menge — die Prüfung, die sich selbst bestätigt.
    expect(paths.length).toBeGreaterThan(5)

    const uncovered = paths.filter(
      (path) => !apiPrefixes.some((prefix) => path === prefix || path.startsWith(`${prefix}/`)),
    )

    expect(uncovered).toEqual([])
  })

  it('führt die drei Wege des Umzugs und der Diagnose', () => {
    // Sie sind der Anlass dieser Runde: Ohne sie bekäme der Umzugsbildschirm
    // die `index.html` und liefe in einen JSON-Parse-Fehler.
    expect(apiPrefixes).toContain('/migration')
    expect(apiPrefixes).toContain('/ready')
    expect(apiPrefixes).toContain('/operational')
  })

  it('reklamiert keine Pfade, die das SPA selbst bedient', () => {
    // Ein Präfix zu viel ist der spiegelbildliche Fehler: `/` oder `/assets`
    // in dieser Liste schickte die Oberfläche selbst ans Backend.
    expect(apiPrefixes).not.toContain('/')
    expect(apiPrefixes).not.toContain('/assets')
  })
})
