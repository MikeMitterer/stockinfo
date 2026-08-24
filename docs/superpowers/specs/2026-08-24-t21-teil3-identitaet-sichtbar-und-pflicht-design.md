# T-21 Teil 3 — Identität sichtbar machen und im Vertrag verlangen

**Datum:** 2026-08-24 · **Ticket:** `_tickets/T-21-identitaet-mic-und-ticker.md` ·
**Branch:** `t-21d-offene-zuordnungen` · **Status:** entworfen, **Runde 13** ·
**Vorlauf:** Runden 8, 9 und 10 haben je fünf bis sechs Befunde gebracht. Die
„Hoch"-Befunde waren durchweg Entwurfsfehler — genau dafür läuft Teil 3 als
Entwurfsprüfung ohne Produktcode.

## Worum es geht

Teil 1 hat die kanonische Identität `(ticker, mic)` ins Schema gebracht, Teil 2
das Anlegen neuer Papiere darauf umgestellt. Teil 3 schließt das Ticket ab: Was
sich nicht zuordnen lässt, wird **sichtbar**, und der Weg, auf dem unzuordenbare
Zeilen überhaupt entstehen, wird im **Vertrag** geschlossen.

## Drei Begriffe, die nicht vermischt werden dürfen

Der schwerste Fehler in Runde 8 kam daher, dass der Entwurf zwei verschiedene
Dinge „Symbol" nannte. Deshalb zuerst die Begriffe:

| Begriff | Beispiel | Wer ihn führt |
|---|---|---|
| **Kanonische Identität** | `(GOLD, XSTU)` | der Core — gespeichert in `ticker`/`mic` |
| **Provider-Alias** | `GOLD.SG` | die jeweilige Kursquelle — gespeichert in `symbol` |
| **Eingabeform** | `GOLD.SG` oder `GOLD.XSTU` | der Benutzer im Dashboard-Feld |

`app/services/quote_service.py:255` fragt die Quelle mit
`self._quote_provider.fetch_quote(resolved.symbol)` und speichert
`symbol=resolved.symbol`. Der Provider-Alias ist also nicht schmückendes
Beiwerk, sondern **abrufrelevant** — ein Weg, der nur `(ticker, mic)` liefert,
fragt Yahoo nach `GOLD` statt `GOLD.SG` und speichert den falschen Alias.

**Die Ableitungsrichtung ist festgelegt:** Aus der Identität entsteht der Alias,
nie umgekehrt. Für Yahoo gilt `alias = ticker + EXCHANGES[mic].suffix`. Die
Plugin-Grenze bleibt gewahrt (`plugin_api/src/stockinfo_plugin/types.py:54-71`):
Ein Resolver liefert `(ticker, mic)`, und **jede Kursquelle setzt daraus ihr
eigenes Format zusammen**. Der Core kennt die Yahoo-Ableitung nur, weil Yahoo
heute die eingebaute Quelle ist; sie lebt bei der Quelle, nicht in der
Validierung.

## Ausgangslage, gemessen und von Codex bestätigt

Offene Zuordnungen entstehen aus zwei Quellen:

| Quelle | Wann | Heilt sich selbst? |
|---|---|---|
| Migration (`app/db.py:277`) | beim Start, offline, Altbestand | ja, sobald eine ISIN-Auflösung läuft |
| Symbolweg (`app/services/quote_service.py:179`) | laufend, bei jedem suffixlosen Symbol | **nein** |

`get_quote_for_known` löst nicht auf — *„der Scheduler löst nichts auf, er holt
nur Kurse."* Für `AAPL` bleibt `split_symbol` dauerhaft `(None, None)`.

Der ISIN-Weg liefert immer eine vollständige Identität oder einen definierten
Fehler. Mit `DEFAULT_EXCHANGE=XETR`: `IE00B4L5Y983` → `EUNL.DE`/`XETR`,
`US0378331005` → `APC.DE`/`XETR`, `US9229087690` → `VTI`/`ARCX`; mit
`STRICT_EXCHANGE=true` wird aus der dritten Zeile `NotFound`.

## Entscheidungen

