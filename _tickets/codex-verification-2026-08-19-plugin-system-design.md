# Codex-Verifikation: Plugin-System-Design

**Datum:** 2026-08-19  
**Geprüft:** `docs/superpowers/specs/2026-08-19-plugin-system-design.md`,
Tickets T-17 bis T-23, `plugin_api/` und die betroffenen App-, Persistenz- und
Deployment-Codepfade.  
**Ergebnis:** Die Grundarchitektur ist sinnvoll, aber vor der Freigabe sind
mehrere Widersprüche und Architekturblocker zu klären.

## Kurzurteil

Die Trennung zwischen deklarativen REST-Quellen und Python-Plugins passt zum
Problem. Ebenfalls sinnvoll sind eine gemeinsame Registry, explizite
Ergebnisarten, Request-Objekte, Zuständigkeitsprüfungen und das Laden von
Python-Code nur beim Start.

In der aktuellen Form tragen Vertrag und Datenmodell das formulierte Ziel aber
noch nicht vollständig. Besonders kritisch sind:

1. Der öffentliche Vertrag deckt nur Resolver und Metadaten ab, nicht Kurse,
   Tageshistorie und FX.
2. Der in T-23 verlangte harte Timeout ist für in-process ausgeführten,
   synchronen Python-Code nicht zuverlässig umsetzbar.
3. T-21 behält das Yahoo-Symbol als notwendiges und eindeutiges Datenbankfeld;
   damit wird die Yahoo-Kopplung nicht wirklich gelöst.
4. T-19 würde beim Wechsel des Listings Historien verschiedener Börsen und
   Währungen unter derselben Instrument-ID vermischen.
5. Der Metadatenvertrag verspricht Herkunft je Feld, die Persistenz besitzt
   aber nur eine gemeinsame Herkunft und einen groben Vollständigkeitsstatus.
6. Das deklarative Format ist noch nicht ausreichend spezifiziert und ist
   sicherer als Python-Code, aber nicht frei von Schlüsselabfluss- und
   SSRF-Risiken.

## 1. Öffentlicher Vertrag und Scope passen noch nicht zusammen

Das Designziel nennt fünf austauschbare Rollen:

- ISIN-Auflösung
- aktuelle Kurse
- Tageshistorie
- Devisen
- ETF-Metadaten

In `plugin_api/src/stockinfo_plugin/sources.py:170-176` sind jedoch nur
`Resolver` und `MetadataSource` umgesetzt. `QuoteSource`, `DailyCloseSource`
und `FxSource` stehen dort ausdrücklich nur als Kommentar für später.

Damit können T-22 und T-23 das Ziel „Datenquellen werden austauschbar“ noch
nicht vollständig erfüllen. Das betrifft nicht nur fehlende Basisklassen,
sondern auch fehlende Request-/Response-Typen und Fehlersemantik:

- Quote braucht Ticker + MIC, Zeitpunkt, Kurs, Währung und Herkunft.
- Daily braucht Ticker + MIC sowie Zeitraumgrenzen und eine unterscheidbare
  Antwort für leer/ausgefallen.
- FX braucht Base/Quote, Zeitpunkt, Kurs und Herkunft.
- Für alle Rollen muss geklärt werden, ob dieselben vier Ergebnisarten gelten
  oder rollenspezifische Result-Typen verwendet werden.

Das Vertragspaket steht bereits auf Version `1.0.0`. Das ist zu früh, solange
drei der fünf versprochenen Rollen fehlen und gemeinsame Typen noch geändert
werden müssen. Empfehlung: bis zur Bewährung aller Rollen `0.x` verwenden.

### Runtime-Integration fehlt

`stockinfo-plugin-api` ist weder in `requirements.txt` enthalten noch wird
`plugin_api/` im Dockerfile kopiert und installiert. T-20 fordert aber, dass die
App die Typen direkt aus diesem Paket übernimmt. In der heute ausgelieferten
App wären diese Imports daher nicht verfügbar.

Vor T-20/T-23 muss festgelegt werden, ob das Paket:

- aus einem Package-Index installiert wird,
- als lokales Paket in das Image kopiert wird oder
- Teil eines Monorepo-Builds wird.

## 2. Harte Plugin-Timeouts funktionieren nicht zuverlässig in-process

