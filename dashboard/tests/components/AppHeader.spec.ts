import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'

import AppHeader from '../../src/components/AppHeader.vue'
import { i18n } from '../../src/i18n'

function mountHeader() {
  return mount(AppHeader, { props: { active: 'assets' }, global: { plugins: [i18n] } })
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
})

describe('AppHeader', () => {
  it('rendert genau vier Arbeitsbereiche in fester Reihenfolge', () => {
    const wrapper = mountHeader()
    const labels = wrapper.findAll('.nav-tabs .tab span').map((s) => s.text())
    expect(labels).toEqual(['Assets', 'Börsen', 'Devisen', 'Analyse'])
  })

  it('zeigt keinen Sprach-Umschalter mehr in der Kopfzeile', () => {
    const wrapper = mountHeader()
    expect(wrapper.find('.lang').exists()).toBe(false)
  })

  it('rendert ein Zahnrad, das zu settings navigiert', async () => {
    const wrapper = mountHeader()
    const gear = wrapper.find('.settings-btn')
    expect(gear.exists()).toBe(true)
    expect(gear.attributes('aria-label')).toBe('Einstellungen')
    await gear.trigger('click')
    expect(wrapper.emitted('navigate')?.[0]).toEqual(['settings'])
  })

  it('öffnet den Drawer per Hamburger und schließt ihn bei Tab-Auswahl', async () => {
    const wrapper = mountHeader()
    await wrapper.find('.hamburger').trigger('click')
    expect(wrapper.find('.nav-tabs').classes()).toContain('open')

    const tabButtons = wrapper.findAll('.nav-tabs .tab')
    expect(tabButtons).toHaveLength(4)
    await tabButtons[1].trigger('click') // exchanges
    expect(wrapper.emitted('navigate')?.[0]).toEqual(['exchanges'])
    expect(wrapper.find('.nav-tabs').classes()).not.toContain('open')
  })

  it('schließt den offenen Drawer bei Escape', async () => {
    const wrapper = mountHeader()
    await wrapper.find('.hamburger').trigger('click')
    expect(wrapper.find('.nav-tabs').classes()).toContain('open')
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.nav-tabs').classes()).not.toContain('open')
  })
})
