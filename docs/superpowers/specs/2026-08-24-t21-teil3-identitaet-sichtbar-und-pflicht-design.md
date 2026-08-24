# T-21 Teil 3 — Identität sichtbar machen und im Vertrag verlangen

**Datum:** 2026-08-24 · **Ticket:** `_tickets/T-21-identitaet-mic-und-ticker.md` ·
**Branch:** `t-21d-offene-zuordnungen` · **Status:** entworfen, **Runde 21** ·
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
vollständige Kombination.

**2. Es gibt keine halbe Identität mehr — nirgends** *(Entscheidung Mike,
2026-08-24, nach Runde 16; kehrt den bisherigen Zwischenzustand um)*.

Eine nicht auflösbare Altzeile darf **nicht** als `NULL`-Identität weiterleben —
weder im aktiven `instruments`-Bestand noch im REST-Vertrag noch im UI. Damit:

* Was sich **einfach und eindeutig** auflösen lässt, wird migriert.
* Alles andere kommt **nicht in den gültigen Bestand** und wird von keinem
  Instrument- oder Quote-Endpunkt serialisiert.
* `ticker` und `mic` sind danach **Pflicht**. Als Invariante nach erfolgreichem
  Start: `COUNT(*) WHERE ticker IS NULL OR mic IS NULL = 0`.
* Der Benutzer bekommt einen verständlichen **Bericht**: altes Symbol,
  konkreter Ablehnungsgrund, Aufforderung zur Neuerfassung. Entfallen dabei
  Kurspunkte, nennt der Bericht auch das; der Vorabhinweis verweist auf das
  Backup.
* Ein technischer Fehlerbericht oder eine Quarantäne darf die Rohinformation
  halten — sie ist aber **kein aktiver Instrumentdatensatz** und tritt über
  keinen Endpunkt als `NULL`-Zeile aus.

**Was dadurch gegenstandslos wird:** `identity_status` hätte nur noch **einen**
Wert. Die Spalte, ihre Konstanten in `app/exchanges.py` und die privaten Kopien
in `app/db.py` entfallen ersatzlos — damit erledigt sich auch der frühere
Abschnitt „Eine Quelle für den Identitätsstatus": Die beste Zahl an Quellen für
einen Wert, den es nicht mehr gibt, ist null. Ebenso entfällt die *offene
Zuordnung als Instrumentzustand*; der Abweichungszustand zur Vorzugsbörse
bleibt unberührt.

**Was das im echten Bestand kostet — nachgemessen**, damit die Entscheidung
nicht abstrakt bleibt:

| Papier | Tageskurse | unter der neuen Regel |
|---|---|---|
| `GOLD.SG` | **257** | migriert — **sofern `XSTU` vorher im Katalog steht** |
| `VTI` | **0** | abgelehnt; verliert praktisch nichts |
| `EUNL.DE`, `VGWL.DE`, `APC.DE`, `BRYN.DE` | 256–2234 | migrieren über das Suffix |

Der Preis der strengen Regel ist also **ein** Papier ohne Historie. Das Risiko
liegt woanders — siehe die Reihenfolge im Umsetzungsschnitt.

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

Ein bloßes Herkunftsfeld reicht **nicht**, wie Runde 10 gezeigt hat — der
Typwechsel kommt aber nicht von mehreren Suffixformen. Die Forderung nach
„Suffixformen im Plural" ist mit Mikes Präzisierung zurückgenommen, und dieser
Entwurf hält sie nicht mehr am Leben.

Nötig ist der Typwechsel aus drei anderen Gründen: `ExchangeInfo`
(`app/models.py:262-269`, `dashboard/src/types.ts:115-127`) kennt **keine
Unterscheidung zwischen Börse und Sammelcode** — es serialisiert heute
`mic="US"` —, es hat **keine Provenienz**, und sein `suffix: str` ist
**nicht optional**, obwohl die US-Plätze keinen Alias haben. Teil 3 legt deshalb
gleich die tragfähige Form fest:

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
Alias ist zweimal vergeben; jeder Börseneintrag hat Währung und Anzeigename;
und **kein Börseneintrag trägt eine eigene Mitgliedschaftsliste** — die
Zugehörigkeit steht ausschließlich als `members` am Collector.