**1. Die Handzuordnung entfällt** (Verify `#2c`, Entscheidung Mike). Statt offene
Zeilen zu reparieren, entstehen sie nicht mehr: Der Symbolweg verlangt die
vollständige Kombination. Damit entfällt auch die Statusfrage aus Runde 3;
`identity_status` bleibt zweiwertig.

**2. Der Migrationspfad wird nicht eng gesehen** (Entscheidung Mike). Was sich
einfach migrieren lässt, wird migriert; der Rest bleibt offen und bekommt eine
verständliche Meldung. Kein Reparaturwerkzeug für Altbestand.

**3. Bewusste Umkehr gegenüber Teil 2.** Der Kommentar in `quote_service.py`
argumentiert dagegen, die Auskunft zu verweigern. Neu ist das Wissen, dass genau
diese Abfrage dauerhaft unzuordenbare Zeilen erzeugt. Der Parameter ist zudem
seit jeher als *„Vollständiges Yahoo-Symbol inkl. Suffix"* dokumentiert.

**4. `core_version` steigt auf `2.0.0`** (Entscheidung Mike).

**5. Ein Eingabefeld, zwei erlaubte Formen** (Entscheidung Mike). Bevorzugt die
ISIN; sonst im **selben** Feld entweder Provider-Suffix (`EUNL.DE`) oder echter
MIC (`EUNL.XETR`). Kein zweites Feld. Beide Formen normalisieren auf dieselbe
Identität `EUNL`/`XETR` und denselben Alias `EUNL.DE`.

## Die Börsentabelle wird vollständig

`EXCHANGES` führt heute 33 Einträge und **keinen einzigen echten US-MIC** —
`ARCX`, `XNAS`, `XNYS`, `XASE` und `BATS` fehlen, `US` steht als Sammelcode mit
Währung `USD`. Das trägt weder die Alias-Ableitung noch die Währungsanzeige.

Teil 3 ergänzt sie:

```python
"XSTU": ExchangeDef(".SG", "Stuttgart",   "germany", "EUR"),
"XNAS": ExchangeDef("",    "NASDAQ",      "usa",     "USD"),
"XNYS": ExchangeDef("",    "NYSE",        "usa",     "USD"),
"ARCX": ExchangeDef("",    "NYSE Arca",   "usa",     "USD"),
"XASE": ExchangeDef("",    "NYSE American","usa",    "USD"),
"BATS": ExchangeDef("",    "Cboe BZX",    "usa",     "USD"),
```

**Die Tabelle wird damit richtungsabhängig, und das ist beabsichtigt:**

* **MIC → Formen, Währung, Anzeigename** ist ab jetzt **vollständig**. Daran
  hängen Alias-Ableitung und Anzeige.
* **Form → MIC** bleibt **eindeutig**, weil leere Formen aus dieser Richtung
  ausgeschlossen sind. Fünf US-MICs teilen sich das leere Suffix; welcher
  gemeint ist, sagt nur die Auflösung oder der Benutzer. Genau diesen Fall
  benennt der Plugin-Entwurf vorab
  (`2026-08-19-plugin-system-design.md:365-373`).

### Der Exchange-Descriptor — erweiterbar von Anfang an

Ein bloßes Herkunftsfeld reicht **nicht**, wie Runde 10 gezeigt hat.
`ExchangeInfo` (`app/models.py:262-269`, `dashboard/src/types.ts:115-127`) trägt
heute genau **ein** `suffix: str` — T-30 verlangt aber „Suffixformen" im Plural
und müsste den Typ also doch ändern. Teil 3 legt deshalb gleich die tragfähige
Form fest:

**Zwei Arten von Eintrag, als diskriminierte Union.** Eine Börse und ein
Sammelcode sind verschiedene Dinge, und nur eines davon hat einen MIC:

```
{ "kind": "exchange",
  "mic": "XSTU", "name": "Stuttgart", "currency": "EUR",
  "alias": "SG",                      // genau einer, optional
  "provenance": { "kind": "core" } }

{ "kind": "collector",
  "code": "US", "name": "NYSE / NASDAQ", "currency": "USD",
  "members": ["XNAS", "XNYS", "ARCX", "XASE", "BATS"],
  "provenance": { "kind": "core" } }
```

