# Design: ETF-Extras vollständig nachtragen + aufklappbare Zeile

**Datum:** 2026-08-17
**Ticket:** Die Zerlegung in Tickets folgt aus dem Implementierungsplan —
Backend (Daten + Beschaffung) und Frontend (Schublade) sind getrennt
abnehmbar und werden getrennte Tickets.
**Scope:** Backend (DB, Provider, Modelle) + Frontend (Dashboard). Kein ux-foundation-Change.
**Bezug:** Baut auf T-09 (manuelle Kennzahlen) auf; Skill `ux-standards`
(aufklappbare Zeile, „Die Kennung öffnet die Zeile").

## Problem

Wer außerhalb von Österreich/Deutschland arbeitet, trägt Papiere ein, die
justETF nicht kennt — nicht-europäisches Domizil wird vom Provider bewusst
übersprungen (`is_european_isin`), und auch innerhalb Europas kann der Scrape
scheitern. Dann fehlen die ETF-Extras, und der Nutzer hat keine Möglichkeit,
sie beizusteuern.

Beim Nachmessen im Code ist die Lücke schmaler als vermutet, aber anders
gelagert:

**Die Währung hängt nicht an justETF.** `quote_service.py:127` nimmt
`raw.currency or resolved.currency` — yfinance zuerst. Wer ein Papier einträgt,
das yfinance kennt, bekommt eine Währung. Was fehlt, ist die Unterscheidung:
justETF liefert die **Fonds**währung (bei `IE00B4L5Y983` USD), angezeigt wird die
**Handels**währung (EUR an Xetra). Die Fondswährung dient heute nur als
Lückenfüller und geht sonst verloren.

**Tatsächlich fehlen sechs Felder** ohne justETF: `ter`, `volatility`,
`accumulating` — seit T-09 von Hand pflegbar — sowie `provider`, `replication`,
`fund_size`, die es nicht sind. `fund_domicile` wird gar nicht erst geholt,
obwohl `get_etf_overview` es liefert.

**Und die Tabelle ist am Anschlag.** Acht Kennzahlen als Spalten wären
unlesbar; StockPortfolio löst dasselbe Problem über eine aufklappbare Zeile.

## Lösung

Drei Teile: die Override-Tabelle wächst auf alle ETF-Extras, die Beschaffung
holt zwei bisher verworfene Felder, und gepflegt wird künftig ausschließlich in
einer aufklappbaren Zeile. Die Tabelle selbst bleibt, wie sie ist — nur ohne
Editoren.

### 1. Datenmodell

`instruments` bekommt zwei Spalten für Werte der Quelle:

| Spalte | Typ | Herkunft |
|---|---|---|
| `fund_domicile` | TEXT | justETF `fund_domicile` |
| `fund_currency` | TEXT | justETF `fund_currency` |

`instrument_overrides` bekommt fünf:

| Spalte | Typ |
|---|---|
| `provider` | TEXT |
| `replication` | TEXT |
| `fund_size` | REAL |
| `fund_domicile` | TEXT |
| `fund_currency` | TEXT |

**Migration:** `_migrate()` in `db.py` liest heute nur
`PRAGMA table_info(instruments)`. Dieselbe idempotente Schleife braucht es ein
zweites Mal für `instrument_overrides`. Bestehende Datenbanken ziehen beim
Start nach, wie schon bei `volatility`/`accumulating`.

**`OVERRIDE_FIELDS` wächst von drei auf acht** und trägt den Rest von selbst:
`apply_overrides`, `_with_overrides`, die Endpoint-Modelle und der
Modell-Wächter laufen bereits über diese Konstante. Nur `accumulating` behält
die Sonderbehandlung `_as_bool`; die Textfelder gehen unverändert durch.

**Validierung je Feld** — der Grund, Spalten statt einer generischen
Schlüssel/Wert-Tabelle zu nehmen:

| Feld | Regel |
|---|---|
| `ter` | ≥ 0, ≤ 5 (unverändert seit T-09) |
| `volatility` | ≥ 0, ≤ 500 (unverändert) |
| `fund_size` | ≥ 0, ≤ 2 000 000 (in Mio. EUR, also 2 Bio. — der größte Fonds weltweit liegt bei rund 1,5 Bio.) |
| `fund_currency` | genau drei Großbuchstaben (ISO 4217) |
| `provider`, `replication`, `fund_domicile` | freier Text, ≤ 100 Zeichen |

### 2. Beschaffung

In `justetf_provider.py`: `fund_domicile` wird gemappt, `EtfDetails` bekommt das
Feld. `fund_currency` wird ein eigenes Feld statt Lückenfüller.

**Der Währungs-Rückfall entfällt.** `quote_service.py:152` setzt heute
`response.currency = response.currency or details.currency`. Fällt yfinance
einmal ohne Währung aus, rutscht dort die Fondswährung in die Handelswährung —
bei `IE00B4L5Y983` stünde USD am Euro-Kurs. Zwei Begriffe, zwei Felder, kein
Übersprechen: Die Zeile wird ersatzlos gestrichen, `fund_currency` wird separat
gesetzt.

Nebenwirkung im Blick behalten: Bei Papieren, für die yfinance keine Währung
liefert, bleibt `currency` künftig leer, wo bisher die Fondswährung einsprang.
Von den fünf Papieren im laufenden Bestand ist keines betroffen.

### 3. Die Schublade

**Auslöser:** Symbol und Name der Zeile werden Schaltflächen — „Die Kennung
öffnet die Zeile" (ux-standards). Der Pfeil bleibt zusätzlich, für Tastatur und
Gewohnheit. Markiert wird zurückhaltend: gepunktete Linie beim Überfahren,
keine dauerhafte Unterstreichung.

**Zweispaltig**, wie `PositionDrilldown.vue` in StockPortfolio:

- **Links — pflegen:** die acht Kennzahlen. Die T-09-Regel gilt unverändert:
  Liefert die Quelle einen Wert, steht er da und ist gesperrt; fehlt er, ist das
  Feld offen. Der Titel nennt den Grund.
- **Rechts — nachlesen:** `source` (`yfinance` bzw. `yfinance+justetf`), der
  Zeitpunkt der letzten Beschaffung, und **warum** justETF nichts beigesteuert
  hat. Bei nicht-europäischer ISIN wird bewusst übersprungen — genau diese
  Erklärung fehlt dem Nutzer heute.

**Die Tabelle bleibt unverändert** — dieselben Spalten, dieselbe Reihenfolge,
nur ohne Inline-Editoren. Die fünf neuen Felder bekommen **keine** Spalten. Die
Zeilen-Knöpfe (JSON, eETF, Y!, Aktualisieren, Löschen) bleiben, wo sie sind.

**Ein verdecktes Feld behält eine Aktion: „Eigenen Wert entfernen".** Das ist
kein Nachtrag, sondern die Auflösung eines Widerspruchs. Der Anwendungsfall
dieses Features lautet: Quelle liefert nichts, der Mensch trägt acht Felder
nach. Kommt die Quelle später doch, wären nach der reinen T-09-Regel alle acht
Eingaben verdeckt und damit **gesperrt** — wegzubekommen nur noch per `curl`.
Bei einem Feld war das vertretbar, bei acht ist es ein Konstruktionsfehler.
Bearbeiten bleibt gesperrt (das war die Verwirrung, die T-09 auslöste),
Entfernen nicht. In der Tabellenzelle fehlte dafür der Platz, in der Schublade
steht der Wert der Quelle, daneben der eigene und daneben das Kreuz.

**Mobil** ändert sich wenig: Unter `md` ist die Tabelle bereits eine
Kartenliste, die Schublade wird der aufgeklappte Teil der Karte.

## Betroffene Einheiten

| Einheit | Was |
|---|---|
| `app/db.py` | zwei Spalten in `instruments`, fünf in `instrument_overrides`, `_migrate` auf beide Tabellen |
| `app/models.py` | `OVERRIDE_FIELDS` 3 → 8, `InstrumentOverrides` + fünf Felder mit Validierung, `QuoteResponse`/`InstrumentSummary` + `fund_domicile`/`fund_currency` |
| `app/repository.py` | `set_overrides`/`get_overrides` auf acht Felder, Instrument-Upsert um zwei Spalten |
| `app/providers/base.py`, `justetf_provider.py` | `fund_domicile` mappen, `fund_currency` als eigenes Feld |
| `app/services/quote_service.py` | Währungs-Rückfall streichen, zwei Felder durchreichen |
| `app/services/quote_cache.py` | `_from_cache` um zwei Felder; Vorrang-Wege wachsen über `OVERRIDE_FIELDS` von selbst |
| `dashboard/src/components/InstrumentsTable.vue` | Kennung öffnet die Zeile, Editoren raus |
| `dashboard/src/components/MetricValue.vue` | **neu** — zeigt Wert und Merkmal (Tabelle) |
| `dashboard/src/components/MetricEditor.vue` | **neu** — pflegt, sperrt, entfernt (Schublade); ersetzt `ManualMetric.vue` |
| `dashboard/src/components/InstrumentDrilldown.vue` | **neu** — der aufgeklappte Bereich |
| `dashboard/src/i18n/{de,en}.ts` | Beschriftungen der fünf neuen Felder, Herkunfts-Erklärung, Entfernen-Aktion |

`ManualMetric.vue` wird durch die beiden neuen Komponenten ersetzt: Sie kann
heute anzeigen **und** bearbeiten und hat seit der T-09-Nacharbeit einen
statischen Zweig. Aufgeteilt hat jede Komponente eine Aufgabe, und die
Sperrlogik steht an einer Stelle statt in zwei Zweigen einer Datei.

## Teststrategie (TDD)

**Backend**
- Migration ist idempotent und ergänzt beide Tabellen auf einer bestehenden DB.
- Alle acht Felder laufen durch `apply_overrides` **und** `_with_overrides`;
  die vorhandenen Routen-Tests wachsen über `OVERRIDE_FIELDS` mit.
- Validierung je neuem Feld, jeweils ein gültiger Grenzfall und ein ungültiger.
- `fund_domicile` wird gemappt; `fund_currency` landet **nicht** mehr in
  `currency` (Regressionstest für den gestrichenen Rückfall).

**Frontend**
- `MetricValue` zeigt den wirksamen Wert und das richtige Merkmal.
- `MetricEditor` sperrt nach der Regel, lässt ein verdecktes Feld aber
  entfernen.
- Schublade öffnet und schließt über Kennung und Pfeil, `aria-expanded` stimmt,
  `Escape` schließt.

**Im Browser**, nach Hausstandard gemessen statt geschätzt: Ausrichtung der
Spalten gegen ihre Köpfe, kein waagrechter Überhang bei 375 px, Schublade in
beiden Breiten, Kontrast der neuen Flächen je Theme.

## Bewusst NICHT im Scope (YAGNI)

- **Holdings, Länder- und Sektorgewichte.** `get_etf_overview` liefert sie
  bereits mit (10/10/13 Einträge), und sie kosten nichts extra
  (`expand_allocations` ~0,04 s). Sie anzuzeigen ist ein eigener Schnitt mit
  eigener Darstellungsfrage.
- **`index`, `investment_focus`, `inception_date`, `legal_structure`,
  `sustainability`, `currency_hedged`, `description`.** Ebenfalls vorhanden,
  aber nicht verlangt.
- **Zeilen-Knöpfe in die Schublade verschieben.** Ausdrücklich abgelehnt.
- **`load_overview` als ETF-Suche.** Die Library kann eine filterbare Tabelle
  aller ETFs liefern — ein eigenes Feature, kein Teil dieses Designs.
