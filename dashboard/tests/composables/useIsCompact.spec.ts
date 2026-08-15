import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, type Ref } from 'vue'

import { COMPACT_QUERY, useIsCompact } from '../../src/composables/useIsCompact'

/** Ersetzt window.matchMedia durch eine steuerbare Attrappe. */
function stubMatchMedia(matches: boolean) {
  const listeners = new Set<(e: MediaQueryListEvent) => void>()
  const mql = {
    matches,
    media: COMPACT_QUERY,
    addEventListener: (_: string, cb: (e: MediaQueryListEvent) => void) => listeners.add(cb),
    removeEventListener: (_: string, cb: (e: MediaQueryListEvent) => void) => listeners.delete(cb),
  }
  const spy = vi.fn().mockReturnValue(mql)
  vi.stubGlobal('matchMedia', spy)
  return {
    spy,
    /** Simuliert einen Breitenwechsel. */
    emit(next: boolean) {
      mql.matches = next
      listeners.forEach((cb) => cb({ matches: next } as MediaQueryListEvent))
    },
    listenerCount: () => listeners.size,
  }
}

function mountCompact(): { compact: Ref<boolean>; unmount: () => void } {
  let compact!: Ref<boolean>
  const wrapper = mount(
    defineComponent({
      setup() {
        compact = useIsCompact()
        return () => null
      },
    }),
  )
  return { compact, unmount: () => wrapper.unmount() }
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('useIsCompact', () => {
  it('fragt die md-Grenze ab (unter 768px)', () => {
    const mm = stubMatchMedia(false)
    const { unmount } = mountCompact()
    expect(mm.spy).toHaveBeenCalledWith('(max-width: 767.98px)')
    unmount()
  })

  it('liefert den Anfangszustand aus matchMedia', () => {
    stubMatchMedia(true)
    const { compact, unmount } = mountCompact()
    expect(compact.value).toBe(true)
    unmount()
  })

  it('reagiert auf einen Breitenwechsel', async () => {
    const mm = stubMatchMedia(false)
    const { compact, unmount } = mountCompact()
    expect(compact.value).toBe(false)
    mm.emit(true)
    expect(compact.value).toBe(true)
    unmount()
  })

  it('meldet den Listener beim Unmount wieder ab', () => {
    const mm = stubMatchMedia(false)
    const { unmount } = mountCompact()
    expect(mm.listenerCount()).toBe(1)
    unmount()
    expect(mm.listenerCount()).toBe(0)
  })
})