Vier Entscheidungen, jede aus einem Befund:

* **`US` verlässt die Börsentabelle.** Heute serialisiert
  `app/routers/dashboard.py:72-82` jeden Eintrag als
  `ExchangeInfo(mic=mic, …)` — auch `US`. Die REST-API behauptet damit einen
  MIC, den `is_real_mic` selbst ablehnt. Ein Feld `mic` darf nie einen
  Sammelcode tragen; ein Plugin oder das UI könnte ihn sonst als kanonischen
  Wert übernehmen und genau den Zustand erzeugen, den T-21 verhindert.
* **Genau ein optionaler `alias`, keine Liste.** *(Präzisierung Mike nach
  Runde 10.)* `EUNL.XETR` und `EUNL.DE` sind **zwei Auflösungswege, nicht zwei
  Aliaswerte**: Der eine kommt über `mic`, der andere über den einen Alias. Die
  Liste aus Runde 11 war eine Überkorrektur auf einen Befund, der etwas anderes
  meinte, und bringt einen Kollisionsraum mit, den niemand braucht.
* **Die Punktkonvention steht an genau einer Stelle.** `alias` trägt das
  **nackte Token ohne Punkt** (`"SG"`, `"DE"`). Nachgeschlagen wird der Teil
  hinter dem letzten Punkt, also ebenfalls nackt; zusammengesetzt wird
  `ticker + "." + alias`, und ohne Alias bleibt es beim nackten `ticker`
  (`AAPL`). Der vorige Entwurf speicherte `".SG"` und schlug `SG` nach — die
  zwei Schichten hätten aneinander vorbeigesucht.
* **Die Collector-Mitgliedschaft steht genau einmal**, nämlich als `members` am
  Collector-Eintrag. Nicht zusätzlich als `collectors` an jeder Börse, nicht
  zusätzlich als `COLLECTOR_CODES`: Letzteres wird künftig **aus** den
  Collector-Einträgen abgeleitet, statt daneben gepflegt zu werden. Aus dem
  `region`-Feld abzuleiten ist ebenfalls verworfen — Kanada steht als
  `region: "global"`, und überlappende Sichten wären nicht ausdrückbar.

`region` bleibt, was es ist — eine Anzeigegruppe für die Oberfläche, keine
Fachregel.

**Vertragstests dazu:** Kein `mic`-Feld serialisiert je einen Sammelcode; `US`
funktioniert weiterhin als `DEFAULT_EXCHANGE` samt seinen Mitgliedern; kein
Alias ist zweimal vergeben; jeder Börseneintrag hat Währung und Anzeigename.

## Die Pflicht-Kombinationen für den Benutzer

Am Ende muss immer `(kanonischer Ticker, echter MIC)` herauskommen:

| Weg | Eingabe | Ergebnis |
|---|---|---|
| **1 — ISIN** | `IE00B4L5Y983` | Auflösung wählt das Listing, Vorzugsbörse entscheidet |
| **2 — Ticker + Suffix** | `EUNL.DE` | `(EUNL, XETR)`, Alias `EUNL.DE` |
| **3 — Ticker + MIC** | `EUNL.XETR`, `AAPL.XNAS`, `GOLD.XSTU` | `(EUNL, XETR)` / `(AAPL, XNAS)` / `(GOLD, XSTU)`, Alias `EUNL.DE` / `AAPL` / `GOLD.SG` |

**Die Trennung entsteht durch Nachschlagen, nicht durch Zählen.** Der frühere
Entwurf klassifizierte nach Länge — „vier Großbuchstaben = MIC, ein bis zwei
Zeichen = Suffix". Das trägt nur den heutigen Bestand: Ein Plugin darf einen
**vierstelligen** Provider-Alias mitbringen, und dann wäre die Länge eine
Rateregel mit hübscher Begründung.

Stattdessen: Der Teil hinter dem letzten Punkt wird **im Börsenkatalog
nachgeschlagen** — erst als kanonischer MIC, dann als Alias. Trifft er beides
und zeigt auf **verschiedene** Börsen, ist das ein benannter Konflikt mit
eigener Fehlerkennung, kein stillschweigender Vorrang. Trifft er nichts, ist es
ein unbekannter Handelsplatz — mit einer Meldung, die sagt, was der Katalog
kennt.

