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

describe('AppHeader mobile menu', () => {
  it('rendert einen Hamburger-Button mit aria-label aus nav.menu', () => {
    const wrapper = mountHeader()
    const burger = wrapper.find('.hamburger')
    expect(burger.exists()).toBe(true)
    expect(burger.attributes('aria-label')).toBe('Menü')
  })

  it('öffnet den Drawer per Hamburger und schließt ihn bei Tab-Auswahl', async () => {
    const wrapper = mountHeader()
    expect(wrapper.find('.nav-tabs').classes()).not.toContain('open')

    await wrapper.find('.hamburger').trigger('click')
    expect(wrapper.find('.nav-tabs').classes()).toContain('open')

    const tabButtons = wrapper.findAll('.nav-tabs .tab')
    expect(tabButtons).toHaveLength(7)
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
