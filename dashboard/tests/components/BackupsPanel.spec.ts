import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiClient } from '../../src/api/client'
import BackupsPanel from '../../src/components/BackupsPanel.vue'
import { i18n } from '../../src/i18n'
import type { BackupList } from '../../src/types'

/**
 * Die Sicherungsansicht.
 *
 * Geprüft wird der gerenderte Text und der ausgelöste Aufruf — nicht die
 * inneren Klassen von Naive UI. Die Zusagen stammen aus der Verify-Matrix:
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
 * Mountet die Ansicht mit **eingefangenem** Teleport.
 *
 * Naive versetzt den Dialog an den Dokumentkörper; ohne diesen Stub läge er
 * außerhalb des Wrappers, und jede Zusage über ihn müsste am globalen DOM
 * hängen — samt der Reste, die ein vorheriger Fall dort liegen lässt.
 */
function mountPanel() {
  return mount(BackupsPanel, {
    global: { plugins: [i18n], stubs: { teleport: true } },
  })
}

/** Klickt im Dialog auf „Vormerken". */
async function confirmDialog(wrapper: ReturnType<typeof mountPanel>): Promise<void> {
  const button = wrapper
    .findAll('button')
    .find((candidate) => /Vormerken|Schedule/.test(candidate.text()))
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
    // **Die Zeitspalte muss etwas enthalten.** Sie stand im Browser leer, weil
    // `d()` ein benanntes Format braucht, das der Katalog nicht führt — im
    // Test fiel das nicht auf, weil niemand hinsah.
    const ersteZelle = wrapper.findAll('tbody tr')[0].findAll('td')[0].text()
    expect(ersteZelle).not.toBe('')
    expect(ersteZelle).toMatch(/2026/)
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

  it('verlangt für eine unpassende Sicherung eine ausdrückliche Handlung', async () => {
    // Ohne den Haken geht der Aufruf **ohne** `force` hinaus und wird vom
    // Backend mit `409` abgelehnt — das Übergehen ist eine Entscheidung des
    // Benutzers, keine Voreinstellung der Ansicht.
    vi.spyOn(apiClient, 'get').mockResolvedValue(listing())
    const post = vi.spyOn(apiClient, 'post').mockResolvedValue({})

    const wrapper = mountPanel()
    await flushPromises()
    await wrapper.findAll('tbody button')[1].trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Trotzdem einspielen')
    expect(wrapper.find('.n-checkbox').exists(), 'die Force-Handlung fehlt').toBe(true)
    expect(post).not.toHaveBeenCalled()

    // **Ohne Zutun kein `force`.** Der Haken sichtbar zu machen genügt nicht —
    // steht er vorbelegt, geht das Übergehen ungefragt hinaus, und der
    // Benutzer hat nie entschieden.
    await confirmDialog(wrapper)

    expect(post).toHaveBeenCalledTimes(1)
    expect(post.mock.calls[0][0]).not.toContain('force')
  })

  it('übergeht die Quellenlage erst, wenn der Haken gesetzt ist', async () => {
    vi.spyOn(apiClient, 'get').mockResolvedValue(listing())
    const post = vi.spyOn(apiClient, 'post').mockResolvedValue({})

    const wrapper = mountPanel()
    await flushPromises()
    await wrapper.findAll('tbody button')[1].trigger('click')
    await flushPromises()
    await wrapper.find('.n-checkbox').trigger('click')
    await flushPromises()
    await confirmDialog(wrapper)

    expect(post.mock.calls[0][0]).toContain('force=true')
  })

  it('trägt ein gesetztes Übergehen nicht in den nächsten Dialog', async () => {
    // **Der eigentliche Schutz sitzt im Öffnen, nicht im Anfangswert.** Wer
    // einmal übergangen hat und danach eine passende Sicherung wählt, würde
    // sonst wieder mit `force` einspielen — ohne es zu wollen und ohne es zu
    // sehen, denn bei einer passenden Sicherung gibt es den Haken gar nicht.
    vi.spyOn(apiClient, 'get').mockResolvedValue(listing())
    const post = vi.spyOn(apiClient, 'post').mockResolvedValue({})

    const wrapper = mountPanel()
    await flushPromises()
    await wrapper.findAll('tbody button')[1].trigger('click')
    await wrapper.find('.n-checkbox').trigger('click')
    await flushPromises()
    const abbrechen = wrapper
      .findAll('button')
      .find((candidate) => /Abbrechen|Cancel/.test(candidate.text()))
    await abbrechen?.trigger('click')
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
    expect(wrapper.text()).not.toContain('Ein Neustart steht aus')
  })

  it('lädt nach dem Anlegen den Serverzustand neu', async () => {
    // Anlegen verdrängt die älteste; eine Ansicht, die ihren eigenen Stand
    // fortschreibt, zeigt danach etwas anderes als die Instanz.
    const get = vi.spyOn(apiClient, 'get').mockResolvedValue(listing())
    vi.spyOn(apiClient, 'post').mockResolvedValue({})

    const wrapper = mountPanel()
    await flushPromises()
    expect(get).toHaveBeenCalledTimes(1)

    await wrapper.find('button').trigger('click')
    await flushPromises()

    expect(get).toHaveBeenCalledTimes(2)
  })

  it('zeigt einen ausstehenden Neustart', async () => {
    // **`#8`, UI-Halbsatz.** Eine Ansage, die nur einmal in einer Antwort
    // stand, sieht nach dem Neuladen der Seite niemand mehr.
    vi.spyOn(apiClient, 'get').mockResolvedValue(
      listing({ pending_restore: FITTING.name }),
    )

    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('Ein Neustart steht aus')
    expect(wrapper.text()).toContain(FITTING.name)
  })

  it('zeigt einen gescheiterten Tausch statt eines ausstehenden Neustarts', async () => {
    // Nach einem Fehler folgt kein Versuch mehr — dann steht dort nichts aus.
    vi.spyOn(apiClient, 'get').mockResolvedValue(
      listing({ restore_error: `${FITTING.name}: OSError: Zielmedium voll` }),
    )

    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('Das Einspielen ist gescheitert')
    expect(wrapper.text()).toContain('Zielmedium voll')
    expect(wrapper.text()).not.toContain('Ein Neustart steht aus')
  })

  it('übersetzt beide Sprachen und lässt keinen Schlüssel roh stehen', async () => {
    // Das `analysis.role.`-Muster aus T-46: Ein fehlender Schlüssel fällt in
    // der Oberfläche nur auf, wenn jemand hinsieht — hier sieht der Test hin.
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
