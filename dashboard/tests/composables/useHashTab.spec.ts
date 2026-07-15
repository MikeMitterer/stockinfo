import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import { defineComponent, nextTick, type Ref } from 'vue'

import { useHashTab } from '../../src/composables/useHashTab'
import type { TabKey } from '../../src/types'

afterEach(() => {
  window.location.hash = ''
})

/** Mountet das Composable in einer Minimal-Komponente (für onMounted/onUnmounted). */
function mountHashTab(): { active: Ref<TabKey>; unmount: () => void } {
  let active!: Ref<TabKey>
  const wrapper = mount(
    defineComponent({
      setup() {
        active = useHashTab()
        return () => null
      },
    }),
  )
  return { active, unmount: () => wrapper.unmount() }
}

describe('useHashTab', () => {
  it('liefert den Default-Tab ohne Hash', () => {
    const { active, unmount } = mountHashTab()
    expect(active.value).toBe('assets')
    unmount()
  })

  it('liest einen gültigen Tab aus dem Hash', () => {
    window.location.hash = '#/exchanges'
    const { active, unmount } = mountHashTab()
    expect(active.value).toBe('exchanges')
    unmount()
  })

  it('fällt bei unbekanntem Hash auf den Default zurück', () => {
    window.location.hash = '#/unbekannt'
    const { active, unmount } = mountHashTab()
    expect(active.value).toBe('assets')
    unmount()
  })

  it('schreibt Tab-Wechsel in den Hash', async () => {
    const { active, unmount } = mountHashTab()
    active.value = 'themes'
    await nextTick()
    expect(window.location.hash).toBe('#/themes')
    unmount()
  })
})