T-23 Verify #5 verlangt, dass ein 60 Sekunden hängendes Plugin durch eine
Zeitgrenze gestoppt wird und die Kette weiterläuft. T-23 nennt als Isolation
Timeout, `except Exception` und einen Circuit-Breaker.

Ein synchroner Python-Aufruf lässt sich durch einen Thread- oder
Future-Timeout aber nicht beenden. Der wartende Aufrufer kann zwar nach Ablauf
zurückkehren, der Plugin-Thread läuft oder hängt jedoch weiter. Wiederholte
Hänger erschöpfen schließlich den Threadpool. Native Bibliotheken können den
Prozess noch stärker blockieren.

Es braucht deshalb eine explizite Entscheidung:

- **Separate Worker-Prozesse:** Ein hängender Aufruf kann beendet werden. Das
  bringt IPC, Serialisierung, Prozess-Lifecycle und mehr Aufwand mit sich.
- **Kooperative Timeouts:** Die harte Garantie aus T-23 entfällt. Provider
  müssen ihre HTTP-/Bibliotheks-Timeouts selbst setzen; Circuit-Breaker schützen
  nur vor weiteren Aufrufen, nicht vor dem bereits hängenden Aufruf.

`except Exception` schützt vor Ausnahmen, aber nicht vor Hängern, `BaseException`,
Prozessabstürzen oder Ressourcenverbrauch.

## 3. T-21 löst die Yahoo-Identität nicht vollständig

T-21 führt `ticker` und `exchange_mic` ein, behält `symbol` aber als
Yahoo-Symbol. Im heutigen Schema ist `symbol`:

- `NOT NULL` (`app/db.py:21`)
- durch `idx_instruments_symbol` global eindeutig (`app/db.py:170-174`)
- Schlüssel mehrerer API-, Repository- und Dashboard-Pfade

Wenn diese Bedingungen bestehen bleiben, benötigt auch ein Instrument, das
ausschließlich über EODHD oder Twelve Data verwaltet wird, weiterhin ein
gültiges und eindeutiges Yahoo-Symbol. Yahoo bleibt dadurch ein notwendiger
Bestandteil der Identität.

Empfehlung:

- Kanonische Listing-Identität: `ticker + mic`.
- Yahoo-Symbol nur als optionaler, provider-spezifischer Alias oder abgeleiteter
  Wert.
- Provider-Aliase nicht in die kanonische Instrumentenzeile pressen; bei Bedarf
  eigene Alias-Tabelle.
- Bestehende `/by-symbol/`-Pfade als Kompatibilitätsschicht behandeln.

### `US` ist kein MIC

`EXCHANGES` verwendet `US` als Sammelcode für NYSE/NASDAQ und OpenFIGI
`exchCode=US`. Das ist kein ISO-10383-MIC. Ein Feld namens `exchange_mic` darf
deshalb nicht gleichzeitig echte MICs und diesen internen Composite-Code
enthalten, ohne das ausdrücklich zu modellieren.

### Suffix-Rückrechnung ist nicht universell verlustfrei

Die vorhandenen 33 Suffixe können eindeutig sein, aber daraus folgt nicht, dass
jedes künftig oder manuell gespeicherte Yahoo-Symbol eindeutig zerlegbar ist.
Zu berücksichtigen sind:

- unbekannte oder neu hinzugekommene Suffixe,
- suffixlose Nicht-US-Symbole,
- provider- oder nutzerspezifische Symbole,
- Punkte oder andere Zeichen, die Bestandteil des eigentlichen Tickers sind.

Der Contract-Test `assert "." not in antwort.ticker` ist deshalb zu streng. Ein
Punkt kann Teil einer legitimen Anteilsklassen-/Ticker-Schreibweise sein und ist
nicht automatisch ein Börsensuffix.

## 4. T-19 kann Historien verschiedener Listings vermischen

T-19 verlangt, beim Neu-Auflösen nur Symbol, Börse und Gattung zu ändern und
alle historischen Daten zu behalten. Die Tabellen `quotes` und
`daily_closes` speichern jedoch weder Listing noch Quelle. Beide hängen nur an
`instrument_id`.

Beispiel:

