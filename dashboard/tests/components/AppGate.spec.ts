/** Die sichtbare Gate-Handlung bis zum vorhandenen Backup-Composable. */
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

const actions = vi.hoisted(() => ({
  check: vi.fn(),
  confirm: vi.fn(),
  retry: vi.fn(),
  createBackup: vi.fn().mockResolvedValue(undefined),
}))

vi.mock('../../src/composables/useMigration', () => ({
  useMigration: () => ({
    phase: ref('pending'),
    preview: ref({
      pending: true,
      migrating: 1,
      unchanged: 0,
      rejected: [],
      lost_quotes: 0,
      lost_daily_closes: 0,
    }),
    report: ref(null),
    error: ref(null),
    check: actions.check,
    confirm: actions.confirm,
    retry: actions.retry,
  }),
}))

vi.mock('../../src/composables/useBackups', () => ({
  useBackups: () => ({
    loading: ref(false),
    error: ref(null),
    create: actions.createBackup,
  }),
}))

import AppGate from '../../src/components/AppGate.vue'
import { i18n } from '../../src/i18n'

describe('AppGate · Sicherung vor der Migration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    actions.createBackup.mockResolvedValue(undefined)
  })

  it('verdrahtet genau den Sicherungsklick und bestätigt die Migration nicht', async () => {
    const wrapper = mount(AppGate, { global: { plugins: [i18n] } })

    await wrapper.find('.gate__backup-action').trigger('click')
    await flushPromises()

    expect(actions.createBackup).toHaveBeenCalledTimes(1)
    expect(actions.confirm).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain(i18n.global.t('migration.backupDone'))
  })
})
