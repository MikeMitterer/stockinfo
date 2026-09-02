# T-59 · Der Titel eines Hinweises friert die Sprache vom Seitenaufbau ein

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Dashboard) | offen | 30 min | ein Titel wird reaktiv statt einmalig ausgewertet | — |

- **Angelegt:** 2026-09-02, beim Wiederholungslauf zu **T-56** Punkt 5
- **Blockiert:** nichts. T-56 Punkt 5 ist **grün**; das hier ist ein
  Nebenbefund aus demselben Handgriff
- **Hängt ab von:** nichts

**Löst:** Wer die Sprache umstellt, ohne neu zu laden, liest englische
Fehlertexte unter einer deutschen Überschrift.

---

## Der gemessene Befund

Isolierte Instanz, Aufnahme von `KEINPAPIER.XX`. Zweimal derselbe Handgriff,
einmal mit Sprachwechsel **vor** dem Seitenaufbau, einmal **danach**:

| Sprache gesetzt | Titel | Text |
|---|---|---|
| **vor** dem Aufbau (`localStorage`, dann geladen) | `Error` | `Adding failed — The symbol has no exchange suffix …` |
| **nach** dem Aufbau (Umschalten in den Einstellungen) | **`Fehler`** | `Adding failed — The symbol has no exchange suffix …` |

Aus dem DOM gelesen, nicht vom Bild abgeschätzt:

```
n-notification-main__header  :: Fehler
n-notification-main__content :: Adding failed — The symbol has no exchange suffix …
```

## Die Ursache

`dashboard/src/components/AppDashboard.vue:115`:

```ts
notify(
  computed(() => source.value !== null),
  {
    title: t('errors.title'),          // einmal beim Aufbau ausgewertet
    type: 'error',
    content: () => source.value ?? '', // eine Funktion — wird neu ausgewertet
  },
)
```

`title` ist ein **Wert**, `content` eine **Funktion**. Der Text folgt der
Sprache deshalb, die Überschrift nicht. Beide Kataloge haben den Schlüssel
(`de.ts:323` `'Fehler'`, `en.ts:288` `'Error'`) — es fehlt keine Übersetzung,
sie wird nur zum falschen Zeitpunkt gelesen.

**Es ist kein i18n-Loch, sondern ein Reaktivitätsfehler.** Ein Test über die
Kataloge findet das nie: Beide sind vollständig.

## Was zu tun ist

`title` als Funktion übergeben, wie `content` es schon ist — sofern
`useNotifier` das annimmt. Ob es das tut, gehört gemessen, nicht angenommen;
falls nicht, ist die kleinere Änderung dort und nicht an der Aufrufstelle.

## Verify

| # | Where | Look for | Wer |
|---|---|---|---|
| **1** | Sprachwechsel **ohne** Neuladen, dann ein Fehler | Titel und Text stehen in derselben Sprache | KI |
| **2** | Gegenprobe | mit Sprache **vor** dem Aufbau bleibt es richtig — das ging vorher schon und darf nicht kaputtgehen | KI |
| **3** | Mutant | macht man `title` wieder zu einem Wert, wird ein Test rot | KI |
| **4** | Inventar | **alle** `notify`-Aufrufe geprüft, nicht nur dieser eine — aufgezählt, nicht gegriffen | KI |

Zeile `#4` ist der Punkt, an dem dieses Ticket scheitern kann: Es gibt
möglicherweise weitere Stellen mit demselben Muster. Sie werden aufgezählt,
nicht erraten.

## Nicht-Ziele

- Keine Änderung an `useNotifier` über das Nötige hinaus.
- Keine neuen Katalogtexte — es fehlt keiner.
- Keine Umstellung anderer `t()`-Aufrufe „vorsichtshalber". Was reaktiv sein
  muss, zeigt der Befund; der Rest bleibt.