**`COLLECTOR_CODES` wird abgeleitet, nicht gepflegt** — aus den
Collector-Einträgen derselben Katalogschicht, in der auch der Descriptor lebt;
damit entsteht kein Importzyklus. **Für T-30 ist das eine Auflage:** Sobald
Plugins Einträge beisteuern, darf keine beim Import eingefrorene Menge als
Wahrheit dienen. Dann wird der **zusammengeführte** Katalog gefragt oder die
Ableitung bei Invalidierung erneuert.

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
| Router | Transport, Exception-Mapping, `created` → `201`/`200` — **keine Fachregel** | HTTP-Status und Rumpf |
| Intake-Service | Rohwert gegen den Börsenkatalog auflösen, Auflösung anstoßen, über das Repository speichern | **`IntakeResult(summary, created)`** |
| Kursquelle (Yahoo-Adapter) | aus `(ticker, mic)` ihr eigenes Format bilden | Abrufalias, z. B. `GOLD.SG` |

**Warum der Service ein typisiertes Ergebnis liefert und nicht nur die
Identität:** Der Erfolgsvertrag unten verlangt ein vollständiges
`InstrumentSummary` **und** die Unterscheidung „neu angelegt" gegen „gab es
schon". Gäbe der Service nur `(ticker, mic)` zurück, müsste der Router die
Summary selbst beschaffen und den vorherigen Datenbankzustand ein zweites Mal
ermitteln — genau die Fach- und Repository-Logik, die er laut Zeile darüber
nicht enthalten darf. `IntakeResult` trägt beides; der Router mappt
ausschließlich `created` auf den Status und serialisiert `summary`.

**`created` ist eine Tatsache der schreibenden Transaktion, keine Vorabfrage.**
`_upsert_instrument` (`app/repository.py:387-427`) behandelt heute schon den
parallelen Erst-Request: Schlägt der Insert mit `IntegrityError` fehl, wird auf
die inzwischen existierende Zeile aktualisiert. Die Funktion **weiß** also, was
passiert ist, wirft es aber weg und gibt nur die ID zurück. Ein Existenzcheck
*vor* dem Schreiben wäre genau deshalb falsch: Ein konkurrierender Insert kann
ihn überholen, und der Aufnahmeweg meldete `201` für ein Papier, das jemand
anders gerade angelegt hat.

Also: Die Repository-Operation liefert **innerhalb derselben Transaktion**
`(instrument_id, created)`; im abgefangenen UNIQUE-Rennen ist `created = false`.
Der Service baut daraus Summary und `IntakeResult`, **ohne** eigenen Preflight.

Der Kettentest prüft **beide Zweige** und belegt, dass weder im Router noch im
Service ein zweiter Existenz-Check steht; ein Repository-Test deckt zusätzlich
den Konfliktpfad ab.

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

### B. Sichtbarkeit — was davon übrig bleibt

Die Entscheidung 2 hat diesen Abschnitt halbiert. Sichtbar zu machen ist noch:

1. **Von der Vorzugsbörse abgewichen** — mit erwartetem und tatsächlichem MIC,
   Anzeigenamen und **beiden Währungen**. Ein Zustand des laufenden Betriebs,
   von der Migration unberührt.
2. **Der Migrationsbericht** — und der ist etwas anderes als eine Liste offener
   Instrumente: Er zählt Zeilen auf, die **nicht** in den Bestand gekommen
   sind, mit altem Symbol, Ablehnungsgrund, verlorenen Kurspunkten und der
   Aufforderung zur Neuerfassung. Er liest **nicht** aus `instruments` — dort
   gibt es diese Zeilen ja gerade nicht mehr —, sondern aus dem getrennten
   Quarantäne-/Berichtsspeicher.

**Verify `#2b` ändert damit seine Bedeutung**, statt zu entfallen: Es prüft
nicht mehr „erscheint in einer Liste offener Zuordnungen", sondern „erscheint
im Migrationsbericht, mit Grund". Die alte Formulierung stammt aus einer Welt,
in der offene Zeilen im Bestand bleiben durften.

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