1. Ein Papier ist bisher als London-Listing in GBP gespeichert.
2. Neu-Auflösen wechselt auf Xetra in EUR.
3. Alte GBP- und neue EUR-Kurse landen unter derselben Instrument-ID und werden
   als eine Zeitreihe ausgegeben.
4. `daily_meta` behauptet weiterhin, Zeiträume des neuen Listings seien bereits
   synchronisiert.

Das Ergebnis sieht plausibel aus, ist fachlich aber falsch. Besonders
Volatilität und Charts können dadurch verfälscht werden.

Mögliche Lösungen:

- Listing-Versionen/-Generationen einführen und Historie daran binden.
- Alte Listing-Historie archivieren und für das neue Listing eine neue Serie
  beginnen.
- Mindestens `daily_closes` und `daily_meta` beim Listingwechsel invalidieren;
  Quote-Historie sichtbar nach Listing/Währung segmentieren.

„Kein Datenverlust“ darf nicht mit „unterschiedliche Messreihen unverändert
zusammenführen“ gleichgesetzt werden.

## 5. Metadatenvertrag, Merge-Regeln und Persistenz sind inkonsistent

`Reading` trägt die Herkunft pro Feld. Das Design begründet dies damit, dass
mehrere Quellen dasselbe Papier ergänzen können. Die heutige Persistenz besitzt
aber nur:

- ein gemeinsames `instruments.source`,
- einen gemeinsamen `meta_fetched_at`,
- das grobe Flag `QuoteResponse.metadata_complete`,
- eine feste Menge von Metadatenspalten.

Damit lässt sich beispielsweise „TER von Quelle A, Anbieter von Quelle B“ nicht
dauerhaft korrekt erklären. Auch ein Ausfall einer Quelle kann nicht je Feld
von „nicht geliefert“ oder „bewusst leer“ unterschieden werden.

Vor der Registry müssen Merge- und Löschregeln definiert werden:

- Gewinnt pro Feld die erste Quelle, die einen Wert liefert?
- Darf eine leere Liste alle von dieser Quelle deklarierten Felder löschen?
- Bedeutet ein fehlendes Reading „nicht geführt“, „nicht gefunden“ oder
  „bestehenden Wert behalten“?
- Wie werden Ergebnisse mehrerer Quellen und deren Zeitstempel gespeichert?
- Was geschieht, wenn eine höher priorisierte Quelle ausfällt, eine niedrigere
  aber einen Wert liefert?

Pragmatische Anfangslösung: feste bekannte Feldmenge, kanonischer Feldkatalog
und Provenienz/Aktualisierungsstatus je Feld.

### Offene Feldmenge widerspricht sich

Das Design sagt in `docs/...plugin-system-design.md:161-166`, dass unbekannte
Felder verworfen werden. `FieldSpec` und `MetadataContract` sind dagegen darauf
ausgelegt, neue Felder samt Labels einzuführen. Auch der offene Punkt zu
Plugin-Labels setzt neue sichtbare Felder voraus.

Es muss eine Variante gewählt werden:

- zunächst nur bekannte Felder: Feldkatalog gehört in den Vertrag und neue
  Labels sind nicht nötig, oder
- offene Felder: generische Persistenz, API-Modelle und Dashboard-Darstellung
  müssen vor dem Plugin-System vorhanden sein.

### Einheitenmodell ist noch unvollständig

`FieldSpec.unit` und `Reading.unit` beschreiben beide die Quelleneinheit; der
Contract-Test verlangt sogar Identität. Das kanonische Umrechnungsziel der App
ist jedoch nicht Teil des Vertrags.

Zusätzlich:

- `Unit.ABSOLUTE` verlangt laut Kommentar eine Währung, `Reading` besitzt aber
  kein Währungsfeld.
- `MILLIONS` lässt sich durch `convert()` nicht in `ABSOLUTE` umrechnen.
- Plausibilitätsbereiche sollen laut Dokumentation nach der Umrechnung gelten;
  das Beispiel testet den Bereich dagegen auf dem Rohwert in Basispunkten.

Empfehlung: kanonische Einheit und Wertebereich in einem App-/API-Feldkatalog,
Quelleneinheit am Reading und explizite Währung für Geldbeträge.

## 6. Ein gemeinsamer `ResolveRequest` reicht nicht für Metadaten

