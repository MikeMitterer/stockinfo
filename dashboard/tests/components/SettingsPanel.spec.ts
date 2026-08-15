import { shallowMount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'

import SettingsPanel from '../../src/components/SettingsPanel.vue'
import { i18n } from '../../src/i18n'

function mountPanel(tab: 'appearance' | 'language' | 'links' | 'environment' = 'appearance') {
  return shallowMount(SettingsPanel, {
    props: { tab, env: null },
    global: { plugins: [i18n] },
  })
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
})

describe('SettingsPanel', () => {
  it('rendert vier Reiter in der Reihenfolge Darstellung, Sprache, Links, Environment', () => {
    const wrapper = mountPanel()
    const labels = wrapper.findAll('.settings__tab').map((b) => b.text())
    expect(labels).toEqual(['Darstellung', 'Sprache', 'API & Links', 'Environment'])
  })

  it('markiert den aktiven Reiter', () => {
    const wrapper = mountPanel('language')
    const active = wrapper.findAll('.settings__tab').filter((b) => b.classes('active'))
    expect(active).toHaveLength(1)
    expect(active[0].text()).toBe('Sprache')
  })

  it('emittiert update:tab beim Klick auf einen Reiter', async () => {
    const wrapper = mountPanel('appearance')
    const linksTab = wrapper.findAll('.settings__tab').find((b) => b.text() === 'API & Links')!
    await linksTab.trigger('click')
    expect(wrapper.emitted('update:tab')?.[0]).toEqual(['links'])
  })

  it('setzt die Sprache über den Sprach-Block und behält die Reiter-Markierung', async () => {
    const wrapper = mountPanel('language')
    const enBtn = wrapper.findAll('.lang-choice__btn').find((b) => b.text() === 'Englisch')!
    await enBtn.trigger('click')
    expect(i18n.global.locale.value).toBe('en')
    // Marker bleibt auf dem Sprach-Reiter (messungsfrei, aus der tab-Prop abgeleitet)
    const active = wrapper.findAll('.settings__tab').filter((b) => b.classes('active'))
    expect(active).toHaveLength(1)
  })
})