Eine Eingabe enthält dabei **genau eine** der beiden Formen; `EUNL.XETR` geht
über den MIC, `EUNL.DE` über den Alias, und beide enden bei derselben Identität
`(EUNL, XETR)` und demselben Abrufalias `EUNL.DE`.

Ergänzende Regeln:

* **Ein nackter Ticker ohne beides wird abgelehnt** — `AAPL` allein ergibt keine
  Identität. Der Fehlertext nennt beide Auswege mit Beispiel.
* **Widerspruch ist ein Fehler.** Führt die Eingabe zu zwei verschiedenen MICs,
  gibt es 400 mit benanntem Widerspruch, statt einen gewinnen zu lassen.
* **`US` als Eingabe wird abgelehnt**, weil es offenlässt, ob NYSE oder NASDAQ
  gemeint ist. Als `DEFAULT_EXCHANGE` bleibt es zulässig — dort heißt es „such
  in den USA", nicht „dieser Handelsplatz".
* **Nicht kanonische Ticker gehen nur über Weg 1.** `is_canonical_ticker` lässt
  nur `[A-Z0-9]` zu; `BRK-B`, `BRK/B` und `BRK.B` sind drei Schreibweisen
  desselben Papiers. Auch `BRK-B.XNYS` bleibt abgelehnt — die ISIN liefert die
  kanonische Schreibweise mit.
* **Nach Aufnahme von `XSTU` müssen `GOLD.SG` und `GOLD.XSTU` beide
  funktionieren** und auf dieselbe Identität `(GOLD, XSTU)` sowie denselben
  Alias `GOLD.SG` führen. Die Regel aus Runde 8, die `GOLD.SG` verwarf, ist
  **gestrichen** — sie widersprach dem Stuttgart-Eintrag im selben Entwurf.

## Was gebaut wird

### A. Der Vertrag am Aufnahmeweg

**Ein Endpunkt, ein roher Wert — und er schreibt, also ist er ein `POST`.**

```
POST /instruments/intake     { "identifier": "<roher Feldwert>" }
```

Kein `isin`/`symbol`-Verzweigen mehr am Client, kein zweiter Parameter für den
MIC. Was `identifier` bedeutet, entscheidet **allein der Core**.

Der vorige Entwurf hatte hier ein `GET`, das laut eigener Schichtentabelle
auflöst **und speichert**. Das ist der falsche HTTP-Vertrag: Browser, Proxies
und Vorablader dürfen ein `GET` als sichere Leseoperation behandeln und es
beliebig wiederholen oder vorziehen.

**Die Schichten, ohne Doppeldeutigkeit:**

| Schicht | Aufgabe | Ergebnis |
|---|---|---|
| Router | Transport, Normalisierung, Exception-Mapping — **keine Fachregel** | HTTP-Status und `{code, params}` |
| Intake-Service | Rohwert gegen den Börsenkatalog auflösen, Auflösung anstoßen, über das Repository speichern | kanonische Identität in `ticker`/`mic` |
| Kursquelle (Yahoo-Adapter) | aus `(ticker, mic)` ihr eigenes Format bilden | Abrufalias, z. B. `GOLD.SG` |

Die Auflösung gegen Börsenkatalog, MIC und Alias ist eine **Fachregel**, keine
HTTP-Prüfung. Sie gehört deshalb nicht in `app/routers/validation.py`, wo der
vorige Entwurf sie hinlegte, sondern in einen eigenen Intake-Service — dieselbe
Trennung, die der Rest des Projekts schon einhält.

Die Validierung liefert **nur** `(ticker, mic)`. Der frühere Satz, sie liefere
„`(ticker, mic)` und den Alias", war ein direkter Widerspruch zum Absatz
darunter und ist gestrichen. Der Alias entsteht ausschließlich im Adapter, über
`provider_alias(ticker, mic)` — die einzige Stelle im Projekt, die aus einer
Identität ein Providerformat baut. Wem der Alias **gehört** und was beim
Providerwechsel mit ihm geschieht, klärt **T-29**, nicht dieser Entwurf.

