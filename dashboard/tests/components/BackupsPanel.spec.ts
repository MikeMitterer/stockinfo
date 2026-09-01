import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiClient } from '../../src/api/client'
import BackupsPanel from '../../src/components/BackupsPanel.vue'
import { i18n } from '../../src/i18n'
import type { BackupList } from '../../src/types'

/**
 * Die Sicherungsansicht. Geprüft wird der gerenderte Text und der ausgelöste
 * Aufruf, nicht die inneren Klassen von Naive UI.
 *
 * ===== ==================================================================
 * `#11` Auch unpassende Sicherungen sind sichtbar, mit ihrem Grund
 * `#12` Der Neustart steht im Text, **bevor** der Aufruf abgeschickt wird
 * `#8`  Ein ausstehender Neustart bleibt sichtbar; ein Fehler ebenso
 * ===== ==================================================================
 */
const FITTING = {
  name: 'stockinfo-20260901T120000000Z-abcdef123456.db',
  created_at: '2026-09-01T12:00:00Z',
  size: 90112,
  fingerprint: 'abcdef123456',
  compatible: true,
  reason: '',
}
const FOREIGN = {
  name: 'stockinfo-20260831T120000000Z-999999999999.db',
  created_at: '2026-08-31T12:00:00Z',
  size: 81920,
  fingerprint: '999999999999',
  compatible: false,
  reason: 'quotes: dort [yaml-file], hier [yfinance]',
}

function listing(extra: Partial<BackupList> = {}): BackupList {
  return {
    fingerprint: 'abcdef123456',
    pending_restore: null,
    restore_error: '',
    backups: [FITTING, FOREIGN],
    ...extra,
  }
}

/**
 * Mountet die Ansicht mit **eingefangenem** Teleport: Sonst läge der Dialog am
 * Dokumentkörper, und jede Zusage über ihn hinge am globalen DOM.
 */
function mountPanel() {
  return mount(BackupsPanel, {
    global: { plugins: [i18n], stubs: { teleport: true } },
  })
}

/** Der Bestätigungsknopf des Dialogs. */
function confirmButton(wrapper: ReturnType<typeof mountPanel>) {
  return wrapper.findAll('button').find((candidate) => /Vormerken|Schedule/.test(candidate.text()))
}

/** Klickt im Dialog auf „Vormerken". */
async function confirmDialog(wrapper: ReturnType<typeof mountPanel>): Promise<void> {
  const button = confirmButton(wrapper)
  expect(button, 'der Bestätigungsknopf fehlt').toBeTruthy()
  await button?.trigger('click')
  await flushPromises()
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
  vi.restoreAllMocks()
})

