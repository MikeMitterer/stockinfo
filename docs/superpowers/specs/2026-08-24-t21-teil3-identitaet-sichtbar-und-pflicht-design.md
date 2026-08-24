# T-21 Teil 3 — Identität sichtbar machen und im Vertrag verlangen

**Datum:** 2026-08-24 · **Ticket:** `_tickets/T-21-identitaet-mic-und-ticker.md` ·
**Branch:** `t-21d-offene-zuordnungen` · **Status:** entworfen, nicht umgesetzt

## Worum es geht

Teil 1 hat die kanonische Identität `(ticker, mic)` ins Schema gebracht, Teil 2
das Anlegen neuer Papiere darauf umgestellt. Teil 3 schließt das Ticket ab: Was
sich nicht zuordnen lässt, wird **sichtbar**, und der Weg, auf dem unzuordenbare
Zeilen überhaupt entstehen, wird im **Vertrag** geschlossen.

Der ursprüngliche Zuschnitt sah eine Handzuordnung über die Oberfläche vor
(Verify `#2c`) und dafür einen eigenen `identity_status`, den der automatische
Weg nicht anfasst (Frage aus Review-Runde 3). Beides entfällt — siehe
„Entscheidungen".

## Ausgangslage, gemessen

Offene Zuordnungen entstehen aus zwei Quellen, nicht aus einer:

| Quelle | Wann | Heilt sich selbst? |
|---|---|---|
| Migration (`app/db.py:277`) | beim Start, offline, Altbestand | ja, sobald eine ISIN-Auflösung läuft |
| Symbolweg (`app/services/quote_service.py:179`) | laufend, bei jedem suffixlosen Symbol | **nein** |

Belegt mit einer Wegwerf-Sonde gegen eine frische Datenbank: Eine über
`GET /quote?symbol=AAPL` angelegte Zeile bleibt bei jedem weiteren Abruf offen.
Der Grund steht im Kommentar von `get_quote_for_known` selbst — *„der Scheduler
löst nichts auf, er holt nur Kurse."* Die Auffrischung zieht die Zuordnung aus
`split_symbol(symbol)`, und das liefert für `AAPL` dauerhaft `(None, None)`.

Der ISIN-Weg dagegen liefert immer eine vollständige Identität oder einen
definierten Fehler. Gemessen mit `DEFAULT_EXCHANGE=XETR` gegen die echte Kette:

| ISIN | `STRICT_EXCHANGE=false` | `STRICT_EXCHANGE=true` |
|---|---|---|
| `IE00B4L5Y983` | `EUNL.DE` → `EUNL`/`XETR` | gleich |
| `US0378331005` | `APC.DE` → `APC`/`XETR` | gleich |
| `US9229087690` | `VTI` → `VTI`/`ARCX` (Yahoo-Fallback) | `NotFound` (404) |

## Entscheidungen

**1. Die Handzuordnung entfällt** (Verify `#2c` gestrichen, Entscheidung Mike).
Statt offene Zeilen nachträglich von Hand zu reparieren, entstehen sie gar nicht
erst: Der Symbolweg verlangt künftig die vollständige Kombination. Damit
entfällt auch die Statusfrage aus Runde 3 — einen Status, den der automatische
Weg nicht anfasst, braucht es nur, *weil* es manuelle Zuordnungen gibt.
`identity_status` bleibt zweiwertig.

**2. Der Migrationspfad wird nicht eng gesehen** (Entscheidung Mike). Was sich
einfach migrieren lässt, wird migriert; der Rest bleibt offen und bekommt eine
verständliche Meldung. Kein Reparaturwerkzeug für Altbestand.

**3. Bewusste Umkehr gegenüber Teil 2.** Teil 2 hat den Symbolweg absichtlich
nachsichtig gelassen; der Kommentar in `quote_service.py` argumentiert wörtlich
dagegen, die Auskunft zu verweigern, weil das *„eine Abfrage wegnähme, die es
heute gibt"*. Diese Entscheidung wird hier umgedreht. Das ist keine Drift,
sondern eine Abwägung mit neuem Wissen: Die weggenommene Abfrage ist genau die,
die dauerhaft unzuordenbare Zeilen erzeugt. Der Parameter ist zudem seit jeher
als *„Vollständiges Yahoo-Symbol inkl. Suffix"* dokumentiert — suffixlose
Symbole waren nie zugesagt, sie wurden nur angenommen.