### B. Sichtbarkeit: zwei Zustände

`GET /instruments/identity` liefert:

1. **Offen** — `identity_status = legacy_unresolved`, mit **Grund** je Fall
   (`suffixlos`, `Suffix unbekannt`, `fremde Schreibweise`). Deckt Verify `#2b`.
2. **Von der Vorzugsbörse abgewichen** — mit erwartetem und tatsächlichem MIC,
   Anzeigenamen und **beiden Währungen**.

**Die Währung kommt aus den Kursdaten, nicht aus der Tabelle.** Die tatsächliche
Währung steht in `instruments.currency` — was die Quelle geliefert hat, ist die
belastbare Aussage; die Tabelle sagt nur, was zu erwarten *wäre*. Die erwartete
Währung kommt aus `EXCHANGES[default_exchange]`, sofern das ein echter MIC ist.

Das ist keine neue Regel, sondern eine schon aufgeschriebene: Der Docstring von
`ExchangeDef` sagt wörtlich *„`currency` ist nur Anzeige — die reale Kurswährung
stammt aus dem Live-Quote."* Der Entwurf aus Runde 8 hat genau diese Zusage
gebrochen, indem er beide Währungen aus der Tabelle nehmen wollte.

**Die Präferenz ist nicht immer ein Handelsplatz — der Antworttyp muss das
tragen.** `DEFAULT_EXCHANGE` darf ein Sammelcode sein (`US`), und dann gibt es
schlicht keinen „erwarteten MIC". Ein Antworttyp, der ihn zusagt, kann seinen
eigenen Vertrag bei einer ganz normalen Konfiguration nicht erfüllen. Deshalb
wird die Präferenz **typisiert** ausgeliefert:

```
preferred: { code: "US",   kind: "collector", currency: "USD" }
actual:    { mic:  "XLON", name: "London LSE", currency: "GBp" }
```

Bei `kind: "mic"` trägt `code` einen echten MIC und `name` den Anzeigenamen; bei
`kind: "collector"` gibt es keinen einzelnen Handelsplatz, aber sehr wohl eine
erwartete Währung.

**Die Abweichungsprüfung ist damit Collector-bewusst:**

* `AAPL`/`XNAS` bei Präferenz `US` → **keine** Abweichung, `XNAS` gehört dazu.
* `VOD`/`XLON` bei Präferenz `US` → **Abweichung**, mit `preferred.code = US`
  und erwarteter Währung `USD`, aber ohne erwarteten MIC.
* `VTI`/`ARCX` bei Präferenz `XETR` → Abweichung mit vollem erwartetem MIC.

Die Mitgliedschaft steht als `collectors` am jeweiligen Eintrag — `XNAS`,
`XNYS`, `ARCX`, `XASE` und `BATS` tragen dort `["US"]`. Sie aus `region`
abzuleiten war der Vorschlag aus Runde 9 und ist verworfen; die Begründung steht
beim Exchange-Descriptor.

**Keine Schemaänderung.** Beide Zustände sind aus gespeicherten Spalten und der
Konfiguration ableitbar.

### C. Dashboard: ein Feld, zwei Formen

Das bestehende Feld in `dashboard/src/components/Toolbar.vue:20-32` bleibt das
einzige.

**Der Core ist die einzige Parser- und Validierungsquelle.** Das Dashboard
schickt den **rohen** Feldwert und beschränkt sich auf Darstellung, Transport
und i18n. Der TypeScript-Parser aus dem vorigen Entwurf entfällt ersatzlos: Er
hätte dieselbe Grammatik ein zweites Mal implementiert, und sobald T-30
zusätzliche Formen erlaubt, klassifizierten UI und Core dieselbe Eingabe
verschieden. Das macht den Umfang von Teil 3 kleiner, nicht größer.