`MetadataSource.fetch()` verwendet derzeit ebenfalls `ResolveRequest`. Dieser
enthält ISIN, ein unspezifiziertes `symbol` und `preferred_mic`, aber nicht das
tatsächlich aufgelöste Listing.

Das kollidiert mit T-18 und T-21:

- Metadaten sollen auch ohne ISIN anhand von Börse oder Währung zuständig sein.
- Nach T-21 soll ein Plugin keine Yahoo-Symbole verstehen müssen.
- `preferred_mic` ist nicht dasselbe wie der tatsächliche MIC des Listings.

Empfehlung: eigener `MetadataRequest` mit mindestens `isin`, `ticker`, `mic`,
`instrument_type` und gegebenenfalls Handelswährung. Provider-Aliase sollten
nicht als kanonisches `symbol` hineingereicht werden.

## 7. Ergebnisaggregation ist noch nicht eindeutig definiert

Die vier Resolver-Antworten sind sinnvoll. Für eine Registry fehlen aber einige
Regeln, unter anderem:

- Was ist das Gesamtergebnis bei `NotFound` von Quelle A und `Unavailable` von
  Quelle B? Ohne erfolgreiche Antwort kann 404 falsch sein, weil nicht alle
  zuständigen Quellen nachsehen konnten.
- Wird ein Erfolg einer Fallback-Quelle nach einem Ausfall als degradiert
  sichtbar gemacht?
- Wann und wie lange öffnet ein Circuit-Breaker?
- Wie wird er thread-sicher zurückgesetzt?
- Gilt der Fehlerzähler je Quelle, je Rolle oder je Instrument/Markt?
- Welche Fehlermeldungen dürfen an API und Logs gelangen?

Insbesondere rohe Exceptions dürfen keine URLs mit Query-API-Keys oder
Header-Inhalte offenlegen.

## 8. Registry- und Konfigurationsvertrag brauchen Präzisierung

### `is_configured()` kann keinen Grund liefern

T-19 und `/sources` verlangen bei `configured: false` eine Begründung.
`Source.is_configured()` liefert jedoch nur `bool`. Dafür braucht es entweder
ein strukturiertes Ergebnis oder eine zusätzliche Diagnosemethode.

### OpenFIGI-Key ist optional

Der aktuelle `OpenFigiClient` dokumentiert den Key als optional und sendet ihn
nur, wenn er vorhanden ist (`app/providers/openfigi_provider.py:24-50`). T-22
Verify #2 erwartet dagegen, dass OpenFIGI ohne Key `configured: false` ist.
Diese Erwartung widerspricht dem Ist-Verhalten und würde die anonyme,
limitierte Nutzung unnötig abschalten.

### Reihenfolge gegen Kosten

Das Design sagt, `sources.yaml` bestimme Auswahl und Reihenfolge.
`Source.cost` sagt zugleich, die Kostenklasse steuere die Reihenfolge. T-22
spricht zusätzlich von Priorität und alphabetischem Tie-Breaker.

Es muss genau eine Regel festgelegt werden, beispielsweise:

1. explizite Reihenfolge in `sources.yaml` gewinnt immer,
2. Kosten dienen nur als Information/Warnung,
3. alphabetische Sortierung wird nur für nicht explizit konfigurierte Quellen
   verwendet.

### Fehlende Registry-Regeln

Noch zu definieren sind:

- Name der Entry-Point-Gruppe,
- ob ein Entry-Point Klasse, Factory, Instanz oder Liste liefert,
- Verhalten bei doppelten Quellennamen,
- Verhalten bei Import-/Konstruktorfehlern,
- exakter Versionsvergleich,
- Lifecycle und Aufruf von `Source.close()`,
- Thread-Sicherheit gemeinsam genutzter Multi-Rollen-Instanzen,
- Verhalten, wenn nach Ablehnungen keine Quelle für eine Pflichtrolle übrig
  bleibt.

## 9. Entry-Points passen noch nicht zum Deployment

Das Image installiert Dependencies während des Builds. Ein Anwender kann auf
dem Host nicht einfach `pip install stockinfo-resolver-ca` in das bereits
gebaute Image hinein installieren. Eine Installation in einem laufenden
Container ist bei Image-Update/Neuerstellung nicht dauerhaft und für Unraid
kein belastbares Betriebsmodell.