**4. `core_version` steigt auf `2.0.0`** (Entscheidung Mike). Eine Anfrage, die
heute 200 liefert, liefert künftig 400. Nach der Regel im Artefakt
(*„Pflichtfeld entfernt oder unverträglich geändert"*) ist das ein Major, auch
wenn die betroffene Form nie dokumentiert war. Die Alternative — ein Minor mit
der Begründung, suffixlose Symbole seien nie zugesagt gewesen — wurde verworfen:
Ein Konsument, dessen Aufruf bricht, hat von dieser Begründung nichts.

## Die Pflicht-Kombinationen für den Benutzer

Am Ende muss immer `(kanonischer Ticker, echter MIC)` herauskommen. Drei Wege
führen dorthin:

| Weg | Pflicht | Woher `(ticker, mic)` kommt | ISIN nötig? |
|---|---|---|---|
| **1 — ISIN** `GET /quote/{isin}` | ISIN | StockInfo löst auf, Vorzugsbörse entscheidet | ist der Weg |
| **2 — Symbol mit bekanntem Suffix** `GET /quote?symbol=EUNL.DE` | Symbol | Zerlegung: `EUNL` + `.DE` → `XETR` | nein |
| **3 — Symbol + MIC** `GET /quote?symbol=AAPL&mic=XNAS` | **beides** | direkt vom Aufrufer | nein |

Ergänzende Regeln:

* **MIC wird Pflicht**, sobald das Symbol keinen in `EXCHANGES` bekannten Suffix
  hat. Er muss ein echter MIC sein: `mic=US` wird abgelehnt, weil `US` in
  `COLLECTOR_CODES` steht und offenlässt, ob NYSE oder NASDAQ gemeint ist.
* **Die ISIN ist für keinen Kurs Pflicht.** Sie ist aber Voraussetzung für die
  ETF-Anreicherung über justETF — Weg 2 und 3 liefern Kurse ohne TER,
  Fondsgröße und Thesaurierung.
* **Nicht kanonische Ticker gehen auf keinem Weg außer 1.** `is_canonical_ticker`
  lässt nur `[A-Z0-9]` zu; `BRK-B`, `BRK/B` und `BRK.B` sind drei Schreibweisen
  desselben Papiers. Ein mitgegebener MIC rettet das nicht — `symbol=BRK-B&mic=XNYS`
  bleibt abgelehnt. Für solche Papiere liefert die ISIN die kanonische
  Schreibweise mit.
* **Widerspruch ist ein Fehler.** `symbol=EUNL.DE&mic=XLON` — Suffix sagt Xetra,
  Parameter sagt London — führt zu 400 mit benanntem Widerspruch. Einen der
  beiden gewinnen zu lassen wäre genau das Raten, das dieses Ticket abschafft.
* **Mit `mic` muss das Symbol der reine Ticker sein.** `symbol=GOLD.SG&mic=XSTU`
  wird abgelehnt: `.SG` ist kein bekanntes Suffix, also bleibt `GOLD.SG` als
  Ticker stehen — und der ist wegen des Punktes nicht kanonisch. Richtig ist
  `symbol=GOLD&mic=XSTU`. Ein unbekanntes Suffix bei einem gesetzten `mic`
  stillschweigend abzuschneiden hieße raten: In `EUNL.DE` trennt der Punkt die
  Börse ab, in `BRK.B` die Anteilsklasse, und von außen ist beides dasselbe
  Zeichen. Der Fehlertext nennt die richtige Form.

## Was gebaut wird

### A. Der Vertrag am Symbolweg

`GET /quote` bekommt einen optionalen Query-Parameter `mic`. Die Prüfung sitzt
vor dem Service, im Router beziehungsweise in `app/routers/validation.py`, wo
die übrigen Eingabeprüfungen schon liegen.

Ablauf: Symbol normalisieren → `split_symbol` → bekanntes Suffix? Dann muss ein
mitgegebener `mic` dazu passen, sonst 400. Kein bekanntes Suffix? Dann ist `mic`
Pflicht, sonst 400. Der 400er nennt beide Auswege wörtlich.

### B. Stuttgart in die Börsentabelle

`"XSTU": ExchangeDef(".SG", "Stuttgart", "germany", "EUR")` in `EXCHANGES`.
`test_kein_suffix_ist_doppelt_vergeben` deckt die Kollisionsfreiheit ab. Damit
löst sich `GOLD.SG` — der einzige offene Fall im echten Bestand — ohne
Handzuordnung, und jedes künftige Stuttgarter Papier gleich mit.

### C. Sichtbarkeit: zwei Zustände, nicht einer

`GET /instruments/identity` liefert beides:

1. **Offen** — `identity_status = legacy_unresolved`, mit **Grund** je Fall
   (`suffixlos`, `Suffix unbekannt`, `fremde Schreibweise`). Der Grund entsteht
   serverseitig aus `split_symbol` und `is_canonical_ticker`; im Dashboard ist
   er nicht rekonstruierbar. Deckt Verify `#2b`.
2. **Von der Vorzugsbörse abgewichen** — `mic != default_exchange`, mit dem MIC
   und der Währung beider Seiten: *erwartet `XETR` (EUR), tatsächlich `ARCX`
   (USD)*. Heute ist das nur die Logzeile `resolve_foreign_exchange`; im
   Dashboard sieht niemand, dass ein Papier in USD hereinkommt, obwohl XETR
   eingestellt ist. Das ist die Fehlerklasse, die im Depot weh tut.

**Keine Schemaänderung nötig.** Die Abweichung ist ableitbar: Die Zeile hat
`mic`, die Konfiguration hat `default_exchange`, und `EXCHANGES` kennt zu beiden
die Währung. Nichts wird zusätzlich gespeichert, nichts muss migriert werden.

### D. Dashboard

Eine Zeile im **Environment-Panel** — dort steht der Systemzustand schon als
Schlüssel/Wert-Liste (Version, DB-Pfad, TTLs, Vorzugsbörse). Zwei Zähler
(`Offene Zuordnungen`, `Abweichende Börse`), aufklappbar zur Detailliste. Kein
neuer Nav-Punkt: Beide Zustände sind selten und nichts, was man täglich ansieht.
Die Assets-Tabelle bleibt unberührt — Verify `#4`.

Texte über `vue-i18n` in `de.ts` und `en.ts`, wie im Rest der Oberfläche.

### E. Vertrag und Version

`listing_id` und `ticker_mic` wandern aus `planned` in den zugesagten Core.
`InstrumentSummary` bekommt `ticker`, `mic` und `listing_id`. `core_version`
geht `1.0.0` → `2.0.0`, Snapshot per
`UPDATE_CORE_SNAPSHOT=1 .venv/bin/pytest tests/test_contract_openapi.py -q`.

### F. Mitzuziehende Dokumentation

Zwei Stellen im Produktcode versprechen noch die gestrichene Handzuordnung und
werden mit der Umsetzung berichtigt — sonst steht im Code eine Zusage, die es
nicht mehr gibt:

* `app/exchanges.py:233` — *„Der Fall bleibt offen und sichtbar, bis ihn jemand
  von Hand zuordnet."*
* `tests/test_identity_intake_paths.py:129` — *„Teil 3 listet sie zur Zuordnung
  von Hand auf."*

Dazu der Kommentar in `get_quote_for_known`, der die alte Nachsicht des
Symbolwegs begründet, und die README-Zeile zu `GET /quote?symbol=…`.

## Testen

* **Vertrag am Symbolweg:** suffixloses Symbol ohne `mic` → 400 mit beiden
  Auswegen im Text; mit gültigem `mic` → 200 und Zeile entsteht `resolved`;
  `mic=US` → 400; Widerspruch Suffix/`mic` → 400; suffixbehaftetes Symbol ohne
  `mic` → unverändert 200.
* **Stuttgart:** Zerlegung `GOLD.SG` → `GOLD`/`XSTU` und die Rückrichtung, plus
  der bestehende Kollisionstest.
* **Sichtbarkeit:** offene Liste mit Grund je Fall; leere Liste bei sauberem
  Bestand; Abweichungsliste mit beiden Währungen; ein Papier an der
  Vorzugsbörse taucht **nicht** auf.
* **Vertrag:** der bestehende `test_contract_openapi.py` gegen den erneuerten
  Snapshot mit `core_version 2.0.0`.
* **Dashboard:** Vitest für das Panel, beide Zähler und der leere Zustand.
* **Smoke:** `_tickets/T-21c-smoke.sh` gegen einen laufenden Server auf eigenem
  Port — `GOLD.SG` vor und nach dem Börseneintrag, der 400er am Symbolweg, die
  beiden Listen.

## Was bewusst nicht gebaut wird

* **Handzuordnung über die Oberfläche** — siehe Entscheidung 1.
* **Ein eigener Status für manuelle Zuordnungen** — ohne Handzuordnung
  gegenstandslos.
* **Ein Reparaturwerkzeug für Altbestand** — siehe Entscheidung 2.
* **Eine gespeicherte Abweichungsmarkierung** — ableitbar, siehe C.

Taucht ein realer Fall auf, in dem ein Mensch eine **falsche** automatische
Zuordnung überschreiben muss, ist das ein eigenes Ticket. Das ist Korrektur,
nicht Erstzuordnung, und es ist heute durch nichts belegt.

## Prüfauflage an Codex

Die Streichung von `#2c` hängt an den beiden Messungen oben. Beide bitte
**eigenständig nachvollziehen**, nicht anhand dieser Zusammenfassung:

1. Dass eine über den Symbolweg ohne ISIN angelegte Zeile dauerhaft offen
   bleibt — `get_quote_for_known` löst nicht auf.
2. Dass der ISIN-Weg mit `DEFAULT_EXCHANGE=XETR` die Tabelle oben liefert,
   einschließlich `APC.DE` für Apple und des Yahoo-Fallbacks für VTI.

Ist eine davon falsch, fällt der Zuschnitt mit ihr.
