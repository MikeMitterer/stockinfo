# T-21 Teil 3 — Identität sichtbar machen und im Vertrag verlangen

**Datum:** 2026-08-24 · **Ticket:** `_tickets/T-21-identitaet-mic-und-ticker.md` ·
**Branch:** `t-21d-offene-zuordnungen` · **Status:** entworfen, Runde 9 ·
**Vorlauf:** Runde 8 hat fünf Befunde gebracht; die zwei „Hoch"-Befunde waren
Entwurfsfehler und sind hier behoben.

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

* **MIC → Suffix, Währung, Anzeigename** ist ab jetzt **vollständig**. Daran
  hängen Alias-Ableitung und Anzeige.
* **Suffix → MIC** bleibt **eindeutig**, weil das leere Suffix aus dieser
  Richtung ausgeschlossen ist. Fünf US-MICs teilen es sich; welcher gemeint ist,
  sagt nur die Auflösung oder der Benutzer. Genau diesen Fall benennt der
  Plugin-Entwurf schon vorab (`2026-08-19-plugin-system-design.md:365-373`).

`test_kein_suffix_ist_doppelt_vergeben` prüft künftig die Eindeutigkeit **der
nichtleeren** Suffixe und zusätzlich, dass jeder Eintrag Währung und
Anzeigename hat. Der Sammelcode `US` bleibt bestehen; er ist der Vorgabewert für
`DEFAULT_EXCHANGE` und keine Handelsplatzangabe.

## Die Pflicht-Kombinationen für den Benutzer

Am Ende muss immer `(kanonischer Ticker, echter MIC)` herauskommen:

| Weg | Eingabe | Ergebnis |
|---|---|---|
| **1 — ISIN** | `IE00B4L5Y983` | Auflösung wählt das Listing, Vorzugsbörse entscheidet |
| **2 — Ticker + Suffix** | `EUNL.DE` | `(EUNL, XETR)`, Alias `EUNL.DE` |
| **3 — Ticker + MIC** | `EUNL.XETR`, `AAPL.XNAS`, `GOLD.XSTU` | `(EUNL, XETR)` / `(AAPL, XNAS)` / `(GOLD, XSTU)`, Alias `EUNL.DE` / `AAPL` / `GOLD.SG` |

**Die Trennung ist syntaktisch eindeutig**, nicht geraten: Suffixe sind ein bis
zwei Zeichen (`.F`, `.DE`, `.TO`), echte MICs genau vier (`XETR`, `XNAS`). Ein
Token von vier Großbuchstaben hinter dem Punkt ist ein MIC, alles Kürzere ein
Suffix. Beide werden gegen `EXCHANGES` geprüft, nichts wird erraten.

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

`GET /quote` bekommt einen optionalen Query-Parameter `mic`. Die Prüfung sitzt
in `app/routers/validation.py`, wo die übrigen Eingabeprüfungen liegen, und
liefert `(ticker, mic)` **und** den Alias.

Der Alias entsteht in der Kursquelle, nicht in der Validierung — sonst wäre die
Plugin-Grenze verletzt. Der Yahoo-Adapter bekommt dafür eine Funktion
`provider_alias(ticker, mic)`; sie ist die einzige Stelle, die
`ticker + suffix` bildet.

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

Die Mitgliedschaft (`US` → `{XNAS, XNYS, ARCX, XASE, BATS}`) wird aus dem
`region`-Feld der Einträge abgeleitet, damit sie nicht als dritte Liste gepflegt
werden muss — Sammelcode und Mitglieder tragen dieselbe Region.

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

* **`dashboard/src/api/paths.ts:24-35`** bildet den Rohwert auf den
  Aufnahme-Endpunkt ab — ein Parameter, nicht zwei.
* **Fehlerrückmeldung als Code, nicht als Text.** Der Core liefert einen
  strukturierten Fehler mit Kennung und Parametern (etwa
  `identity.mic_required` mit dem erkannten Ticker); das Dashboard übersetzt ihn
  über `de.ts`/`en.ts`. Ein deutsch formulierter Backendtext, der unverändert in
  der englischen Oberfläche landet, wäre die falsche Lösung.
* **Sicheres Lesen des Fehlerrumpfs.** `dashboard/src/api/client.ts:18-20` liest
  Fehler heute mit `response.text()`, FastAPI liefert aber
  `{"detail": …}` — der Benutzer sähe rohes JSON. Der Client parst künftig JSON
  und fällt bei unbekannter Form auf `statusText` zurück.
* **i18n-Hilfe** in `de.ts` und `en.ts` mit den drei Formen als Beispiel, plus
  ein Auffangtext für unbekannte Fehlerkennungen.
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

### F. Dokumentationsinventur, diesmal vollständig

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
Einträge beisteuern kann, ohne dass sich der Antworttyp ändert.** Jeder Eintrag
trägt dafür von Anfang an ein Herkunftsfeld; heute steht dort immer `core`.
Verify `#8` in T-30 prüft, ob das gehalten hat.

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
* **Eingabe als Integrationstest, nicht als Parser-Unittest:** ISIN,
  `TICKER.DE`, `TICKER.XETR`, unbekannte Form — jeweils durch den Core, weil dort
  die einzige Grammatik lebt.
* **Dashboard:** Vitest für den rohen Durchreichweg, für die Übersetzung der
  Fehlerkennung in Deutsch **und** Englisch, für den Auffangtext bei unbekannter
  Kennung, für das sichere Lesen eines JSON-Fehlerrumpfs und für die beiden
  Zähler.
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