Mögliche Modelle:

- dokumentiertes Custom-Image mit zusätzlichen `pip install`-Schritten,
- Wheel-Verzeichnis im Daten-Volume und bewusstes Installieren beim Start,
- ausschließlich dateibasierte Plugins im Standard-Image,
- kuratierte Plugins bereits ins offizielle Image aufnehmen.

Ein automatisches Installieren aus dem Volume würde allerdings die im Design
betonte Aussage „keine Automatik, die von selbst etwas nachlädt“ berühren und
muss sicherheitlich klar benannt werden.

Dateibasierte `*.py`-Plugins können außerdem nur bereits im Image verfügbare
Dependencies zuverlässig importieren. Für komplexere Bibliotheken reicht ein
einzelnes `data/plugins/foo.py` nicht.

## 10. Deklarative Quellen: gute Grenze, aber Format und Threat-Model fehlen

Die Grenze „Pfadauswahl, Mapping, Einheiten und Zuständigkeit – keine
Bedingungen, Schleifen oder HTML-Selektoren“ ist sinnvoll. Das Beispiel reicht
aber noch nicht, um selbst die gemessenen Quellen vollständig abzubilden.

Erforderlich sind mindestens:

- HTTP-Methode,
- Query, JSON-Body, Form-Body und Headers,
- Authentifizierungs-/Secret-Referenzen,
- URL-Encoding der Platzhalter,
- Connect-/Read-/Gesamt-Timeout,
- maximale Antwortgröße,
- Redirect-Regeln,
- erlaubte Content-Types,
- JSON-Pfad-Syntax und Verhalten bei fehlenden/mehrdeutigen Treffern,
- Typkonvertierung,
- statische Wertetabellen, etwa Anbieter-Exchange-Code zu MIC,
- Statuscode-/Fehler-Mapping auf `NotFound` und `Unavailable`,
- Logging und Secret-Redaction,
- Schema-Version des Formats.

OpenFIGI benötigt beispielsweise `POST` mit einem JSON-Array; das gezeigte
Schema enthält weder Methode noch Body.

### Sicherheitsbehauptung abschwächen

Eine Beschreibungsdatei kann keinen beliebigen Python-Code ausführen. Sie kann
aber sehr wohl einen ihr bereitgestellten `{config.api_key}` an eine beliebige,
von ihr definierte URL senden. Je nach HTTP-Client sind außerdem möglich:

- SSRF gegen lokale/interne Dienste,
- Redirects auf andere Hosts,
- sehr große oder komprimierte Antworten,
- Schlüssel in Query-URLs und Exception-Logs,
- Aufrufe von Cloud-Metadata-Endpunkten.

Deshalb sollte das Design „kein beliebiger Code“ statt „kein
Ausführungsrisiko/kein Schlüsselabzug“ versprechen. Notwendig sind `safe_load`,
Schema-Validierung, Größen-/Zeitgrenzen, Redirect-Policy, Secret-Redaction und
idealerweise eine Host-Policy.

## 11. Contract-Tests überversprechen derzeit

Die Contract-Test-Idee ist wertvoll, die vorhandenen Tests prüfen den Vertrag
aber noch nicht vollständig.

Beispiele:

- `api_version <= API_VERSION` akzeptiert auch `0` oder negative Versionen.
- Für kaputte Requests wird beim Resolver nur geprüft, dass das Ergebnis nicht
  `None` ist; ein beliebiger anderer Typ würde bestehen.
- MIC, ISIN, `instrument_type`, Whitespace und Feldtypen werden nicht umfassend
  validiert.
- Namen werden nicht auf das erlaubte Format oder globale Eindeutigkeit geprüft.
- `MetadataContract.test_neue_felder_tragen_eine_beschriftung` verlangt Labels
  für alle Felder, obwohl der Test gar nicht wissen kann, welches Feld für die
  App neu ist.
- Unzuständige Metadata-Quellen dürfen sowohl `[]` als auch `None` liefern;
  damit bleibt „nicht zuständig“ gegen „ausgefallen“ wieder uneindeutig.
- `NaN`, `inf`, boolesche Zahlenwerte und falsche Reading-Typen sind nicht
  systematisch abgedeckt.
- Der Punkt-im-Ticker-Test verwechselt mögliche Tickerzeichen mit einem
  Provider-Suffix.

