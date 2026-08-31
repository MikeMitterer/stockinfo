import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'

import StatusBar from '../../src/components/StatusBar.vue'
import { i18n } from '../../src/i18n'

/**
 * Die Statuszeile nennt seit T-43 die Quelle, von der die Kurse kommen.
 *
 * Geprueft wird der **Kontexttext**, den die Zeile ans Fundament reicht — nicht
 * dessen Darstellung. Wie `UxStatusBar` ihn setzt, ist Sache des Fundaments;
 * dass diese App die richtige Angabe hineinlegt, ist Sache dieser Datei.
 */
function mountBar(props: Record<string, unknown> = {}) {
  return mount(StatusBar, {
    props: { status: 'ok', version: '0.6.0', ...props },
    global: { plugins: [i18n] },
  })
}

/** Der Kontexttext, wie ihn die Zeile an das Fundament weitergibt. */
function contextOf(wrapper: ReturnType<typeof mountBar>): string {
  return wrapper.findComponent({ name: 'UxStatusBar' }).props('context') as string
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
})

describe('StatusBar', () => {
  it('nennt die Kursquelle neben der Anzahl der Papiere', () => {
    const wrapper = mountBar({ instrumentCount: 4, quoteSource: 'yaml-file' })

    expect(contextOf(wrapper)).toBe('4 Papiere · Kurse: yaml-file')
  })

  /*
   * Ohne Quelle faellt die Angabe **samt Trenner** weg. Ein Trenner ins Leere
   * sieht aus wie ein Ladefehler — und genau das soll die Zeile nicht sagen,
   * wenn `/sources` schlicht nicht geantwortet hat.
   */
  it('laesst die Angabe weg, wenn keine Quelle bekannt ist', () => {
    const wrapper = mountBar({ instrumentCount: 4, quoteSource: null })

    expect(contextOf(wrapper)).toBe('4 Papiere')
  })

  /*
   * Die Zeile sagt, **welche Rolle** sie nennt. Ohne diese Beschriftung waere
   * `yaml-file` eine Aussage ueber die ganze Installation — vier weitere
   * Rollen koennen jederzeit von jemand anderem bedient werden.
   */
  it('beschriftet die Quelle als Kursquelle, nicht als „die Quelle"', () => {
    const wrapper = mountBar({ instrumentCount: 1, quoteSource: 'yfinance' })

    expect(contextOf(wrapper)).toContain('Kurse: yfinance')
  })

  it('uebersetzt die Beschriftung mit', () => {
    i18n.global.locale.value = 'en'
    const wrapper = mountBar({ instrumentCount: 1, quoteSource: 'yfinance' })

    expect(contextOf(wrapper)).toBe('one instrument · Quotes: yfinance')
  })
})
