import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'

import { NInput } from 'naive-ui'

import IsinEditor from '../../src/components/IsinEditor.vue'
import { i18n } from '../../src/i18n'

function mountEditor() {
  return mount(IsinEditor, { props: { symbol: 'APC.DE' }, global: { plugins: [i18n] } })
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
})

describe('IsinEditor', () => {
  it('zeigt zunächst nur den Knopf zum Nachtragen', () => {
    const wrapper = mountEditor()
    expect(wrapper.find('.isin__add').exists()).toBe(true)
    expect(wrapper.findComponent(NInput).exists()).toBe(false)
  })

  it('öffnet die Eingabe per Klick', async () => {
    const wrapper = mountEditor()
    await wrapper.find('.isin__add').trigger('click')
    expect(wrapper.findComponent(NInput).exists()).toBe(true)
  })

  it('emittiert save bei gültiger ISIN', async () => {
    const wrapper = mountEditor()
    await wrapper.find('.isin__add').trigger('click')
    await wrapper.findComponent(NInput).find('input').setValue('US0378331005')
    await wrapper.find('.isin__ok').trigger('click')
    expect(wrapper.emitted('save')?.[0]).toEqual([{ symbol: 'APC.DE', isin: 'US0378331005' }])
  })

  it('zeigt bei ungültiger ISIN einen Hinweis und emittiert nicht', async () => {
    const wrapper = mountEditor()
    await wrapper.find('.isin__add').trigger('click')
    await wrapper.findComponent(NInput).find('input').setValue('QUATSCH')
    await wrapper.find('.isin__ok').trigger('click')
    expect(wrapper.emitted('save')).toBeUndefined()
    expect(wrapper.find('.isin__err').exists()).toBe(true)
  })

  it('normalisiert Kleinschreibung', async () => {
    const wrapper = mountEditor()
    await wrapper.find('.isin__add').trigger('click')
    await wrapper.findComponent(NInput).find('input').setValue('us0378331005')
    await wrapper.find('.isin__ok').trigger('click')
    expect(wrapper.emitted('save')?.[0]).toEqual([{ symbol: 'APC.DE', isin: 'US0378331005' }])
  })
})
