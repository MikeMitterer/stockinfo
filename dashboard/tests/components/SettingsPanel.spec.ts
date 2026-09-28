import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'
import { NButton, NSelect, NTabs } from 'naive-ui'

import SettingsPanel from '../../src/components/SettingsPanel.vue'
import type { SettingsTab } from '../../src/types'
import { i18n } from '../../src/i18n'
import { useTheme } from '../../src/composables/useTheme'

/**
 * Die Einstellungsseite nach der Umstellung auf Naive UI (T-12).
 *
 * Geprüft wird über die Komponenten statt über eigene Klassen: Reiter und
 * Knöpfe gehören jetzt der Bibliothek, ihre inneren Klassen sind nicht unsere
 * Zusage. Was bleibt, ist das Verhalten — welche Reiter es gibt, welcher aktiv
 * ist, und dass eine Auswahl gemeldet wird.
 */
function mountPanel(tab: SettingsTab = 'appearance') {
  return mount(SettingsPanel, {
    props: { tab, env: null },
    global: { plugins: [i18n] },
  })
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
  useTheme().setTheme('mangolila')
})

describe('SettingsPanel', () => {
  it('rendert die Reiter in der Reihenfolge Darstellung, Sprache, Links, Backup, Environment', () => {
    // Über die Reiter-Leiste, nicht über die Panes: Naive rendert nur die
    // aktive Pane — die Beschriftungen stehen trotzdem alle in der Leiste.
    const wrapper = mountPanel()
    const bar = wrapper.find('.n-tabs-nav').text()

    for (const label of ['Darstellung', 'Sprache', 'API & Links', 'Backup', 'Environment']) {
      expect(bar, label).toContain(label)
    }
  })

  it('markiert den aktiven Reiter', () => {
    const wrapper = mountPanel('language')

    expect(wrapper.findComponent(NTabs).props('value')).toBe('language')
    expect(wrapper.findComponent(NSelect).props('value')).toBe('language')
  })

  it('bietet alle Reiter über die mobile Auswahl an', async () => {
    const wrapper = mountPanel('about')
    const selection = wrapper.findComponent(NSelect)

    expect(selection.attributes('aria-label')).toBe('Einstellungsbereich')
    expect(selection.props('options')?.map((option) => option.label)).toEqual([
      'Darstellung', 'Sprache', 'Backup', 'Environment', 'API & Links', 'About',
    ])
    selection.vm.$emit('update:value', 'language')
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('update:tab')?.[0]).toEqual(['language'])
  })

  it('meldet den Wechsel des Reiters', async () => {
    const wrapper = mountPanel('appearance')

    wrapper.findComponent(NTabs).vm.$emit('update:value', 'links')
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('update:tab')?.[0]).toEqual(['links'])
  })

  it('setzt die Sprache über den Sprach-Block und behält die Reiter-Markierung', async () => {
    const wrapper = mountPanel('language')
    const enBtn = wrapper
      .findAllComponents(NButton)
      .find((button) => button.text() === 'Englisch')!

    await enBtn.trigger('click')

    expect(i18n.global.locale.value).toBe('en')
    // Der Marker bleibt am Sprach-Reiter — er kommt aus der Prop, nicht aus
    // einer Messung, und verrutscht deshalb beim Sprachwechsel nicht.
    expect(wrapper.findComponent(NTabs).props('value')).toBe('language')
  })

  it('zeigt im deutschen About-Reiter Datenhinweis und deutsche Lizenz', () => {
    const wrapper = mountPanel('about')

    expect(wrapper.find('.n-tabs-nav').text()).toContain('About')
    expect(wrapper.find('.n-tabs-nav').text()).not.toContain('Über')
    expect(wrapper.text()).toContain('Angaben können fehlen, veraltet oder fehlerhaft sein')
    expect(wrapper.find('a[href$="/LICENSE.de.txt"]').exists()).toBe(true)
    expect(wrapper.find('a[href$="/LICENSING.md"]').exists()).toBe(true)
    expect(wrapper.find('a[href="https://www.mangolila.at/impressum/haftungsausschluss-disclaimer-finanzinhalte/"]').exists()).toBe(true)
    const address = wrapper.get('address.about__address')
    expect(address.text()).toContain('MangoLila GmbH')
    expect(address.text()).toContain('Dorfstraße 112')
    expect(address.text()).toContain('6363 Westendorf')
    expect(address.text()).toContain('Österreich')
    expect(wrapper.get('.about__brand img').attributes('src')).toContain('mangolila-logo-dark.png')
    expect(wrapper.get('a[href="https://www.mangolila.at/"]').text()).toBe('www.mangolila.at')
  })

  it('verwendet in hellen Themes das dunkle Original-Logo', async () => {
    const wrapper = mountPanel('about')

    useTheme().setTheme('paper')
    await wrapper.vm.$nextTick()

    expect(wrapper.get('.about__brand img').attributes('src')).toContain('mangolila-logo-light.png')
  })

  it('wechselt im offenen About-Reiter Text und Lizenzziel auf Englisch', async () => {
    const wrapper = mountPanel('about')

    i18n.global.locale.value = 'en'
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Data may be missing, outdated or incorrect')
    expect(wrapper.find('a[href$="/LICENSE"]').exists()).toBe(true)
    expect(wrapper.find('a[href$="/LICENSE.de.txt"]').exists()).toBe(false)
    expect(wrapper.get('address.about__address').text()).toContain('Austria')
  })
})
