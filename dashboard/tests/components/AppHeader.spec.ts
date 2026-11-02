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
function mountHeader(refreshing = false) {
  return mount(AppHeader, {
    props: { active: 'assets', refreshing },
    global: { plugins: [i18n] },
  })
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
    const navItems = wrapper.findAll('.ux-navitem')

    await navItems[navItems.length - 1].trigger('click')

    expect(wrapper.emitted('navigate')?.[0]).toEqual(['settings'])
  })

  it('meldet die Auswahl eines Bereichs', async () => {
    const wrapper = mountHeader()

    await wrapper.findAll('.ux-navitem')[1].trigger('click')

    expect(wrapper.emitted('navigate')?.[0]).toEqual(['exchanges'])
  })

  it('markiert den aktiven Bereich für Hilfstechnik', () => {
    const wrapper = mountHeader()
    const activeItems = wrapper.findAll('[aria-current="page"]')

    expect(activeItems).toHaveLength(1)
    expect(activeItems[0].text()).toContain('Assets')
  })

  /*
   * Seit T-13 steht „Alle aktualisieren" rechts in der Leiste statt über der
   * Tabelle. Der Grund ist nicht Geschmack: Im oberen rechten Eck des Inhalts
   * erscheinen die Fehler-Toasts, und die bleiben stehen, bis man sie
   * wegklickt — der Knopf lag also unter der Meldung, die er behebt.
   */
  it('trägt die Aktualisieren-Handlung rechts, nicht zwischen den Menüpunkten', () => {
    const wrapper = mountHeader()
    const actions = wrapper.find('.ux-topbar__actions')

    expect(actions.exists()).toBe(true)
    expect(actions.text()).toContain('Alle aktualisieren')
    expect(actions.find('.ux-navitem').exists()).toBe(false)
  })

  it('meldet den Klick auf Aktualisieren', async () => {
    const wrapper = mountHeader()

    await wrapper.find('.ux-topbar__actions button').trigger('click')

    expect(wrapper.emitted('refresh')).toHaveLength(1)
  })

  it('sperrt den Knopf, solange aktualisiert wird', () => {
    // Sonst stößt ein zweiter Klick denselben Lauf noch einmal an.
    const wrapper = mountHeader(true)
    const button = wrapper.find('.ux-topbar__actions button')

    expect(button.attributes('disabled')).toBeDefined()
    expect(button.text()).toContain('Aktualisiere')
  })
})