Die Mitgliedschaft wird **am Collector-Eintrag** nachgeschlagen: `US` führt
`members: ["XNAS", "XNYS", "ARCX", "XASE", "BATS"]`. Die Börseneinträge tragen
**keine** eigene Liste — sonst gäbe es die Regel wieder zweimal, und beim
Plugin-Merge liefen die Seiten auseinander. Aus `region` abzuleiten war der
Vorschlag aus Runde 9 und ist ebenfalls verworfen; beide Begründungen stehen
beim Exchange-Descriptor.

**Der Abweichungszustand braucht keine Schemaänderung** — er ist aus `mic`,
`instruments.currency` und der Konfiguration ableitbar. Das galt in Runde 13
noch für beide Zustände; seit Entscheidung 2 stimmt es nur noch für diesen.
Der **Migrationsbericht** liest aus einem eigenen Speicher, und Teil 2 ändert
das Schema ohnehin: `identity_status` fliegt raus, `ticker` und `mic` werden
`NOT NULL`.

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

**`ticker`, `mic` und `listing_id` sind Pflichtfelder.** Diese Zeile hat sich
zwischen Runde 15 und 16 gedreht, und der Grund ist nicht Unentschlossenheit,
sondern eine geänderte Voraussetzung:

* **Runde 15** verlangte zu Recht `nullable`. Damals durfte eine nicht
  zerlegbare Altzeile mit `NULL`-Identität im Bestand bleiben; nicht-nullbare
  Felder hätten `GET /instruments` bei genau diesem Zustand in einen
  Response-Validation-Fehler laufen lassen.
* **Entscheidung 2** hat diesen Zustand abgeschafft. Es gibt keine Zeile mehr,
  die `NULL` tragen dürfte — die Invariante nach dem Start lautet
  `COUNT(*) WHERE ticker IS NULL OR mic IS NULL = 0`.

Damit ist `nullable` nicht mehr nötig, sondern **schädlich**: Es wäre eine
Zusage an Konsumenten, mit einem Zustand zu rechnen, den es nicht geben darf,
und würde genau die halbe Identität wieder salonfähig machen, die dieses Ticket
austreibt.

**Der Vertragstest kehrt sich mit um:** Statt eine `legacy_unresolved`-Zeile mit
`ticker: null` zu serialisieren, belegt er künftig die **Invariante** — nach dem
Start trägt keine Zeile eine halbe Identität, und der Migrationsbericht nennt
die abgelehnten Fälle. Verify `#2j3` entfällt ersatzlos.

**Der Erfolgsvertrag von `POST /instruments/intake`** — ohne ihn dürfte die
Umsetzung zwischen `200 null`, `QuoteResponse`, `InstrumentSummary` und `204`
wählen, und Snapshot wie Integrationstest hätten keine Erwartung:

| Fall | Status | Rumpf |
|---|---|---|
| Papier neu angelegt | `201 Created` | `InstrumentSummary` |
| Papier gab es schon, Kurs aufgefrischt | `200 OK` | `InstrumentSummary` |
| Eingabe nicht auflösbar | `400` | `{code, params}` |
| Quelle nicht erreichbar | `502` | `{code, params}` |

`204` wäre die bequemere Zusage, wirft aber genau die Information weg, um die
der Aufrufer gerade gebeten hat: Welche Identität ist daraus geworden? Der
Rumpf erspart dem Dashboard den zweiten Roundtrip, um Ticker und echten MIC
anzuzeigen. Beide Erfolgsfälle tragen denselben Typ; unterschieden wird nur der
Status, damit „war schon da" nicht als Neuanlage erscheint.

**Die Börsenauskunft heißt nicht mehr `exchanges`.** Die Liste trägt seit dem
Descriptor zwei Eintragsarten; sie weiter `exchanges` zu nennen, während
Sammelcodes darin stehen, wäre dieselbe Unehrlichkeit wie `mic="US"`. Die
Antwort heißt `catalog`, ihre Einträge sind die diskriminierte Union.

### E. `identity_status` entfällt ersatzlos