Contract-Tests ersetzen außerdem keine Marktvalidierung. Sie beweisen Form und
Fehlerverhalten, nicht, dass das aufgelöste Instrument fachlich die korrekte
Gattung oder Notierung ist.

## 12. Weitere Kopplungen im vorhandenen Code

Neben den im Design genannten Instanziierungen sind weitere Stellen zu
berücksichtigen:

- `QuoteService` setzt `source="yfinance"` fest.
- `CachedFxService` setzt `source="yfinance"` fest.
- Tageskurse speichern aktuell keine Provider-Herkunft.
- `QuoteAnalyzer` kennt feste Stufen wie OpenFIGI und justETF.
- Repository-Lookups und zahlreiche API-Pfade identifizieren weiterhin über
  Yahoo-`symbol`.
- Der Scheduler und Request-Threadpool können dieselben Source-Instanzen
  gleichzeitig verwenden; Registry und Plugins brauchen eine klare
  Thread-Safety-Regel.

Diese Stellen müssen bei T-21 bis T-23 entweder migriert oder bewusst als
Kompatibilitätsschicht dokumentiert werden.

## 13. T-18: ISIN-Land zu Heimatbörse ist nur eine Heuristik

Das ISIN-Präfix bezeichnet die ausgebende Jurisdiktion bzw. Nummerierungsstelle,
nicht zwingend den gewünschten oder einzigen Handelsplatz. Länder können
mehrere Börsen haben; Fonds mit irischer ISIN werden beispielsweise an mehreren
europäischen Börsen gehandelt.

Die Kaskade „bevorzugte Börse → Börse aus ISIN-Land → beliebiges Listing“ kann
als Fallback sinnvoll sein, sollte aber ausdrücklich als Heuristik gelten. Die
gewählte Listing-Währung und Abweichung von der Präferenz müssen sichtbar
bleiben. Eine starre Land-zu-einem-MIC-Tabelle ist keine allgemeine
Identitätsregel.

## Test- und Verifikationsstand

Ausgeführt am 2026-08-19:

| Suite | Ergebnis |
|---|---:|
| Backend | 244 Tests bestanden |
| Dashboard | 230 Tests bestanden |
| Ruff für `plugin_api/` | bestanden |
| Plugin-API mit `PYTHONPATH=src:.` aus `plugin_api/` | 36 Tests bestanden |

Die Plugin-Suite ist nicht in `make test` integriert. Aus dem Repository-Root
scheitert sie an `examples.*`; aus `plugin_api/` scheitert sie ohne Installation
oder gesetzten `PYTHONPATH` an `stockinfo_plugin`. Damit prüft die reguläre CI
den öffentlichen Vertrag derzeit nicht.

## Empfohlene Freigabebedingungen

Vor der Umsetzung von T-21 bis T-23 sollten mindestens diese Entscheidungen im
Design feststehen:

1. Kanonische Listing-Identität und optionale Provider-Aliase.
2. Historienmodell bzw. Invalidierungsregel bei einem Listingwechsel.
3. Vollständige Rollenverträge für Resolver, Metadata, Quote, Daily und FX.
4. Eigener Request-Typ je Rolle, insbesondere für Metadaten.
5. Provenienz, Zeitstempel und Aktualisierungsstatus je Metadatenfeld.
6. Eindeutige Aggregationsregeln für die Result-Typen.
7. Prozess- oder Timeout-Modell für fremden Python-Code.
8. Entry-Point-, Lifecycle-, Namens- und Versionsregeln der Registry.
9. Praktisches Installationsmodell für Docker und Unraid.
10. Formales Schema und Threat-Model für deklarative Quellen.
11. Integration der Plugin-API-Tests in den normalen Testlauf.

## Schlussfolgerung

Das Vorhaben ist grundsätzlich tragfähig. Die Registry sollte aber nicht auf
dem aktuellen `1.0.0`-Vertrag und dem bestehenden Yahoo-zentrierten Schema
aufgebaut werden, bevor die obigen Punkte geklärt sind. Sonst entsteht zwar ein
Plugin-Lader, aber die Quellen bleiben in Identität, Persistenz, Fehlersemantik
und Deployment praktisch an den heutigen Sonderfällen gekoppelt.