describe('BackupsPanel', () => {
  it('zeigt auch die unpassende Sicherung — mit ihrem Grund', async () => {
    // **`#11`.** Eine auszublenden hieße, jemanden nach einer Datei suchen zu
    // lassen, die er im Verzeichnis liegen sieht.
    vi.spyOn(apiClient, 'get').mockResolvedValue(listing())

    const wrapper = mountPanel()
    await flushPromises()

    const text = wrapper.text()
    expect(text).toContain('quotes: dort [yaml-file], hier [yfinance]')
    expect(text).toContain('passt zur laufenden Quellenlage')
    expect(wrapper.findAll('tbody tr')).toHaveLength(2)
    // **Die Zeitspalte muss etwas enthalten** — eine leere Zelle fällt nur
    // auf, wenn jemand hinsieht.
    const firstCell = wrapper.findAll('tbody tr')[0].findAll('td')[0].text()
    expect(firstCell).not.toBe('')
    expect(firstCell).toMatch(/2026/)
  })

  it('nennt den Neustart, bevor der Aufruf hinausgeht', async () => {
    // **`#12`.** Geprüft am gerenderten Text und daran, dass bis dahin **kein**
    // POST gelaufen ist — eine Ansage nach der Entscheidung ist keine.
    vi.spyOn(apiClient, 'get').mockResolvedValue(listing())
    const post = vi.spyOn(apiClient, 'post').mockResolvedValue({})

    const wrapper = mountPanel()
    await flushPromises()
    await wrapper.findAll('tbody button')[0].trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Neustart')
    expect(post).not.toHaveBeenCalled()
  })

  it('sperrt die Bestätigung, solange das Übergehen nicht gesetzt ist', async () => {
    // **Der Dialog weiß schon, dass die Sicherung nicht passt.** Den Aufruf
    // trotzdem hinauszulassen hieße, den Benutzer erst aus einem `409`
    // erfahren zu lassen, was hier längst dasteht.
    vi.spyOn(apiClient, 'get').mockResolvedValue(listing())
    const post = vi.spyOn(apiClient, 'post').mockResolvedValue({})

    const wrapper = mountPanel()
    await flushPromises()
    await wrapper.findAll('tbody button')[1].trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Trotzdem einspielen')
    expect(confirmButton(wrapper)?.attributes('disabled')).toBeDefined()

    await confirmDialog(wrapper)
    expect(post, 'der Aufruf ging trotz gesperrter Aktion hinaus').not.toHaveBeenCalled()
  })

  it('gibt die Bestätigung mit dem Haken frei — dann mit `force`', async () => {
    vi.spyOn(apiClient, 'get').mockResolvedValue(listing())
    const post = vi.spyOn(apiClient, 'post').mockResolvedValue({})
    const wrapper = mountPanel()
    await flushPromises()
    await wrapper.findAll('tbody button')[1].trigger('click')
    await wrapper.find('.n-checkbox').trigger('click')
    await flushPromises()

    expect(confirmButton(wrapper)?.attributes('disabled')).toBeUndefined()
    await confirmDialog(wrapper)

    expect(post.mock.calls[0][0]).toContain('force=true')
  })

  it('trägt ein gesetztes Übergehen nicht in den nächsten Dialog', async () => {
    // **Der Schutz sitzt im Öffnen, nicht im Anfangswert.** Wer einmal
    // übergangen hat und danach eine passende Sicherung wählt, spielte sonst
    // wieder mit `force` ein — dort gibt es den Haken nicht.
    vi.spyOn(apiClient, 'get').mockResolvedValue(listing())
    const post = vi.spyOn(apiClient, 'post').mockResolvedValue({})

    const wrapper = mountPanel()
    await flushPromises()
    await wrapper.findAll('tbody button')[1].trigger('click')
    await wrapper.find('.n-checkbox').trigger('click')
    await flushPromises()
    const cancel = wrapper
      .findAll('button')
      .find((candidate) => /Abbrechen|Cancel/.test(candidate.text()))
    await cancel?.trigger('click')
    await flushPromises()

    await wrapper.findAll('tbody button')[0].trigger('click')
    await flushPromises()
    await confirmDialog(wrapper)

    expect(post.mock.calls[0][0]).not.toContain('force')
  })

  it('lässt den Fehler vor einem ausstehenden Neustart stehen', async () => {
    // Die Rangfolge gehört in die Ansicht und nicht in eine Annahme über den
    // Server: Steht beides da, ist der Fehler die jüngere und wichtigere
    // Auskunft — nach ihm folgt kein Versuch mehr.
    vi.spyOn(apiClient, 'get').mockResolvedValue(
      listing({ pending_restore: FITTING.name, restore_error: 'Zielmedium voll' }),
    )

    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('Das Einspielen ist gescheitert')
    expect(wrapper.text()).toContain('Zielmedium voll')
    expect(wrapper.text()).not.toContain('Ein Neustart steht aus')
  })

  it('lädt nach dem Anlegen den Serverzustand neu', async () => {
    // Anlegen verdrängt die älteste; ein fortgeschriebener Eigenstand zeigte
    // danach etwas anderes als die Instanz.
    const get = vi.spyOn(apiClient, 'get').mockResolvedValue(listing())
    vi.spyOn(apiClient, 'post').mockResolvedValue({})

    const wrapper = mountPanel()
    await flushPromises()
    expect(get).toHaveBeenCalledTimes(1)

    await wrapper.find('button').trigger('click')
    await flushPromises()

    expect(get).toHaveBeenCalledTimes(2)
  })

  it('nennt den Grund aus dem Katalog und lädt danach nicht nach', async () => {
    // **Ein Nachladen im Fehlerfall löschte genau die Meldung**, für die der
    // Aufruf gerade gescheitert ist — der Benutzer sähe einen Klick ohne
    // Wirkung und ohne Grund. Der Text kommt aus dem Katalog, nicht aus
    // `String(err)`: Sonst stünde in der englischen Oberfläche ein deutscher.
    for (const [locale, expected] of [
      ['de', 'Sicherung fehlgeschlagen'],
      ['en', 'Backup failed'],
    ] as const) {
      i18n.global.locale.value = locale
      const get = vi.spyOn(apiClient, 'get').mockResolvedValue(listing())
      vi.spyOn(apiClient, 'post').mockRejectedValue(new Error('boom'))

      const wrapper = mountPanel()
      await flushPromises()
      await wrapper.find('button').trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain(expected)
      expect(wrapper.text(), 'der rohe Fehlertext steht da').not.toContain('boom')
      expect(get, 'nach dem Fehlschlag wurde nachgeladen').toHaveBeenCalledTimes(1)
      vi.restoreAllMocks()
    }
  })

  it('nennt auch ein gescheitertes Wiederherstellen beim Namen', async () => {
    vi.spyOn(apiClient, 'get').mockResolvedValue(listing())
    vi.spyOn(apiClient, 'post').mockRejectedValue(new Error('boom'))
    const wrapper = mountPanel()
    await flushPromises()
    await wrapper.findAll('tbody button')[0].trigger('click')
    await flushPromises()
    await confirmDialog(wrapper)

    expect(wrapper.text()).toContain('Wiederherstellen fehlgeschlagen')
  })

  it('zeigt einen ausstehenden Neustart', async () => {
    // **`#8`, UI-Halbsatz.** Eine Ansage nur in der Antwort sieht nach dem
    // Neuladen niemand mehr.
    vi.spyOn(apiClient, 'get').mockResolvedValue(
      listing({ pending_restore: FITTING.name }),
    )

    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('Ein Neustart steht aus')
    expect(wrapper.text()).toContain(FITTING.name)
  })

  it('übersetzt beide Sprachen und lässt keinen Schlüssel roh stehen', async () => {
    // Ein fehlender Schlüssel fällt in der Oberfläche nur auf, wenn jemand
    // hinsieht — hier sieht der Test hin.
    vi.spyOn(apiClient, 'get').mockResolvedValue(listing())

    for (const [locale, expected] of [
      ['de', 'Sicherungen der Datenbank'],
      ['en', 'Database backups'],
    ] as const) {
      i18n.global.locale.value = locale
      const wrapper = mountPanel()
      await flushPromises()
      expect(wrapper.text()).toContain(expected)
      expect(wrapper.text()).not.toContain('backups.')
    }
  })
})