Hier stand bis Runde 16, dass die privaten Kopien von `resolved` und
`legacy_unresolved` in `app/db.py:173-175` gegen die kanonischen Konstanten in
`app/exchanges.py:181-185` zusammengeführt werden. Mit Entscheidung 2 ist die
Frage erledigt, aber anders als gedacht: Wenn keine Zeile mehr offen sein
**darf**, trägt die Spalte nur noch einen einzigen Wert.

Also entfallen: die Spalte `identity_status`, `IDENTITY_RESOLVED` und
`IDENTITY_UNRESOLVED` in `app/exchanges.py`, die privaten Kopien in
`app/db.py`, `_report_unresolved` und alles, was daran hängt. Die
Vollständigkeitsaussage von `canonical_identity` bleibt — sie entscheidet
weiterhin, ob eine Identität gültig ist; sie schreibt das Ergebnis nur nicht
mehr als Status weg, sondern führt zu Annahme oder Ablehnung.

Ein Glück für den Rückbau: `identity_status` ist **nie** in den REST-Vertrag
oder ins Dashboard gelangt — nachgeprüft, `contract/` und `dashboard/src/`
kennen ihn nicht. Der Ausbau bleibt damit intern.

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

**Ein dritter Begriff, seit Entscheidung 2:** alles, was den
`legacy_unresolved`-Zwischenzustand als gültiges Ziel beschreibt. Zwei
Fundstellen liegen **außerhalb** von T-21 und sind eigene versionierte
Wissensquellen — sie werden mit berichtigt, sonst widersprechen sich die
Dokumente gegenseitig:

| Stelle | Was dort steht |
|---|---|
| `_tickets/T-24-rest-core-vertrag.md:194` | führt `identity_status = legacy_unresolved` als Vertragsgegenstand |
| `docs/superpowers/specs/2026-08-19-plugin-system-design.md:667` | *„T-21 braucht Zwischenzustand … `NULL`-fähige Spalten plus `identity_status`, sonst ist ‚melden statt raten' technisch unmöglich"* — als **übernommen** markiert |

Die zweite ist die heikelste: Sie steht als abgehakte Entscheidung in einem
fremden Entwurf. Wer dort nachliest und T-21 nicht kennt, baut den
Zwischenzustand nach.

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

## Der Schnitt für die Umsetzung

Vier Übergaben statt einer — Teil 1 brauchte neun Runden, Teil 2 sieben, und
ein Hub aus Katalog, Aufnahmeweg, Sichtbarkeit und Vertrag wäre nicht prüfbar.

**Die Vertragsgrenze bestimmt den Schnitt, nicht die Bequemlichkeit.**
`docs/rest-core-contract.md:33-34` nimmt die Schreibvorgänge des Dashboards und
`/exchanges` ausdrücklich vom geschlossenen Core aus. Daraus folgt:

| | Umfang | Vertrag |
|---|---|---|
| **1 — Börsenkatalog** | Descriptor, Union, `catalog`, die sechs neuen Einträge (**darunter `XSTU`**), `COLLECTOR_CODES` abgeleitet | **kein** Versionssprung — `/exchanges` liegt außerhalb des geschlossenen Core |
| **2 — Migration **mit** ihrer Meldung** | Migrieren-oder-ablehnen, Quarantäne, Berichtsspeicher, `identity_status` ausbauen, `ticker`/`mic` auf `NOT NULL`, Invariante — **und im selben Zug** die Vorabwarnung und die Berichtsanzeige im UI | intern; berührt den Core erst über die Pflichtfelder in Teil 3 |
| **3 — Aufnahmeweg, atomar mit dem Vertrag** | `POST /instruments/intake`, Intake-Service mit `IntakeResult`, Fehlerkennungen, der strengere `/quote?symbol=`, `ticker`/`mic`/`listing_id` als Pflichtfelder, Aufnahme des Endpunkts in den Core-Vertrag, **`core_version 2.0.0`** und Snapshot | **alles in einer Übergabe** |
| **4 — Abweichung, Fehlerpfad, Inventur** | Abweichungszustand sichtbar, Fehlerkennungen in beiden Sprachen, Dokumentationsinventur | Snapshot nur, wenn der Core sich noch einmal ändert |

