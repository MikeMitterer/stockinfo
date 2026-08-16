import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'

import AppHeader from '../../src/components/AppHeader.vue'
import { i18n } from '../../src/i18n'

/**
 * Die Kopfzeile nach der Umstellung auf das Fundament (T-12).
 *
 * Zwei Dinge haben sich gegenüber T-05/T-11a **bewusst gedreht**: Der
 * Hamburger ist weg — unter dem Umschaltpunkt fällt die Beschriftung weg, nicht
 * der Punkt —, und die Einstellungen stehen nicht mehr als Zahnrad rechts,
 * sondern als fünfter Punkt links bei den anderen. Sie sind eine Seite, also
 * ein Ort, kein Werkzeug.
 */
function mountHeader() {
  return mount(AppHeader, { props: { active: 'assets' }, global: { plugins: [i18n] } })
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
})

describe('AppHeader', () => {
  it('rendert die Arbeitsbereiche in fester Reihenfolge, Einstellungen zuletzt', () => {
    const wrapper = mountHeader()
    const labels = wrapper.findAll('.ux-navitem__label').map((s) => s.text())

    expect(labels).toEqual(['Assets', 'Börsen', 'Devisen', 'Analyse', 'Einstellungen'])
  })

  it('zeigt keinen Sprach-Umschalter mehr in der Kopfzeile', () => {
    // Der gehört in die Einstellungen — er wird zweimal im Leben angefasst.
    const wrapper = mountHeader()

    expect(wrapper.find('.lang').exists()).toBe(false)
  })

  it('hat keinen Hamburger und keinen Drawer mehr', () => {
    // Die Symbole bleiben unter dem Umschaltpunkt in der Zeile stehen: Die
    // Navigation ist damit einen Griff entfernt statt zwei.
    const wrapper = mountHeader()

    expect(wrapper.find('.hamburger').exists()).toBe(false)
    expect(wrapper.find('.backdrop').exists()).toBe(false)
  })

  it('führt der Einstellungen-Punkt zu settings — links, nicht als Zahnrad rechts', async () => {
    const wrapper = mountHeader()
    const punkte = wrapper.findAll('.ux-navitem')

    await punkte[punkte.length - 1].trigger('click')

    expect(wrapper.emitted('navigate')?.[0]).toEqual(['settings'])
  })

  it('meldet die Auswahl eines Bereichs', async () => {
    const wrapper = mountHeader()

    await wrapper.findAll('.ux-navitem')[1].trigger('click')

    expect(wrapper.emitted('navigate')?.[0]).toEqual(['exchanges'])
  })

  it('markiert den aktiven Bereich für Hilfstechnik', () => {
    const wrapper = mountHeader()
    const aktiv = wrapper.findAll('[aria-current="page"]')

    expect(aktiv).toHaveLength(1)
    expect(aktiv[0].text()).toContain('Assets')
  })
})
