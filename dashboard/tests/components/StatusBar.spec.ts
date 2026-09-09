import { mount, type VueWrapper } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'

import StatusBar from '../../src/components/StatusBar.vue'
import { i18n } from '../../src/i18n'

/** Prüft den sichtbaren Kontext der echten Statuszeile. */
function mountBar(props: Record<string, unknown> = {}): VueWrapper {
  return mount(StatusBar, {
    props: { status: 'ok', version: '0.6.0', ...props },
    global: { plugins: [i18n] },
  })
}

/** Der Kontext steht im linken Slot unmittelbar nach dem Repo-Link. */
function contextOf(wrapper: ReturnType<typeof mountBar>): string {
  return wrapper.get('.status__context').text()
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
})

describe('StatusBar', () => {
  /*
   * **Beide Namen, in Rangfolge, mit dem Pfeil dazwischen.** Eine Zeile, die
   * nur den Kopf nennt, behauptet eine Herkunft, die `/sources` nicht kennt.
   */
  it('nennt die ganze Kurskette in Rangfolge', () => {
    const wrapper = mountBar({ instrumentCount: 4, quoteChain: ['yfinance', 'yaml-file'] })

    expect(contextOf(wrapper)).toBe('4 Papiere · Kurse: yfinance → yaml-file')
  })

  it('nennt eine einzelne Quelle ohne Pfeil', () => {
    const wrapper = mountBar({ instrumentCount: 4, quoteChain: ['yaml-file'] })

    expect(contextOf(wrapper)).toBe('4 Papiere · Kurse: yaml-file')
  })

  /*
   * Ohne Kette faellt die Angabe **samt Trenner** weg — ein Trenner ins Leere
   * sieht aus wie ein Ladefehler.
   */
  it('laesst die Angabe weg, wenn keine Kette bekannt ist', () => {
    const wrapper = mountBar({ instrumentCount: 4, quoteChain: [] })

    expect(contextOf(wrapper)).toBe('4 Papiere')
  })

  /*
   * Die Zeile sagt, **welche Rolle** sie nennt: Vier weitere kann jemand
   * anderes bedienen.
   */
  it('beschriftet die Kette als Kurskette, nicht als „die Quelle"', () => {
    const wrapper = mountBar({ instrumentCount: 1, quoteChain: ['yfinance'] })

    expect(contextOf(wrapper)).toContain('Kurse: yfinance')
  })

  it('uebersetzt die Beschriftung mit', () => {
    i18n.global.locale.value = 'en'
    const wrapper = mountBar({ instrumentCount: 1, quoteChain: ['yfinance', 'yaml-file'] })

    expect(contextOf(wrapper)).toBe('one instrument · Quotes: yfinance → yaml-file')
  })
})