> ### ⚠️ Gleichzeitige Auslieferung genügt **nicht** — es braucht zwei Phasen
>
> Der frühere Text hier sagte, Ablehnung und Sichtbarkeit müssten „in dieselbe
> Übergabe". Das ist zu wenig, und der Grund steht im Code:
> `app/main.py:27-32` ruft `init_db()` im **FastAPI-Lifespan** auf — also
> bevor die App den ersten Request bedient —, und das gebaute Dashboard wird
> erst nach abgeschlossenem Lifespan erreichbar (`app/main.py:106-125`). Ein
> gemeinsam ausgeliefertes UI kann den Benutzer damit **nicht** warnen: Wenn er
> es sieht, ist die Migration längst gelaufen.
>
> **Der Ablauf ist deshalb zweiphasig:**
>
> | Phase | Was passiert | Was der Benutzer sieht |
> |---|---|---|
> | **1 — erkennen** | Der Start erkennt eine ausstehende Migration und **rechnet ihre Auswirkung vor**: welche Symbole, aus welchem Grund, wie viele Kurspunkte. **Es wird nichts verändert.** | Eine eingeschränkte Oberfläche mit genau dieser Liste, dem Backup-Hinweis und einer ausdrücklichen Bestätigung |
> | **2 — ausführen** | Erst die Bestätigung löst die **atomare** Migration aus. Danach werden Scheduler und normale Endpunkte freigegeben — **genau einmal**. | Der Bericht über das, was tatsächlich passiert ist |
>
> #### Phase 1 ist serverseitig verriegelt, nicht nur im UI ausgeblendet
>
> Den Scheduler abzuschalten genügt **nicht**: Auch normale Requests schreiben.
> `/quote` legt Instrumente an und aktualisiert sie
> (`app/routers/quotes.py:26-116`), dazu kommen `/refresh` sowie mehrere `PUT`-
> und `DELETE`-Routen (`app/routers/dashboard.py:107-198`). Eine eingeschränkte
> Oberfläche hindert weder ein `curl` noch einen alten offenen Browser-Tab —
> und dann stimmt die vorgerechnete Auswirkung bei der Bestätigung nicht mehr.
>
> Deshalb ein **zentraler Migration-Pending-Guard** im Server, **eine** Quelle
> für den Zustand. Die Allowlist ist eine **Liste aus Methode und Pfad**, nicht
> die Faustregel „alles ohne Datenbankzugriff" — die hätte die Diagnosewege
> gleich mitgesperrt, weil `/ready` selbst die Datenbank anfasst
> (`count_instruments()`). Erlaubt sind:
>
> | Pfad | warum |
> |---|---|
> | die statische Oberfläche | sonst gäbe es nichts zu bestätigen |
> | `GET /health` | Liveness, hängt an nichts |
> | der **Healthcheck-Endpunkt** aus dem Abschnitt unten | sonst flaggt das Image während einer korrekten Wartezeit |
> | `GET /ready` | **liest die Datenbank** und muss trotzdem antworten dürfen — sonst kann niemand den Pending-Zustand abfragen |
> | Vorschau, Bestätigung, Bericht | der Zweck der Phase |
>
> Alles andere wird mit einer **stabilen Kennung** abgewiesen — aus derselben
> Zustandsquelle. Einzelprüfungen in den Routern wären eine parallele
> Fachregel, ein Sonderweg für die Diagnose eine zweite Ausnahmequelle; beides
> nicht.
>
> Ein **Routentabellen-Test** ruft im Pending-Zustand jeden erlaubten Pfad
> erfolgreich auf, weist mindestens je einen normalen Lese- **und** Schreibpfad
> mit der stabilen Kennung ab und belegt, dass Datenbank und Vorschau
> unverändert bleiben.
>
> Die Bestätigung ist gegen **parallele und doppelte** Aufrufe verriegelt.
>
> #### `/ready` behält seine Bedeutung — der Healthcheck zieht um
>
> **Eine Selbstkorrektur.** Der vorige Entwurf ließ `/ready` in Phase 1 mit
> `200` antworten, begründet mit einem drohenden Restart- und Routing-Deadlock.
> Diese Begründung stammte aus dem **Kommentar** in `docker/Dockerfile:71-75`
> (*„steuert Neustart und Traffic-Freigabe"*) — nicht aus geprüftem
> Laufzeitverhalten. Nachgemessen stimmt sie für dieses Deployment nicht:
>
> * Ein `HEALTHCHECK` markiert den Container als `unhealthy`. **Die Docker
>   Engine startet ihn deswegen nicht neu.**
> * Die verwendete Policy `--restart unless-stopped` (`Makefile:158`) reagiert
>   auf einen **beendeten Prozess**, nicht auf den Health-Status.
> * Ein Router, der anhand des Status Traffic freigibt, existiert im Projekt
>   nicht.
>
> Damit war `200` nicht nur unnötig, sondern **falsch**: `/ready` ist im
> öffentlichen Diagnosevertrag die Arbeitsbereitschaft — `app/main.py:81-103`
> nennt den Statuscode „die eigentliche Aussage", `ReadinessResponse` fragt
> „Kann er gerade arbeiten?", und die README beschreibt es genauso. Während der
> Guard sämtliche Fachrequests abweist, wäre `200` eine Lüge an jeden
> Consumer, der Readiness bestimmungsgemäß am Statuscode bewertet.
>
> **Also drei Zustände statt zwei, mit je eigener Frage:**
>
> | Frage | Endpunkt | in Phase 1 |
> |---|---|---|
> | Läuft der Prozess? | `/health` | `200`, wie immer |
> | Ist der Prozess arbeitsfähig — Migrations-UI **oder** Fachbetrieb? | **neuer Healthcheck-Endpunkt** | `200` |
> | Ist der **normale Fachbetrieb** freigegeben? | `/ready` | **`503`**, `status: "migration_pending"` |
>
> Der Docker-`HEALTHCHECK` zieht auf den mittleren Endpunkt um. `/ready` behält
> Bedeutung, Modell, README und Tests unverändert — es sagt weiterhin die
> Wahrheit, und die lautet in Phase 1 „nein".
>
> **Zusagen über Restart und Routing macht dieser Entwurf keine mehr.** Sie
> gälten nur für eine konkret vorhandene Orchestrator-Konfiguration und wären
> dort über Health-Status, Container-ID, Restart-Zähler und Erreichbarkeit zu
> prüfen — nicht durch Warten. Der Image-Test belegt deshalb das Nachprüfbare:
> Der Pending-Zustand überdauert `start-period` + 3 × `interval`, der
> Healthcheck-Endpunkt bleibt `200`, `/ready` bleibt `503`, und Vorschau wie
> Bestätigung sind durchgehend erreichbar.
>
> #### Ein verbindlicher Ablauf, kein Wahlrecht
>
> Der Browser-Ablauf ist **Pflicht** — Mikes Entscheidung verlangt Bestätigung
> und Bericht beim Benutzer. Ein `make`-Ziel, das dasselbe offline vorrechnet
> und ausführt, ist ein **zusätzliches Werkzeug** für den Betrieb, **keine
> Alternative**: Der frühere Entwurf nannte beides gleichwertig und verlangte
> zugleich API-Form und `/ready`-Verhalten, was eine reine Offline-Umsetzung
> gar nicht erfüllen kann. Ein Wahlrecht bräuchte zwei vollständig prüfbare
> Zweige; das ist mehr Aufwand als Nutzen.
>
> **Was Phase 1 und 2 gemeinsam brauchen** — und was Teil 2 mitliefert, nicht
> Teil 4: die API-Form für Vorschau und Bericht, **stabile Reason-Codes** statt
> freier Texte, und die DE/EN-Übersetzung dazu. Bloße Gleichzeitigkeit im
> Commit erfüllt `#2b5` nicht.
>
> **Für den Berichtseintrag gilt zusätzlich:** Ablehnung, Zählung der
> verlorenen Kurspunkte und der dauerhafte Eintrag entstehen in **derselben
> Transaktion**; ein zweiter Start dupliziert sie nicht; und der Eintrag bleibt
> abrufbar, **nachdem** die aktive Zeile weg ist — sonst verschwände genau die
> Information, die den Verlust erklären soll.

> ### ⚠️ Die Reihenfolge ist kein Geschmacksfrage — sie entscheidet über Daten
>
> **Teil 1 muss vor Teil 2 laufen.** Solange `XSTU`/`.SG` nicht im Katalog
> steht, ist `GOLD.SG` nicht auflösbar — und unter der neuen Regel wird es dann
> **abgelehnt statt migriert**. Im echten Bestand hängen daran **257
> Tageskurse**, nachgemessen. Andersherum migriert dieselbe Zeile sauber.
>
> Das ist der teuerste Fehler, den dieser Schnitt zulässt, und er ist durch
> nichts wiedergutzumachen außer dem Backup. Deshalb steht er hier und nicht in
> einer Fußnote.

**Warum Teil 3 nicht teilbar ist:** Der strengere `/quote?symbol=` ändert einen
Endpunkt **im** geschlossenen Core — eine Anfrage, die heute `200` liefert,
liefert dann `400`. Käme der Versionssprung erst in Teil 4, wäre der Endpunkt
dazwischen öffentlich geändert, aber nicht zugesagt, und Verify `#2i` ließe sich
bis dahin gar nicht prüfen. Vertragsartefakt, `core_version` und Snapshot ziehen
deshalb **mit der ersten Änderung am geschlossenen Core** um, nicht danach.
Jede weitere Core-Änderung erneuert den Snapshot erneut.

**Teil 3 korrigiert dabei auch die Vertragsprosa.**
`docs/rest-core-contract.md:33-34` sagt heute pauschal, „die Schreibvorgänge des
Dashboards" seien nicht im Core. Nimmt Teil 3 `POST /instruments/intake` in den
geschlossenen Core auf, wird diese Aussage falsch — und sie darf nicht bis zur
Inventur in Teil 4 falsch stehen bleiben. Die Präzisierung gehört in **dieselbe**
Übergabe wie der Endpunkt.

**Teil 4 entscheidet sich am Scope:** Der Abweichungszustand braucht einen
Leseendpunkt. Wird er in den geschlossenen Core aufgenommen, gehören Snapshot
und SemVer in dieselbe Übergabe; bleibt er intern — wie `/exchanges` und die
Diagnosewege —, bleibt der Vertrag unverändert. Der Teil-4-Entwurf entscheidet
das ausdrücklich, statt es offen zu lassen. Den früher hier genannten Namen
`/instruments/identity` gibt es nicht mehr: Er trug beide Zustände, und seit
Entscheidung 2 ist der eine ein Migrationsbericht und der andere ein
Betriebszustand.

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
* **Migration ohne halbe Identität:** zerlegbare Zeilen kommen durch;
  `AAPL`-artige werden **abgelehnt** und erscheinen im Bericht mit Grund und
  verlorenen Kurspunkten; nach dem Lauf gilt die Invariante
  `COUNT(*) WHERE ticker IS NULL OR mic IS NULL = 0`; die Quarantäne ist über
  keinen Instrument-Endpunkt erreichbar. **Und:** mit `XSTU` im Katalog
  migriert `GOLD.SG` samt seiner Kurspunkte, statt abgelehnt zu werden.
* **`_tickets/T-21-smoke.sh` wird umgestellt** — er wertet heute `GOLD.SG` und
  `VTI` als zwei gültige offene `NULL`-Fälle und würde die neue Regel grün
  melden. Neu: vier bis fünf migrierte Zeilen, kein offener Fall, der Rest im
  Bericht.
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
  seinen Mitgliedern. Das ist die Zeile, die den heutigen `mic="US"` aus der
  Börsenauskunft fallen lässt. Dazu: **kein** Börseneintrag trägt eine eigene
  Mitgliedschaftsliste.
* **Der Erfolgsvertrag des Aufnahmewegs:** `201` bei Neuanlage, `200` bei einem
  schon bekannten Papier, beide mit `InstrumentSummary`; `400` und `502` mit
  `{code, params}`. Im OpenAPI-Snapshot zugesagt und über die echte Kette
  geprüft, nicht nur im Modell.
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
