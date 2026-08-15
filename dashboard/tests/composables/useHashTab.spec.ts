import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import { defineComponent, nextTick, type Ref } from 'vue'

import { useHashTab } from '../../src/composables/useHashTab'
import type { SettingsTab, TabKey } from '../../src/types'

afterEach(() => {
  window.location.hash = ''
})

/** Mountet das Composable in einer Minimal-Komponente (für onMounted/onUnmounted). */
function mountHashTab(): {
  tab: Ref<TabKey>
  settingsTab: Ref<SettingsTab>
  unmount: () => void
} {
  let api!: { tab: Ref<TabKey>; settingsTab: Ref<SettingsTab> }
  const wrapper = mount(
    defineComponent({
      setup() {
        api = useHashTab()
        return () => null
      },
    }),
  )
  return { tab: api.tab, settingsTab: api.settingsTab, unmount: () => wrapper.unmount() }
}

describe('useHashTab', () => {
  it('liefert Default-Tab und Default-Reiter ohne Hash', () => {
    const { tab, settingsTab, unmount } = mountHashTab()
    expect(tab.value).toBe('assets')
    expect(settingsTab.value).toBe('appearance')
    unmount()
  })

  it('liest einen gültigen Tab aus dem Hash', () => {
    window.location.hash = '#/exchanges'
    const { tab, unmount } = mountHashTab()
    expect(tab.value).toBe('exchanges')
    unmount()
  })

  it('fällt bei unbekanntem Hash auf den Default zurück', () => {
    window.location.hash = '#/unbekannt'
    const { tab, unmount } = mountHashTab()
    expect(tab.value).toBe('assets')
    unmount()
  })

  it('schreibt Tab-Wechsel in den Hash', async () => {
    const { tab, unmount } = mountHashTab()
    tab.value = 'fx'
    await nextTick()
    expect(window.location.hash).toBe('#/fx')
    unmount()
  })

  it('parst den Settings-Reiter aus der Query', () => {
    window.location.hash = '#/settings?tab=environment'
    const { tab, settingsTab, unmount } = mountHashTab()
    expect(tab.value).toBe('settings')
    expect(settingsTab.value).toBe('environment')
    unmount()
  })

  it('fällt bei unbekanntem Reiter auf appearance zurück', () => {
    window.location.hash = '#/settings?tab=bogus'
    const { tab, settingsTab, unmount } = mountHashTab()
    expect(tab.value).toBe('settings')
    expect(settingsTab.value).toBe('appearance')
    unmount()
  })

  it('schreibt den Reiter als Query, wenn tab === settings', async () => {
    const { tab, settingsTab, unmount } = mountHashTab()
    tab.value = 'settings'
    settingsTab.value = 'links'
    await nextTick()
    expect(window.location.hash).toBe('#/settings?tab=links')
    unmount()
  })

  it('lässt die Query weg, wenn zu einem Arbeitsbereich gewechselt wird', async () => {
    window.location.hash = '#/settings?tab=links'
    const { tab, unmount } = mountHashTab()
    await nextTick()
    tab.value = 'assets'
    await nextTick()
    expect(window.location.hash).toBe('#/assets')
    unmount()
  })
})
