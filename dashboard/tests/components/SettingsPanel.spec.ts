import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'
import { NButton, NTabs } from 'naive-ui'

import SettingsPanel from '../../src/components/SettingsPanel.vue'
import { i18n } from '../../src/i18n'

/**
 * Die Einstellungsseite nach der Umstellung auf Naive UI (T-12).
 *
 * Geprüft wird über die Komponenten statt über eigene Klassen: Reiter und
 * Knöpfe gehören jetzt der Bibliothek, ihre inneren Klassen sind nicht unsere
 * Zusage. Was bleibt, ist das Verhalten — welche Reiter es gibt, welcher aktiv
 * ist, und dass eine Auswahl gemeldet wird.
 */
function mountPanel(tab: 'appearance' | 'language' | 'links' | 'environment' = 'appearance') {
  return mount(SettingsPanel, {
    props: { tab, env: null },
    global: { plugins: [i18n] },
  })
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
})

describe('SettingsPanel', () => {
  it('rendert vier Reiter in der Reihenfolge Darstellung, Sprache, Links, Environment', () => {
    // Über die Reiter-Leiste, nicht über die Panes: Naive rendert nur die
    // aktive Pane — die Beschriftungen stehen trotzdem alle in der Leiste.
    const wrapper = mountPanel()
    const leiste = wrapper.find('.n-tabs-nav').text()

    for (const label of ['Darstellung', 'Sprache', 'API & Links', 'Environment']) {
      expect(leiste, label).toContain(label)
    }
  })

  it('markiert den aktiven Reiter', () => {
    const wrapper = mountPanel('language')

    expect(wrapper.findComponent(NTabs).props('value')).toBe('language')
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
})
