import { mount, type VueWrapper } from '@vue/test-utils'
import { afterEach, expect, it } from 'vitest'
import { nextTick } from 'vue'

import ConfirmExchangeDialog from '../../src/components/ConfirmExchangeDialog.vue'
import { i18n } from '../../src/i18n'
import type { IntakeConfirmation } from '../../src/types'

let wrapper: VueWrapper | null = null
const decision: IntakeConfirmation = {
  status: 'confirmation_required', name: 'Vanguard', exchange: 'NYSE Arca', currency: 'CHF',
  identity: { kind: 'listed', ticker: 'VTI', mic: 'ARCX', isin: 'US9229087690' },
  preferred: { mic: 'XETR', name: 'Xetra', currency: 'EUR' },
}
afterEach(() => { wrapper?.unmount(); document.body.innerHTML = ''; i18n.global.locale.value = 'de' })

it.each(['de', 'en'] as const)('zeigt beide Börsen und beide Entscheidungen auf %s', async (locale) => {
  i18n.global.locale.value = locale
  wrapper = mount(ConfirmExchangeDialog, { props: { decision, busy: false }, attachTo: document.body, global: { plugins: [i18n] } })
  await nextTick()
  const text = document.body.textContent
  for (const value of ['Vanguard', 'NYSE Arca', 'ARCX', 'CHF', 'Xetra', 'XETR', 'EUR']) expect(text).toContain(value)
  const buttons = [...document.querySelectorAll('button')]
  const cancel = buttons.find(button => button.textContent === (locale === 'de' ? 'Abbrechen' : 'Cancel'))
  const confirm = buttons.find(button => button.textContent === (locale === 'de' ? 'Dennoch aufnehmen' : 'Add anyway'))
  expect(cancel).toBeDefined()
  expect(confirm).toBeDefined()
  cancel?.click()
  expect(wrapper.emitted('cancel')).toHaveLength(1)
  expect(wrapper.emitted('confirm')).toBeUndefined()
  confirm?.click()
  expect(wrapper.emitted('confirm')).toHaveLength(1)
  await wrapper.setProps({ busy: true })
  expect(cancel?.disabled).toBe(true)
  expect(confirm?.disabled).toBe(true)
})