* **`isIsin` verschwindet aus dem Aufnahmeweg.** Heute klassifiziert
  `dashboard/src/api/paths.ts:3-5` das Format, und
  `useInstrumentActions.ts:36-39` wählt danach zwischen zwei REST-Formen — das
  ist die Doppelimplementierung, die Runde 10 zu Recht benannt hat. Künftig
  schickt `add(identifier)` den getrimmten Wert unverändert als
  `POST /instruments/intake` mit `{identifier}`. `isIsin` bleibt nur, wo es um
  **Darstellung** geht, nicht um Routing — dort ist es eine andere
  Verantwortung und muss nicht verschwinden.
* **Fehlerrückmeldung als Code, nicht als Text.** Der Core liefert
  `{code, params}` (etwa `identity.mic_required` mit dem erkannten Ticker); das
  Dashboard übersetzt über `de.ts`/`en.ts`. Ein deutscher Backendtext in der
  englischen Oberfläche wäre auch bei sauberem Parsen falsch.
* **Der Fallback ist ein Katalogeintrag, nicht `statusText`.**
  `dashboard/src/api/client.ts:18-20` liest Fehler heute mit `response.text()`,
  FastAPI liefert aber `{"detail": …}` — der Benutzer sähe rohes JSON. Der
  Client parst künftig den typisierten Fehler; **unbekannte Kennung,
  Nicht-JSON, leerer Rumpf und Netzwerkfehler laufen alle auf einen
  übersetzten Katalogeintrag** in DE und EN. `status` und `statusText` gehören
  ins Log, nicht in die Oberfläche: Sie sind browser- und serverabhängig, oft
  leer oder englisch („Bad Request") und erklären dem Benutzer nichts über die
  verlangte Eingabe.
* **i18n-Hilfe** in `de.ts` und `en.ts` mit den drei Formen als Beispiel.
* **Anzeige:** Nach der Auflösung zeigt das UI Ticker und echten MIC mit
  lesbarem Börsennamen; die Werte kommen aus der Core-REST-API.

### D. Vertrag und Version

`listing_id` und `ticker_mic` wandern aus `planned` in den zugesagten Core.
`InstrumentSummary` bekommt `ticker`, `mic` und `listing_id`. `core_version`
geht `1.0.0` → `2.0.0`, Snapshot per
`UPDATE_CORE_SNAPSHOT=1 .venv/bin/pytest tests/test_contract_openapi.py -q`.

### E. Eine Quelle für den Identitätsstatus

`app/db.py:173-175` hält private Kopien von `resolved` und `legacy_unresolved`
aus `app/exchanges.py:181-185`, obwohl der dortige Kommentar ausdrücklich eine
einzige Regelquelle verspricht. Die Kopien entfallen; Migration und
Laufzeitlogik importieren dieselben Konstanten.

### F. Dokumentationsinventur — wonach gesucht wurde

Zweimal hintereinander stand hier „vollständig", und zweimal fehlten Stellen.
Das lag an der Methode: Gesucht wurde nach **Formulierungen**, nicht nach dem
**Begriff**. Ab hier steht deshalb nicht mehr „vollständig", sondern wonach
gesucht wurde — nachvollziehbar und wiederholbar.

**Suchausdruck** über `app/`, `tests/`, `dashboard/src/`, `docs/`, `README.md`,
`plugin_api/src/` und `contract/`, ohne Vorfilter, jeder Treffer einzeln
eingeordnet:

```
manuelle[rn]? zuordnung | handzuordnung | von hand (zu|ge)?(ordn|setz) |
zur zuordnung | teil 3
```

Das ergibt siebzehn Treffer. Alle betreffen die gestrichene Handzuordnung:

| Stelle | Was dort steht |
|---|---|
| **`app/resolver.py:304`** | **Benutzer-Fehlermeldung:** *„Ticker und MIC müssen von Hand gesetzt werden"* — die sichtbarste Stelle überhaupt |
| `app/repository.py:455,458` | „Offen für Teil 3 … braucht dafür einen eigenen Status" |
| `app/db.py:306` | „Später von Hand zuordnen" als Versprechen der Meldung |
| `app/exchanges.py:167` | „die Tabelle ist eine Auswahl der Börsen, die eine manuelle Zuordnung setzen soll" |
| `app/exchanges.py:233` | „bis ihn jemand von Hand zuordnet" |
| `app/models.py:60` | „noch nicht am REST-Rand (T-21, Teil 3)" — ändert sich mit D |
| `docs/rest-core-contract.md:84` | „überlebt manuelle Zuordnung" |
| `tests/test_exchanges.py:82` | dieselbe Aussage wie `exchanges.py:167`, gespiegelt |
| `tests/test_openfigi_lookup.py:36` | „Eine manuelle Zuordnung darf einen Wert …" |
| `tests/test_identity_creation.py:121,187` | „die Liste offener Fälle (Teil 3)", „Vertrag ändert sich erst in Teil 3" |
| `tests/test_identity_intake_paths.py:129` | „Teil 3 listet sie zur Zuordnung von Hand auf" |
| `tests/test_identity_migration.py:206,385,439` | „später von Hand zuordnen", „ein von Hand gesetztes `VTI/XNAS`" |
| `tests/test_quote_service.py:632` | „Teil 3 samt Vertragsversion" |
| `_tickets/T-21-…:480` | „Ohne diesen Zustand ist ‚später von Hand zuordnen' ein Versprechen …" |

**Ein zweiter Begriff, der nicht im selben Ausdruck steckt:** die Begründung der
Nachsicht am Aufnahmeweg in `app/services/quote_service.py:171-177` — *„nähme
ihm eine Abfrage weg, die es heute gibt"*. Sie wird durch Entscheidung 3
hinfällig und gehört mit berichtigt. Dazu die README-Zeile zu
`GET /quote?symbol=…` (`README.md:207`), die nur das Suffix-Beispiel zeigt.

**Ausdrücklich nicht angefasst:** alle Stellen zu von Hand gepflegten
**Kennzahlen** aus T-09 (`overrides`, `manual_fields`, `MetricEditor`). Andere
Fachlichkeit, die derselbe Wortlaut mitfängt — rund dreißig Treffer, die beim
Einordnen ausgeschieden sind.

## Was in eigene Tickets geht

Entscheidung Mike, 2026-08-24: aufteilen. Zwei Themen sind aus diesem Entwurf
herausgeschnitten und liegen als Tickets im Board:

* **[`T-29`](../../../_tickets/T-29-alias-lebenszyklus-und-providerwechsel.md)
  — Provider-Alias: Eigentümer, Lebenszyklus, Wechsel.** Aus Runde 9, Finding 1.
  Wer `symbol` besitzt, was beim Providerwechsel damit geschieht, Backup-Pflicht
  und Best-Effort-Restore samt Importbericht. Revidiert außerdem
  `T-25-quellenprofil-wechseln.md:94-110`.
* **[`T-30`](../../../_tickets/T-30-plugin-boersenauskunft.md) — plugin-
  deklarierte Börsenauskunft.** Aus Runde 8 (Finding 3) und Runde 9 (Finding 5).
  Neuer `plugin_api`-Typ samt Merge-, Vorrang-, Kollisions-, Provenienz- und
  Invalidierungsregeln.

### Was Teil 3 deshalb ausdrücklich *nicht* tut

**Teil 3 stärkt die Zusage zu `symbol` nicht.** Das Vertragsartefakt nennt die
Spalte heute *„Anzeigename beim Kursanbieter"*
(`contract/core-contract.json:13-16, 49, 55`), der Plugin-Entwurf einen
*stabilen, App-eigenen Anzeigewert*
(`2026-08-19-plugin-system-design.md:323-329, 379-411`). Diese Unschärfe wird in
**T-29** aufgelöst, nicht hier. Der Sprung auf `core_version 2.0.0` betrifft
`ticker`, `mic`, `listing_id` und den strengeren Aufnahmeweg — **nicht** die
Bedeutung von `symbol`. Der Entwurf zementiert damit nichts, was T-29 später
umwerfen müsste.

**Die REST-Form der Börsenauskunft wird so entworfen, dass ein Plugin später
Einträge beisteuern kann, ohne dass sich der Antworttyp ändert.** Das leistet
der Exchange-Descriptor oben — die diskriminierte Union aus Börse und
Sammelcode, der optionale `alias` und die typisierte `provenance`. Ein bloßes
Herkunftsfeld hätte **nicht** gereicht; das war der Irrtum aus Runde 10, und
`ExchangeInfo` mit seinem einzelnen `suffix: str` und dem `mic="US"` hätte T-30
zur Typänderung gezwungen. Verify `#8` in
T-30 prüft rückwirkend, ob es gehalten hat.

## Testen

* **Aufnahmeweg:** nackter Ticker → 400 mit beiden Auswegen; `EUNL.DE` und
  `EUNL.XETR` → identische Identität **und** identischer Alias; `GOLD.SG` und
  `GOLD.XSTU` ebenso; `AAPL.XNAS` → Alias `AAPL`; `mic=US` → 400; Widerspruch →
  400; `BRK-B.XNYS` → 400.
* **Provider-Aufruf, gespeichertes `symbol`, `ticker` und `mic` werden
  gemeinsam geprüft** — genau die Lücke aus Befund 1. Ein Test, der nur die
  Identität prüft, hätte den falschen Alias nicht bemerkt.
* **Börsentabelle:** Eindeutigkeit der nichtleeren Suffixe; jeder Eintrag hat
  Währung und Anzeigename; die fünf US-MICs sind da.
* **Abweichung, alle drei Konfigurationen:** `VTI/ARCX` bei `XETR` → Abweichung
  mit vollem erwartetem MIC, `USD` gegen `EUR`; **`AAPL/XNAS` bei Default `US`
  → keine Abweichung**; **`VOD/XLON` bei Default `US` → Abweichung mit
  `kind: collector`, erwarteter Währung `USD` und *ohne* erwarteten MIC**. Dazu:
  ein Papier an der Vorzugsbörse taucht nicht auf, und die tatsächliche Währung
  kommt aus den Kursdaten, auch wenn die Tabelle etwas anderes erwarten ließe.
* **Vertrag:** `test_contract_openapi.py` gegen den Snapshot mit `2.0.0`.
* **Eingabe über den echten Weg**, nicht gegen einen Parser-Unittest: Router →
  Service → Repository für ISIN, `TICKER.DE`, `TICKER.XETR` und unbekannte
  Form. **Keine eigene Core-Komponente wird dabei gemockt** — nur die äußeren
  Grenzen. Die Zeilen stehen in der Verify-Matrix des T-21-Tickets, nicht nur
  hier in der Prosa.
* **Börsenkatalog als Descriptor:** `EUNL.XETR` und `EUNL.DE` ergeben dieselbe
  Identität und denselben Abrufalias; ein **vierstelliger** Alias wird als Alias
  erkannt und nicht wegen seiner Länge für einen MIC gehalten; ein Token, das
  als MIC **und** als Alias auf verschiedene Börsen zeigt, ergibt den benannten
  Konflikt.
* **Der Sammelcode als Vertragstest:** `US` wird **nie** als `mic` serialisiert
  oder gespeichert, funktioniert aber weiterhin als `DEFAULT_EXCHANGE` samt
  seinen Mitgliedern. Das ist die Zeile, die den heutigen `mic="US"` aus
  `GET /exchanges` fallen lässt.
* **Dashboard:** Vitest für den rohen Durchreichweg **ohne** `isIsin`-Routing,
  und für den Fehlerpfad in beiden Sprachen — bekannte Kennung, unbekannte
  Kennung, kaputtes JSON, leerer Rumpf, Netzwerkfehler. Dazu die beiden Zähler.
* **Smoke:** `_tickets/T-21c-smoke.sh` auf eigenem Port — `GOLD.SG` vor und nach
  dem Börseneintrag, der 400er am Aufnahmeweg, beide Listen.

## Was bewusst nicht gebaut wird

* **Handzuordnung über die Oberfläche** und ein **eigener Status** dafür.
* **Ein Reparaturwerkzeug für Altbestand.**
* **Eine gespeicherte Abweichungsmarkierung** — ableitbar.
* **Ein zweites MIC-Eingabefeld** — Entscheidung Mike.

Taucht ein realer Fall auf, in dem ein Mensch eine **falsche** automatische
Zuordnung überschreiben muss, ist das ein eigenes Ticket: Korrektur, nicht
Erstzuordnung.
