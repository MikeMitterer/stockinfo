# Design: Devisen-Panel-UX (T-06)

**Datum:** 2026-08-13
**Ticket:** `_tickets/T-06-fx-panel-ux.md`
**Scope:** Frontend (Dashboard). Kein Backend-Change — `/fx` liefert bereits alle
nötigen Daten (`rate`, `quote_time`, `source`, `stale`).

## Problem

Der Devisen-Tab (`#/fx`, `FxPanel.vue`) hat vier vom Nutzer gemeldete Schwächen:

1. Währungen werden als Freitext (3-Buchstaben-Code) eingegeben — fehleranfällig,
   keine Übersicht der verfügbaren Währungen.
2. Der Wechselkurs wird mit voller Float-Präzision angezeigt
   (`1.1527377367019653`) statt lesbar gerundet.
3. Die Kurszeit steht als roher ISO-String (`2026-08-13T07:41:13.759837+00:00`).
4. Dieser lange String bricht in der schmalen Spalte um.

## Lösung — Überblick

Reine UI-Überarbeitung von `FxPanel.vue`, gespeist aus bereits vorhandenen Daten.
Keine neue API, keine hartkodierte Währungsliste.

### 1. Währungs-Dropdowns statt Freitext

- Basis- und Zielwährung je ein natives `<select>`.
- Optionsliste = Währungen aus `GET /exchanges`, **dedupliziert**, **sortiert**,
  mit Normalisierung **`GBp → GBP`** (die Börsen-Tabelle führt London als `GBp`
  = Pence; das ist keine FX-Währung).
- Ergebnisliste (Stand heute):
  `AUD, BRL, CAD, CHF, CNY, DKK, EUR, GBP, HKD, ILS, INR, JPY, KRW, MXN, NOK,
  PLN, SEK, SGD, TWD, USD, ZAR`.
- **Datenfluss:** `App.vue` lädt `/exchanges` bereits via `useExchanges`. Eine
  dort berechnete `currencies`-Liste (computed) wird als Prop an `FxPanel`
  gereicht — analog zu `ExchangesPanel :data`. Kein zusätzlicher Fetch in
  `FxPanel`, keine hartkodierte Liste (bleibt *eine Quelle der Wahrheit*,
  konsistent mit T-02).
- Defaults: `EUR` → `USD`. Sind diese Codes nicht in der Liste (leeres
  `/exchanges`), fällt das Select auf die erste verfügbare Währung zurück.
- ⇄-Swap-Button: Verhalten unverändert (tauscht die beiden Auswahlwerte).
- Fallback bei leerer/fehlender Exchanges-Liste: Dropdowns bleiben leer, aber die
  Umrechnung ist ohne Auswahl ohnehin nicht auslösbar — kein Crash.

### 2. Rate auf 3 Nachkommastellen

- Anzeige:
  `rate.toLocaleString(locale, { maximumFractionDigits: 3 })`
  (folgt dem bestehenden Formatmuster in `InstrumentsTable.vue`).
- Der **rohe** Wert bleibt im `result`-Objekt unverändert und wird zusätzlich als
  `title`-Attribut (Hover-Tooltip) an der Rate-Zeile ausgegeben — volle Präzision
  bleibt auf Nachfrage sichtbar.
- **Bewusster Trade-off:** Bei sehr kleinen Kursen (z.B. `1 JPY = 0,0058 EUR`)
  zeigen 3 Nachkommastellen `0,006`. Das entspricht der Nutzer-Anforderung; der
  Tooltip fängt den Präzisionsverlust ab.

### 3. Kurszeit lesbar + kein Umbruch

- Neuer, wiederverwendbarer Helper `utils/datetime.ts`:
  `formatDateTime(iso: string, locale: string): string` auf Basis von
  `Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' })`
  (z.B. de: „13. Aug. 2026, 09:41"). Ungültiger/leerer Input → Rückgabe des
  Rohwerts (defensiv, kein Throw).
- `FxPanel` zeigt `formatDateTime(result.quote_time, locale)` statt des ISO-Strings.
- Styling: `white-space: nowrap` auf dem Wert; das formatierte Datum ist kurz
  genug, der Umbruch entfällt.
- `stale`-Badge (aktuell/veraltet): unverändert.

### 4. Internationalisierung (MUST)

- **Alle** UI-Texte über vue-i18n in `i18n/de.ts` **und** `i18n/en.ts` —
  Labels („Basis"/„Ziel" bzw. deren aria-labels, „zuletzt aktualisiert" o.ä.),
  Platzhalter, aria-Labels. **Kein** hartkodierter String in Template oder Code.
- Währungscodes selbst sind Daten (keine Übersetzung).
- Zahlen-/Datumsformat sind locale-abhängig (`locale` aus vue-i18n).

## Betroffene Einheiten

| Datei | Änderung |
|---|---|
| `utils/datetime.ts` | **neu** — `formatDateTime(iso, locale)` |
| `components/FxPanel.vue` | Dropdowns, Rate-Formatierung, Datums-Formatierung, `currencies`-Prop, nowrap |
| `App.vue` | computed `currencies` aus `exchanges`; als Prop an `FxPanel` |
| `i18n/de.ts`, `i18n/en.ts` | neue/angepasste Labels |
| `tests/utils/datetime.spec.ts` | **neu** |
| `tests/components/FxPanel.spec.ts` | Dropdown-Rendering, GBp→GBP, 3-Stellen-Rate, formatierte Kurszeit |

Kein Backend-Change. `useFx.ts` bleibt unverändert.

## Teststrategie (TDD)

- **`utils/datetime.spec.ts`:** bekannter ISO-Input → erwartetes lokalisiertes
  Format (locale `de`); ungültiger Input → Rohwert zurück.
- **`FxPanel.spec.ts`:**
  - Dropdowns rendern genau die (deduplizierten, sortierten) Währungen aus den
    übergebenen Exchanges; `GBp` erscheint als `GBP`, nicht doppelt.
  - Nach `convert` wird die Rate mit ≤3 Nachkommastellen dargestellt (kein
    `…7019653`), Tooltip trägt den Rohwert.
  - Kurszeit erscheint formatiert, nicht als roher ISO-String.
- Bestehende Tests bleiben grün.

## Verifikation (Human/AI)

Die Verify-Matrix in `_tickets/T-06-fx-panel-ux.md` (#1–#6) ist die
Abnahme-Checkliste — nach Umsetzung im Browser (`#/fx`) durchgehen.

## Bewusst NICHT im Scope (YAGNI)

- Kein Freitext-Fallback für exotische Währungen (nicht angefordert).
- Keine eigene FX-Währungsliste im Backend / keine Paare außerhalb der
  Börsen-Währungen.
- Keine Historie/Charts für Devisen.
