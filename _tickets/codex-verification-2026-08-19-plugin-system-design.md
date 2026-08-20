# Codex-Verifikation: Plugin-System-Design

**Datum:** 2026-08-19  
**Geprüft:** `docs/superpowers/specs/2026-08-19-plugin-system-design.md`,
Tickets T-17 bis T-23, `plugin_api/` und die betroffenen App-, Persistenz- und
Deployment-Codepfade.  
**Ergebnis:** Die Grundarchitektur ist sinnvoll, aber vor der Freigabe sind
mehrere Widersprüche und Architekturblocker zu klären.

> **Fortschreibung:** Die ursprüngliche Prüfung unten dokumentiert den Stand
> vom 2026-08-19. Claude hat anschließend wesentliche Punkte umgesetzt und die
> Spezifikation auf Python-only geändert. Die maßgebliche erneute Bewertung des
> aktuellen Stands steht am Ende unter „Nachprüfung der überarbeiteten
> Spezifikation am 2026-08-20“.

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

---

# Nachprüfung der überarbeiteten Spezifikation am 2026-08-20

**Geprüfter Stand:** Commit `a43364a` (`docs(specs): nur Python-Plugins — der
deklarative Weg entfällt`) und die darin neu formulierten „Offenen
Entscheidungen“.
**Anlass:** Festlegen, ob der deklarative Weg noch einen hinreichenden Nutzen
hat und wie Plugins so installiert werden, dass das System von normalen
Docker-/Unraid-Nutzern tatsächlich verwendet wird.

## Aktualisiertes Kurzurteil

Die Entscheidung **nur Python-Plugins, kein deklaratives Zweitformat** ist
richtig und sollte als abgeschlossen gelten. Die neue Spezifikation begründet
das ausreichend. Ein YAML-Interpreter für HTTP-Quellen wäre kein kleines
Mapping-Feature, sondern eine zweite, eingeschränkte Programmiersprache mit
eigenem Vertrag, eigener Security-Oberfläche und eigener Testmatrix.

Der offene Punkt **#9 Installation über ein abgeleitetes Docker-Image** ist
dagegen aus Produktsicht nicht akzeptabel. Er widerspricht dem Ziel, dass lokale
Marktkenntnis unkompliziert in die App gelangen soll. Wer zunächst ein
Dockerfile schreiben, ein Image bauen, eine Registry bedienen und sein
Unraid-Template auf ein eigenes Image umstellen muss, wird in der Regel kein
Plugin installieren. Dann ist die technische Erweiterbarkeit vorhanden, aber
praktisch wirkungslos.

## Entscheidung zum deklarativen Format: streichen

Der gestrichene deklarative Weg hatte drei behauptete Vorteile: geringere
Einstiegshürde, geringeres Risiko und einfaches Reloading. Keiner davon trägt
genug, um ein zweites Plugin-System zu rechtfertigen:

- Mit Contract-Tests, Vorlage und KI-Unterstützung ist ein kleiner
  Python-Adapter heute kein relevantes Hindernis mehr.
- YAML kann zwar keinen beliebigen Python-Code ausführen, aber weiterhin Keys
  exfiltrieren, interne HTTP-Dienste ansprechen und unkontrollierte Antworten
  erzeugen. Der Sicherheitsgewinn ist real, aber viel kleiner als zunächst
  angenommen.
- Laufzeit-Reload ist für Datenquellen kein zentraler Anwendungsfall. Ein
  Container-Neustart nach Installation oder Konfigurationsänderung ist
  vertretbar.
- Zwei Formate verdoppeln Dokumentation, Tests, Fehlerbilder und
  Kompatibilitätsarbeit.
- Sonderfälle wie mehrstufige Authentifizierung, Anbieter-Code-Tabellen,
  Pagination oder herstellerspezifische Fehlerantworten landen früher oder
  später doch in Python.

**Empfehlung an Claude:** Diesen Punkt in „Offene Entscheidungen“ nicht wieder
öffnen. Python-only ist die einfachere und langfristig belastbarere
Produktentscheidung. Die frei werdende Komplexität sollte vollständig in eine
sehr einfache Installation und eine hervorragende Plugin-Vorlage investiert
werden.

## Installation: Das abgeleitete Image als Standardweg verwerfen

Die aktuelle Empfehlung in Entscheidung #9 lautet sinngemäß: Anwender bauen ein
abgeleitetes Image mit zusätzlichen `pip install`-Schritten. Dieser Weg ist für
Plugin-Autoren und CI sinnvoll, aber nicht als normaler Installationsweg für
Self-Hoster.

Konkrete Nachteile:

- Der Nutzer braucht Dockerfile-, Build- und Registry-Kenntnisse.
- Multi-Arch-Builds für amd64/arm64 werden sein Problem.
- Offizielle StockInfo-Updates müssen in das eigene Image nachgezogen werden.
- Das bestehende Unraid-Template kann nicht mehr unverändert verwendet werden.
- Fehlersuche verteilt sich auf StockInfo, das abgeleitete Image und die
  Plugin-Abhängigkeiten.
- „`pip install …`“ klingt einfach, findet im aktuellen unveränderlichen
  Image-Modell aber nicht dauerhaft statt.

Ein abgeleitetes Image darf als reproduzierbare Expertenoption dokumentiert
werden, aber nicht als primärer Nutzerweg.

## Empfohlenes Installationsmodell

### Nutzererlebnis

Für einen normalen Nutzer sollte die Installation genau so aussehen:

1. Plugin-Paket mit fester Version in `data/sources.yaml` eintragen.
2. Die vom Plugin bereitgestellte Quelle in der gewünschten Kette eintragen.
3. Container neu starten.
4. `/sources` zeigt installiert/geladen/aktiv oder eine konkrete Fehlermeldung.

Beispiel:

```yaml
plugins:
  packages:
    - stockinfo-source-eodhd==1.2.3

resolvers: [eodhd, openfigi, yahoo-search]
quotes: [eodhd, yfinance]

providers:
  eodhd:
    api_key: ${EODHD_API_KEY}
```

Damit bleiben Installation, Aktivierung, Reihenfolge und Konfiguration in
**einer** Datei. Secrets bleiben weiterhin in der Umgebung. Die Datei kann ohne
Schlüssel in ein Issue kopiert werden.

### Technische Umsetzung

Das vorhandene persistente `/data`-Volume eignet sich bereits als
Installationsziel:

1. Ein kleiner StockInfo-Launcher liest vor dem Import der App ausschließlich
   die explizite Paketliste aus `sources.yaml`.
2. Aus der normalisierten Liste wird ein Hash gebildet.
3. Existiert `/data/plugin-envs/<hash>/`, wird es ohne Netzwerkzugriff erneut
   verwendet.
4. Andernfalls installiert der Launcher die Pakete in ein temporäres
   Zielverzeichnis unter `/data`, prüft den Erfolg und benennt es anschließend
   atomar nach `<hash>` um.
5. Dieses `site-packages`-Verzeichnis wird dem Python-Suchpfad hinzugefügt;
   danach startet die App und entdeckt die Entry-Points.
6. Ändert sich die Liste, entsteht eine neue Umgebung. Eine fehlgeschlagene
   Installation beschädigt die zuletzt funktionierende Umgebung nicht.

Das überlebt Container- und Image-Updates, weil nur `/data` beschrieben wird.
Der Installer muss als unprivilegierter App-User laufen und darf nicht die
systemweite Python-Installation verändern.

### Sicherheits- und Reproduzierbarkeitsregeln

- Nur ausdrücklich in `sources.yaml` genannte Pakete werden installiert.
- Exakte Versionen (`==`) sind für externe Pakete Pflicht; kein stilles
  „latest“ bei jedem Neustart.
- Für den einfachen und vorhersehbaren Anfang nur Wheels akzeptieren
  (`--only-binary=:all:`); keine Source-Build-Toolchain im Produktionsimage.
- Der Plugin-API-Vertrag des Basisimages wird per Constraint geschützt, damit
  ein Plugin keine zweite inkompatible Vertragskopie vor die App legt.
- Paketname, Version, Installationszeitpunkt und Ladefehler erscheinen in
  `/sources`, niemals Secrets oder vollständige Auth-URLs.
- Installation bedeutet noch nicht Aktivierung: Nur eine in der jeweiligen
  Kette genannte Source darf aufgerufen werden.
- Bei geänderter Paketliste und fehlgeschlagener Installation sollte der Start
  klar fehlschlagen oder sichtbar degradiert sein; niemals still mit einer
  anderen als der gewünschten Plugin-Menge weiterlaufen.

Das ist weiterhin eine Vertrauensentscheidung: Ein installiertes Python-Paket
hat App-Rechte. Sie ist aber **explizit** durch den Eintrag des Nutzers und nicht
das Ergebnis eines automatisch abgefragten Marketplace-Katalogs.

### Drei Nutzungsebenen, aber nur ein Plugin-Vertrag

Die Distribution darf mehrere Komfortstufen haben, ohne wieder mehrere
Plugin-Arten einzuführen:

1. **Mitgelieferte/kuratierte Quellen:** Bereits im offiziellen Image; der
   Nutzer aktiviert sie nur in `sources.yaml`. Das ist für häufige Anbieter der
   einfachste Weg.
2. **Paketierte Drittanbieter-Plugins:** Paketzeile in `sources.yaml`, Neustart;
   Installation persistent nach `/data` wie oben.
3. **Lokale Entwicklung:** `data/plugins/*.py`, Neustart. Dieser Weg ist für
   Experimente und einfache Plugins ohne zusätzliche Bibliotheken gedacht.

Alle drei Wege liefern dieselben `Source`-Klassen an dieselbe Registry und
verwenden dieselben Contract-Tests. Es sind Distributionswege, keine getrennten
Plugin-Systeme.

## Alternative Minimalvariante

Falls der persistente Paketinstaller für T-23 zunächst zu groß ist, ist die
ehrlichere erste Ausbaustufe:

- häufige kuratierte Plugins in das offizielle Image aufnehmen,
- lokale Einzeldateien aus `/data/plugins/` laden,
- Entry-Point-Installation als Expertenweg zurückstellen.

Auch das ist für Nutzer sinnvoller als ein abgeleitetes Image als einziger Weg.
Es begrenzt zunächst die Zahl installierbarer Pakete, erhält aber ein klares und
funktionierendes Betriebsmodell.

## Bewertung der zehn offenen Entscheidungen

| # | Bewertung nach erneuter Prüfung |
|---|---|
| 1 | **Zustimmung.** `(ticker, mic)` kanonisch; Yahoo-Alias optional und nicht eindeutig. Provider-Aliase langfristig separat modellieren. |
| 2 | **Zustimmung mit Präzisierung.** Historie bei Listingwechsel nicht mischen. Für den ersten Schritt löschen/invalidieren; Archivierung nur, wenn sie sichtbar nach Listing getrennt wird. Manuelle Kennzahlen behalten. |
| 3 | **Zustimmung.** Alle fünf Rollen vor einer stabilen API; bis dahin `0.x`. Das Runtime-Paket muss zusätzlich in App und Image installiert werden. |
| 4 | **Zustimmung.** Eigener `MetadataRequest` mit tatsächlichem Ticker/MIC statt Yahoo-Symbol oder nur `preferred_mic`. |
| 5 | **Nur als bewusste MVP-Grenze akzeptabel.** Ein gemeinsames `source` bedeutet: keine feldweise Kombination mehrerer Metadatenquellen versprechen. `Reading.source` und Dokumentation müssen dazu passen oder als rein flüchtige Diagnose gelten. |
| 6 | **Präzisieren.** `Unavailable` schlägt `NotFound` nur, wenn keine Quelle erfolgreich war. Sobald irgendeine Quelle erfolgreich auflöst, ist das Gesamtergebnis Erfolg; vorherige Ausfälle können höchstens als Degradation protokolliert werden. |
| 7 | **Zustimmung.** Kooperative Timeouts, ehrliche Dokumentation, Circuit-Breaker nur gegen Folgeaufrufe. Verify #5 in T-23 muss entsprechend geändert werden. |
| 8 | **Nicht vollständig vertagen.** Details entstehen in T-23, aber Entry-Point-Gruppe, geliefertes Objekt, Namenskollisionen, Versionsregel, Aktivierung und `close()` sind Abnahmekriterien dieses Tickets und müssen vor Implementierungsende feststehen. |
| 9 | **Ablehnung der aktuellen Empfehlung.** Abgeleitetes Image nur Expertenoption; Standardweg über explizite Paketliste und persistente Plugin-Umgebung in `/data`. |
| 10 | **Bestätigt erledigt.** `make test-plugin-api` läuft mit 36 bestandenen Tests und ist Teil von `make test`. |

## Inkonsistenzen, die Claude noch korrigieren sollte

1. Die Unterüberschriften unter „Offene Entscheidungen“ verwenden falsche
   Nummern: „Zu 6 — was `is_configured()` nicht kann“ gehört nicht zur
   Tabellenentscheidung #6; „Zu 2 — Reihenfolge gegen Kosten“ gehört nicht zur
   Tabellenentscheidung #2. Besser ohne Nummer oder mit eigenen stabilen IDs.
2. T-23 Verify #5 behauptet weiterhin eine greifende harte Zeitgrenze, obwohl
   die Spezifikation kooperative Timeouts empfiehlt. Das Prüfkriterium muss auf
   „Plugin setzt/benutzt begrenzte I/O-Zeit; Circuit-Breaker verhindert weitere
   Aufrufe nach Fehlern“ geändert werden, ohne einen nicht erzwingbaren Abbruch
   zu versprechen.
3. T-22 Verify #2 behauptet weiterhin, OpenFIGI sei ohne Key
   `configured: false`. Die Spezifikation erklärt inzwischen korrekt das
   Gegenteil. Ticket und Spec sind noch nicht synchron.
4. `Source.cost` dokumentiert weiterhin, dass es die Reihenfolge steuere. Die
   neue Spezifikation bestimmt dagegen ausdrücklich `sources.yaml` als einzige
   Reihenfolge und `cost` nur als Information. Der öffentliche Vertrag muss
   angepasst werden.
5. `Source.__init__` behauptet, ein Python-Plugin habe keinen Zugriff auf
   App-Einstellungen, Datenbank oder andere Quellen. Das ist keine
   Sicherheitsgrenze: Fremder Python-Code kann Umgebung und Dateisystem lesen.
   Gemeint sein kann nur, dass die App diese Interna nicht als stabilen Vertrag
   übergibt.
6. Der Text „keine Automatik, die von selbst etwas nachlädt“ muss von einer
   explizit konfigurierten Installation unterschieden werden. Ein vom Nutzer
   gepinntes Paket aus `sources.yaml`, das beim Neustart installiert wird, ist
   kein selbsttätiger Marketplace-Download.

## Aktualisierte Freigabeempfehlung

Die Python-only-Entscheidung kann freigegeben werden. Das gesamte Design sollte
aber erst freigegeben werden, wenn Entscheidung #9 ersetzt und der gewünschte
Nutzerablauf als Verify-Kriterium in T-23 festgehalten ist.

Der wichtigste End-to-End-Test lautet:

> Ein Unraid-/Docker-Nutzer trägt ein versioniertes Plugin und seine Source in
> `sources.yaml` ein, startet den unveränderten offiziellen Container neu und
> sieht die Quelle anschließend in `/sources` als geladen und aktiv — ohne
> eigenes Dockerfile, eigenes Image oder manuelles `pip` im Container.

Wenn dieser Ablauf nicht erfüllt ist, ist das Plugin-System technisch vorhanden,
aber für den vorgesehenen Community-Effekt zu schwer zugänglich.

---

# Antwort an Claude auf die drei Rückfragen vom 2026-08-20

**Bezug:** `docs/superpowers/specs/2026-08-19-plugin-system-design.md`, Abschnitt
„Was ich zurückgebe“, Commit `cf6bf42`.

## 1. T-19: Kursreihen löschen, nicht archivieren

Für die erste belastbare Umsetzung empfehle ich **löschen**. Eine dauerhaft
abfragbare Archivierung über Listing-Generationen ist fachlich sauber, aber für
den derzeitigen Anwendungsfall unverhältnismäßig:

- Jede History-Abfrage, Volatilitätsberechnung und Cache-Synchronisierung müsste
  eine aktive Generation beachten.
- API und Oberfläche müssten entscheiden, ob und wie alte Listings sichtbar
  werden.
- Für einen sehr seltenen Korrekturvorgang entstünde dauerhaft Komplexität in
  allen normalen Lesewegen.
- Ein Archiv, das nirgends lesbar ist, ist nur versteckte Aufbewahrung und kein
  funktionales Feature.

Das heutige Löschen des gesamten Instruments ist trotzdem zu grob. Beim
bestätigten Listingwechsel sollte **in einer Transaktion** gelten:

- `quotes` löschen,
- `daily_closes` löschen,
- `daily_meta` löschen/zurücksetzen,
- abgeleitete Volatilität und listingabhängige Cache-Werte zurücksetzen,
- maschinell geladene Metadaten als veraltet markieren bzw. neu laden,
- Instrument-ID, ISIN, `first_seen` und `instrument_overrides` behalten,
- neues Listing und `resolved_by` schreiben.

Warum auch maschinell geladene Metadaten neu geprüft werden sollten: Der
Korrekturweg kann nicht sicher wissen, ob nur die Börse wechselte oder ob das
alte Symbol auf ein anderes Instrument bzw. eine falsche Gattung zeigte. Nur
die manuellen Overrides sind ausdrücklich menschlich bestätigt und müssen
garantiert erhalten bleiben.

### Destruktiver Wechsel braucht zwei Phasen

Die Formulierung im Ticket „der Endpunkt meldet zurück, damit die Oberfläche
vor dem Verwerfen fragen kann“ reicht technisch nicht. Der Server darf nicht
erst mutieren und danach fragen lassen.

Empfohlenes Verhalten:

1. **Preview:** Neu auflösen, altes und vorgeschlagenes Listing vergleichen,
   Zahl der betroffenen Quote-/Daily-Zeilen und die Konsequenz zurückgeben; noch
   nichts schreiben.
2. **Confirm:** Client bestätigt mit erwartetem alten Listing bzw. einem kurzen
   Preview-Token. Der Server prüft, dass sich der Stand nicht geändert hat, und
   führt Wechsel plus Invalidierung atomar aus.
3. Ist das Listing unverändert, ist keine destruktive Bestätigung nötig.

Die Oberfläche muss ausdrücklich sagen, wie viele gespeicherte Kurs- und
Tagesschlusswerte entfernt werden. Ein späterer echter Bedarf kann eine
Exportfunktion oder Listing-Generationen rechtfertigen; er sollte nicht vorsorglich
in alle Abfragen eingebaut werden.

**Entscheidung:** Für T-19 löschen, transparent bestätigen, manuelle Werte
behalten. Archivierung bleibt ein separates zukünftiges Feature und ist keine
Voraussetzung für das Plugin-System.

## 2. `US`: echter MIC im Vertrag, Composite-Code separat

Empfehlung: **Das kanonische Feld bleibt `mic` und enthält ausschließlich echte
ISO-10383-MICs.** Es sollte nicht neutral in `exchange_code` umbenannt werden,
denn ein untypisierter Code verschiebt das Problem zu jedem Quote-/Daily-Plugin:
Niemand weiß dann, ob `US` ein MIC, OpenFIGI-`exchCode`, Yahoo-Code oder
Anbietercode ist.

Ebenso falsch wäre, `US` pauschal auf `XNYS` oder `XNAS` zu mappen. Das wäre
geraten und für viele Instrumente falsch, etwa NYSE Arca oder andere
US-Handelsplätze.

Die saubere Trennung lautet:

- `mic` ist die kanonische, providerunabhängige Listing-Identität.
- OpenFIGI-`exchCode=US` ist nur ein **provider-spezifischer Suchraum** bzw. eine
  Resolver-Konfiguration, kein Ergebnis-MIC.
- Ein OpenFIGI-Resolver darf `US` intern verwenden, muss vor einem erfolgreichen
  `Resolved` aber einen tatsächlichen MIC ermitteln — durch eine gezielte
  `micCode`-Abfrage, einen validierten Mapping-Schritt oder eine andere Quelle.
- Kann keine Quelle den konkreten MIC bestimmen, darf die Registry keinen
  erfundenen MIC speichern. Das Ergebnis ist unvollständig und muss an einen
  anderen Resolver bzw. in einen sichtbaren manuellen Korrekturweg gehen.

Der offizielle OpenFIGI-v3-Vertrag bestätigt die Trennung: `exchCode` und
`micCode` sind alternative Request-Filter; die Mapping-Antwort enthält unter den
Instrumentattributen `exchCode`, aber keinen zurückgegebenen `micCode`. Das
Beispiel für IBM liefert `exchCode: "US"`. `US` bezeichnet damit gerade nicht
den tatsächlichen Listing-MIC. Quelle:
[OpenFIGI API Documentation](https://www.openfigi.com/api/documentation).

### Konsequenz für Migration und T-18

- `EXCHANGES` sollte nur echte MIC-Einträge enthalten.
- Provider-spezifische Suchgruppen wie OpenFIGI `US` gehören in den jeweiligen
  Provider/Resolver, nicht in die Börsentabelle.
- T-18 sollte für ein Land eine **geordnete Liste** möglicher echter MICs bzw.
  einen Resolver-Fallback definieren, nicht `US` als Pseudo-MIC.
- Suffixlose Bestands-Symbole dürfen bei der Migration nicht automatisch als
  `mic=US` oder pauschal als `XNAS`/`XNYS` gespeichert werden. Sie müssen live
  neu bestimmt oder zur manuellen Zuordnung gemeldet werden.

Falls später bewusst auch Composite-Märkte als erstklassige Identität gebraucht
werden, braucht es einen typisierten Wert wie
`MarketRef(scheme="openfigi_exch", code="US")`. Ein neutrales String-Feld ohne
Schema ist keine Lösung. Für den jetzigen Vertrag sollte diese zusätzliche
Abstraktion vermieden und ein echter MIC verlangt werden.

**Entscheidung:** Echte MICs speichern; `US` als internen OpenFIGI-Suchcode
behalten; niemals raten und niemals beide Codearten unter demselben Feld führen.

## 3. Reihenfolge der Umsetzung

**T-17 muss zuerst kommen.** Es korrigiert aktive stille Datenverfälschung und
ist von der Plugin-Architektur unabhängig.

T-19 würde ich entgegen Claudes Vorschlag **nicht direkt danach** umsetzen. Der
aktuelle Zustand löscht bei einer bewussten Korrektur zu viel, beschädigt aber
nicht von selbst laufend Daten. Vor allem benötigt die neue T-19-Fassung zwei
Grundlagen:

- T-21 für den belastbaren Vergleich der kanonischen Listings,
- T-20 für die Unterscheidung zwischen `NotFound` und einem ausgefallenen
  Resolver während Preview/Neu-Auflösung.

Ohne T-21 müsste T-19 noch über Yahoo-Symbol und Freitext-Börse vergleichen und
kurz danach erneut umgebaut werden. Ohne T-20 kann der Korrekturweg einen
Upstream-Ausfall nicht sauber vom fachlichen Nichtfinden unterscheiden.

Empfohlene Reihenfolge:

1. **T-17** — aktive stille Datenfehler beheben.
2. **T-21** — kanonisches Listing und Migration schaffen; `US`-Frage dabei wie
   oben lösen.
3. **T-20** — differenzierte Resolver-Ergebnisse auf der neuen Identität in die
   App ziehen. T-20 und T-21 dürfen als eng gekoppelte Arbeitseinheit geplant
   werden, falls das weniger Zwischenadapter erzeugt.
4. **T-19** — Preview/Confirm und sichere Invalidierung auf stabiler Identität
   und Fehlersemantik bauen.
5. **T-18** — Markt-Fallbacks auf echte MICs und differenzierte Ergebnisse
   umstellen, statt die heutige Yahoo-Kopplung auszubauen.
6. **Fehlende Verträge für Quote, Daily und FX** samt Runtime-Installation des
   Vertragspakets ausformulieren.
7. **T-22** — Konfiguration und Ketten.
8. **T-23** — Registry, Installation und Fremdplugins als Schlussstein.

Wenn T-19 aus Produktgründen unbedingt unmittelbar nach T-17 kommen soll,
sollte es nur als kleiner Übergangsfix umgesetzt werden: manuelle Overrides vor
dem heutigen Delete sichern und danach wieder zuordnen. Ein vollständiger
Neu-Auflösen-Workflow auf Basis des Yahoo-Symbols würde dagegen Wegwerfcode
erzeugen und sollte vermieden werden.

### Dabei sichtbar gewordene Ticket-Abhängigkeit

T-20 behauptet derzeit „hängt an nichts“, will aber direkt
`stockinfo_plugin.types.Resolved` übernehmen; dieser Typ enthält bereits
`ticker + mic`, während die App noch `ResolvedInstrument(symbol=...)` verwendet.
T-20 und T-21 sind damit praktisch gekoppelt. Entweder:

- T-21 schafft zuerst das neue Listingmodell und T-20 übernimmt danach die
  Result-Typen, oder
- beide Tickets werden als eine migrationsfähige Einheit geplant.

Die aktuelle Dokumentation sollte diese reale Abhängigkeit nennen, statt zwei
scheinbar unabhängige Tickets zu versprechen.

## Kleine Restkorrekturen im aktuellen Stand

Unabhängig von den drei Entscheidungen sind noch drei Textstellen nicht ganz
synchron:

1. Die Spec behauptet bei den Contract-Tests weiterhin, ein Börsensuffix im
   Ticker werde gefangen. Der Punkt-Test wurde zu Recht entfernt; aktuell kann
   der Contract das ohne Börsentabelle nicht allgemein erkennen.
2. Die Reihenfolgetabelle nennt T-19 weiterhin „verlustfreies Neu-Auflösen“.
   Tatsächlich ist das neue Ziel ein transparenter, bestätigter Verlust
   listingabhängiger Cache-Daten ohne Verlust manueller Werte.
3. T-23 „Isolation“ spricht weiterhin von einer gekapselten „Zeitgrenze“. Bei
   kooperativen Timeouts setzt jedoch das Plugin selbst seine I/O-Grenzen; die
   Registry kann nur Exceptions abfangen und Folgeaufrufe per Schutzschalter
   verhindern.

Diese Punkte ändern die Architekturentscheidung nicht, sollten aber vor der
Freigabe bereinigt werden.

---

# Ergänzung aus Nutzersicht: Backup und Wahrscheinlichkeit eines Listingwechsels

**Input von Mike am 2026-08-20:** Der Listingwechsel ist ein extrem kritischer
Zeitpunkt. Der Nutzer sollte darauf hingewiesen werden und vorher ein Backup
erstellen. Außerdem ist zu prüfen, wie realistisch der Fall überhaupt ist, dass
ein Bestand unter Plugin A aufgebaut wurde, Plugin B andere Listings verwendet
und der Nutzer trotzdem den Erhalt der Daten erwartet.

## Ein Backup ist Rollback, keine Datenmigration

Der Hinweis auf ein Backup ist richtig, aber der Ablauf muss präzise formuliert
werden:

- **Vor** dem bestätigten Listingwechsel wird eine konsistente Sicherung der
  Datenbank erstellt.
- Bei erfolgreichem und gewünschtem Wechsel wird dieses Backup **nicht** wieder
  eingespielt.
- Nur wenn der Wechsel rückgängig gemacht werden soll, wird das vollständige
  Backup wiederhergestellt. Damit kehren auch altes Listing und alter
  Konfigurationsstand zurück.

Ein vollständiges Datenbank-Backup nach einem erfolgreichen Wechsel wieder
einzuspielen würde den Listingwechsel selbst rückgängig machen. Nur die alten
Kurszeilen aus dem Backup in das neue Listing zurückzukopieren wäre keine
Wiederherstellung, sondern genau die fachlich falsche Vermischung, die T-19
verhindern soll.

### Empfehlung für die Oberfläche

Der Preview-/Confirm-Ablauf sollte die Kritikalität sichtbar machen:

> Das Handelslisting wechselt von `EUNL / XLON / GBp` zu
> `EUNL / XETR / EUR`. 1.842 Kurswerte und 1.106 Tagesschlusswerte gehören zum
> alten Listing und werden entfernt. Manuelle Kennzahlen bleiben erhalten.
> Erstellen Sie vorher ein Backup, wenn Sie den gesamten Stand später
> zurücksetzen möchten.

Die Bestätigung sollte nicht als gewöhnlicher „OK“-Dialog erscheinen, sondern
altes und neues Listing, Währungen und Zahl der betroffenen Zeilen zeigen.

### Manuelles oder automatisches Backup

Mindestens erforderlich:

- dokumentierter Backup-Weg,
- ausdrückliche Bestätigung „Backup vorhanden / Löschung verstanden“,
- Hinweis, dass bei einer Dateikopie der SQLite-Datenbank der Container gestoppt
  sein muss, damit DB und WAL konsistent sind.

Nutzerfreundlicher und sicherer wäre eine automatische konsistente Sicherung
direkt vor dem bestätigten Wechsel, etwa über SQLite `Connection.backup()` nach
`/data/backups/stockinfo-before-resolve-<timestamp>.db`. Das ist keine
Listing-Archivarchitektur und verkompliziert normale History-Abfragen nicht. Es
ist nur eine vollständige Rollback-Sicherung für einen seltenen destruktiven
Vorgang.

Die eigentliche Änderung bleibt trotzdem transaktional. Das Backup schützt vor
einer später bemerkten fachlich falschen Entscheidung; die Transaktion schützt
vor einem technisch nur halb ausgeführten Wechsel.

## Wie realistisch ist der Fall?

Es sind drei verschiedene Vorgänge zu trennen.

### 1. Plugin B wird installiert, bestehendes Listing bleibt gleich

**Sehr realistisch.** Ein Nutzer wird erwarten, dass seine vorhandenen Daten
erhalten bleiben, wenn er beispielsweise von yfinance zu EODHD wechselt. Diese
Erwartung ist berechtigt.

Der Pluginwechsel darf deshalb bestehende Instrumente nicht automatisch neu
auflösen. Das gespeicherte kanonische Listing `(ticker, mic)` bleibt gepinnt;
Plugin B wird gefragt, genau dieses Listing zu bedienen. Kann es das nicht,
greift die konfigurierte Fallback-Quelle oder die App meldet die Quelle als
unzuständig/nicht verfügbar.

**Wichtig:** Installation, Aktivierung einer Quote-Quelle und Neu-Auflösung sind
drei getrennte Operationen. Keine davon darf die andere still auslösen.

### 2. Plugin B liefert dasselbe Listing, aber eine andere Kursreihe

**Ebenfalls realistisch und bisher unterschätzt.** Auch bei identischem
`ticker + mic + currency` können Anbieter unterschiedliche Zeitreihen liefern:

- adjusted gegen unadjusted close,
- andere Behandlung von Splits und Ausschüttungen,
- andere Handelskalender-/Zeitzonen-Grenzen,
- verzögerte gegen Echtzeit-Kurse,
- unterschiedliche Rundung oder Quote-Zeitpunkte.

Für die laufend gesammelten `quotes` sind geringe Quellenunterschiede meist
vertretbar, sollten aber pro Zeile als `source` nachvollziehbar sein. Für
`daily_closes` muss der Vertrag eindeutig festlegen, welche Serie geliefert
wird. Ein Source-Wechsel darf nicht unbemerkt adjusted und unadjusted Werte
zusammenführen.

Die Gleichheit des Listings allein beweist also noch nicht vollständig, dass
zwei historische Serien kompatibel sind. Mindestens erforderlich sind ein
festgelegter Daily-Preisbegriff und Quellenprovenienz; andernfalls sollte der
Wechsel der Daily-Quelle ebenfalls eine neue Synchronisierung auslösen.

### 3. Plugin B bzw. ein neuer Resolver wählt ein anderes Listing

**Als automatischer Vorgang sollte dieser Fall überhaupt nicht auftreten.** Ein
anderes Plugin kann andere Treffer bevorzugen, aber bestehende Instrumente
werden nicht automatisch re-resolved. Der Fall entsteht nur, wenn der Nutzer
ausdrücklich „Neu auflösen“ ausführt oder eine fehlerhafte Zuordnung korrigiert.

Dass ein Nutzer bei gleicher ISIN trotzdem zunächst Datenkontinuität erwartet,
ist menschlich durchaus realistisch: Für ihn ist es „dasselbe Wertpapier“.
Technisch sind London/GBp und Xetra/EUR jedoch verschiedene Messreihen. Genau
deshalb muss die Oberfläche die Differenz erklären und darf nicht auf
Finanzwissen des Nutzers vertrauen.

Die Wahrscheinlichkeit eines bewussten Listingwechsels ist gering; die
Schadenshöhe bei stiller Vermischung ist hoch. Das rechtfertigt einen seltenen,
deutlich markierten und bestätigungspflichtigen Sonderweg, aber keine komplexe
Listing-Generationslogik in jeder normalen Abfrage.

## Konsequenz für das Design

Die Plugin-Architektur sollte folgende Invariante ausdrücklich festhalten:

> Ein Quellen- oder Pluginwechsel ändert niemals automatisch die kanonische
> Listing-Identität eines bestehenden Instruments. Nur der gesonderte,
> bestätigungspflichtige Neu-Auflösen-Workflow darf das Listing ändern.

Daraus folgt:

1. Plugin B mit demselben Listing: vorhandene Daten bleiben grundsätzlich.
2. Plugin B kann das Listing nicht bedienen: Fallback/Fehler, kein stiller
   Listingwechsel.
3. Expliziter Listingwechsel: Preview, Warnung, konsistentes Backup,
   Bestätigung, transaktionale Invalidierung der inkompatiblen Reihen.
4. Backup-Restore: vollständiger Rollback auf das alte Listing, kein Merge in
   die neue Reihe.

Damit wird der realistische Nutzerwunsch „Plugin wechseln, Daten behalten“
erfüllt, ohne die unrealistische und gefährliche Zusage zu machen, Historien
verschiedener Listings seien austauschbar.

---

# Korrektur der Gewichtung nach Mikes Kanada-Szenario

**Input von Mike am 2026-08-20:** Ein Entwickler in Kanada probiert StockInfo
aus, stellt sofort fest, dass seine Assets mit den Default-Quellen nicht
funktionieren, schreibt daraufhin ein passendes Plugin und nimmt die Assets erst
danach erfolgreich auf. In der Datenbank existieren zu diesem Zeitpunkt keine
wertvollen Daten, die migriert werden müssten.

## Bewertung

Dieses Szenario ist nicht nur plausibel, sondern wahrscheinlich der
**primäre Community-Use-Case**, auf den die Plugin-Architektur zielt:

1. Nutzer testet ein oder wenige lokale Instrumente.
2. Default-Auflösung oder Default-Quelle scheitert bzw. liefert erkennbar das
   falsche Ergebnis.
3. Nutzer löscht den Teststand oder beginnt mit leerer Datenbank.
4. Nutzer entwickelt/installiert das lokale Plugin.
5. Erst mit funktionierender Quelle entsteht der echte Datenbestand.

In diesem Ablauf gibt es weder einen produktiven Wechsel von Plugin A zu B noch
eine erhaltenswerte Kursreihe. Die frühere Codex-Formulierung, ein
Pluginwechsel mit vorhandenem Bestand sei „sehr realistisch“, war als generelle
Nutzererwartung gemeint, hat aber den für dieses Vorhaben wichtigsten Ablauf zu
stark in den Hintergrund gerückt.

## Konsequenz: T-19 nicht übergewichten

T-19 ist ein sinnvoller Korrektur- und Sicherheitsweg, aber **keine
Voraussetzung dafür, dass der kanadische Entwickler sein Plugin bauen und
verwenden kann**. Das Plugin-System sollte nicht durch Backup-,
Listing-Generations- oder aufwendige Migrationslogik verzögert werden, die im
Hauptszenario gar nicht gebraucht wird.

Für den MVP genügt beim seltenen bestehenden Datenbestand:

- Ein installiertes Plugin wirkt auf neu aufzunehmende Instrumente.
- Bestehende Instrumente werden nicht automatisch neu aufgelöst.
- Wer ein bestehendes Instrument absichtlich neu auflösen will, bekommt eine
  deutliche Warnung: bei Listingwechsel werden die listingabhängigen Cache-Daten
  gelöscht.
- Die Dokumentation empfiehlt vor diesem seltenen destruktiven Vorgang ein
  vollständiges Backup.
- Kein Archiv, keine Listing-Generationen und zunächst kein automatischer
  Backup-/Restore-Workflow.

Eine automatische SQLite-Sicherung wäre Komfort, aber angesichts des jetzt
präzisierten Hauptszenarios keine Freigabebedingung für das Plugin-System.

## Revidierte Priorität

Die Umsetzung sollte stärker auf den tatsächlichen Erfolgsweg optimiert werden:

1. Aktuelle stille Datenfehler aus T-17 beheben.
2. Den Plugin-Vertrag und die kanonische Identität ausreichend stabilisieren.
3. Plugin-Installation, Vorlage, Contract-Tests und Registry so einfach machen,
   dass der kanadische Entwickler sein Plugin wirklich einsetzen kann.
4. T-19 als kleinen, ehrlichen destruktiven Korrekturweg umsetzen oder notfalls
   hinter den ersten funktionierenden Plugin-MVP stellen.
5. Erst bei beobachtetem Bedarf Backup-Automatik, Export oder Listing-Archive
   ergänzen.

Damit verschiebt sich auch die frühere Reihenfolge. T-19 muss nicht mehr
zwingend vor T-22/T-23 abgeschlossen sein, sofern zwei Invarianten bereits
gelten:

- Eine Plugin-Installation verändert bestehende Instrumente nicht automatisch.
- Ein bestehendes Instrument wird nur durch eine explizite Nutzeraktion neu
  aufgelöst.

## Erwartung an Datenübernahme, neu eingeordnet

Es bleiben zwei unterschiedliche Erwartungen:

- **Primär und wahrscheinlich:** Plugin wird entwickelt, bevor ein brauchbarer
  Datenbestand existiert. Keine Übernahme erforderlich.
- **Sekundär und möglich:** Eine lang genutzte Instanz wechselt später die
  Quelle. Dann erwartet der Nutzer bei unverändertem Listing nachvollziehbar
  Datenkontinuität; bei geändertem Listing ist eine Warnung und Löschung
  vertretbar.

Die Architektur soll den sekundären Fall nicht still beschädigen, sie muss ihn
aber nicht vorab mit einer aufwendigen Historienplattform lösen.

**Revidiertes Fazit an Claude:** Das Kanada-Szenario spricht dafür, T-19 zu
vereinfachen und gegebenenfalls nach dem Plugin-MVP zu liefern. Der Erfolg des
Vorhabens hängt viel stärker an einer reibungslosen Plugin-Erstellung und
Installation als an der verlustfreien Migration eines bereits gefüllten
Datenbestands zwischen unterschiedlichen Listings.

---

# Schärfung: Quellenprofil ersetzt Datenbankgeneration, REST-Vertrag bleibt stabil

**Input von Mike am 2026-08-20:** Plugin B ersetzt Plugin A vollständig. Vorher
wird die StockInfo-Datenbank nach einem üblichen, fortlaufend nummerierten
Backup-Schema gesichert; Plugin B beginnt mit einer frischen Datenbank. Beispiele
für Installationsprofile sind B für Kanada, C für Russland und A für Österreich
und Deutschland. StockInfo ist zugleich die REST-Datenbasis für StockPortfolio.
Dessen Basiszeile muss unabhängig vom aktiven Plugin stabil bleiben; die
aufklappbaren Details dürfen dynamisch sein. Nicht gelieferte Metadaten können in
StockInfo von Hand ergänzt werden und müssen als wirksame Werte per REST
ankommen.

## Zustimmung zum Betriebsmodell

Ja, mit dieser Präzisierung ist das Modell schlüssig und wesentlich einfacher:

1. Profil A läuft mit der aktiven Datenbank.
2. Profil B wird installiert und vollständig validiert.
3. Die Datenbank von A wird als nächste nummerierte Generation gesichert.
4. B startet mit einer neuen, leeren Datenbank.
5. Ein Restore der alten Datenbank wäre ein vollständiger Rollback **zu Profil
   A**, kein Import in B.

Damit gibt es beim Profilwechsel keine Listingmigration, keine Vermischung von
Kursreihen und keinen Grund für Listing-Generationen innerhalb derselben
Datenbank. Auch die manuellen Ergänzungen werden bewusst nicht übernommen; sie
bleiben mit dem alten Stand im Backup erhalten.

Das revidiert die bisherigen Überlegungen noch einmal deutlicher: **T-19 ist
nicht der Pluginwechsel-Workflow.** Ein explizites Neu-Auflösen eines einzelnen
Instruments innerhalb derselben Datenbank kann weiterhin als separater
Korrekturweg existieren. Es ist aber keine Voraussetzung dafür, A durch B zu
ersetzen.

## A, B und C sind besser als Quellenprofile zu verstehen

Dem Regionalmodell stimme ich zu. Der Nutzer wählt beim Deployment ein zu seinen
Märkten passendes Profil:

- Österreich/Deutschland: Profil A,
- Kanada: Profil B,
- Russland: Profil C.

„Profil“ ist hier präziser als „ein Python-Paket“, weil die bestehende Spec fünf
Rollen und geordnete Ketten kennt. Ein Kanada-Profil kann intern zum Beispiel
einen kanadischen Resolver, einen Kursanbieter und einen FX-Anbieter bündeln. Der
Nutzer sollte diese Bestandteile für den Normalfall nicht einzeln verdrahten
müssen.

Die Region ist eine **explizite Installationsentscheidung**, keine automatische
Ableitung aus Wohnsitz oder ISIN-Präfix. Ein Kanadier kann deutsche ETFs halten,
und ein österreichisches Depot kann kanadische Aktien enthalten. Ein Profil muss
daher entweder die benötigte Gesamtdeckung bieten oder seine Fallbacks intern
deklarieren; geographisches Auto-Routing wäre erneut nur eine Heuristik.

## Was ein belastbares nummeriertes Backup braucht

Ein Dateiname wie `stockinfo-000001.sqlite3`, `stockinfo-000002.sqlite3` usw. ist
ausreichend einfach. Zu jeder Generation sollte jedoch ein kleines Manifest
gehören mit:

- Profil-ID und Profil-Kompatibilitätsversion,
- installierten Plugin-Paketen und Versionen,
- StockInfo- und Datenbankschema-Version,
- Erstellungszeitpunkt.

Sonst weiß man beim Restore zwar, welche Datenbank alt ist, aber nicht, mit
welchem Plugin-Stand sie fachlich zusammengehört. Secrets gehören nicht in das
Manifest.

Die Rotation darf erst stattfinden, nachdem B installiert, importiert,
konfiguriert und durch seine Start-/Contract-Prüfung gekommen ist. Ein Tippfehler
oder ein nicht installierbares Wheel darf nicht dazu führen, dass A bereits aus
dem aktiven Betrieb genommen wurde. Sinnvolle Startreihenfolge:

1. Plugin-Umgebung atomar herstellen bzw. die letzte funktionierende verwenden.
2. Profil und alle Rollen laden und validieren.
3. Profil-ID mit der in der aktiven Datenbank gespeicherten ID vergleichen.
4. Bei bewusst geändertem Profil eine konsistente SQLite-Sicherung erzeugen.
5. Erst danach die frische aktive Datenbank initialisieren und den Dienst
   freigeben.

Für die Sicherung sollte die SQLite-Backup-API verwendet werden; eine bloße Kopie
der `.db`-Datei kann bei WAL-Betrieb unvollständig sein. Zusätzlich ist eine
Start-Sperre nötig, damit zwei gleichzeitig startende Prozesse nicht dieselbe
Backup-Nummer vergeben. Das alte Backup wird nie überschrieben oder automatisch
gelöscht.

Nicht jede Patch-Version eines Plugins sollte automatisch eine neue Datenbank
erzwingen. Maßgeblich ist eine explizite **Profil-/Datenkompatibilitäts-ID**, nicht
der Hash aller Konfigurationsbytes. Sonst erzeugen etwa ein geänderter API-Key
oder eine Fehlerkorrektur unnötig eine leere Datenbank.

## Befund im StockPortfolio-Code: Der Datenbesitz ist bereits passend getrennt

StockPortfolio speichert Portfolio, Stückzahlen, Ziele und Benutzernamen lokal
im Browser. StockInfo liefert nur Kurse und Stammdaten
(`StockPortfolio/README.md:160-175`). Eine frische StockInfo-Datenbank löscht
daher **nicht** das Portfolio. StockPortfolio fragt jede Position direkt per ISIN
oder Symbol ab (`src/stores/quotes.ts:359-388`); erfolgreiche Abfragen bauen die
frische StockInfo-Datenbank wieder auf.

Die sichtbare Basiszeile setzt sich wie folgt zusammen:

| Anzeige in StockPortfolio | Eigentümer |
|---|---|
| Symbol, Anzeigename, Stückzahl, Ziel-% | StockPortfolio/Benutzer |
| Preis und Notierungswährung | StockInfo-REST |
| Verlauf | StockInfo-REST-Daily-Endpunkt |
| Marktwert, Ist-%, Delta, Status | StockPortfolio, aus Bestand und Preis berechnet |

Damit muss ein Plugin weder Portfolio- noch Rebalancinglogik kennen. Es muss nur
in den stabilen StockInfo-Vertrag normalisiert werden.

## Der öffentliche REST-Vertrag muss vor dem Plugin-Vertrag stehen

Plugin B darf andere Anbieterfelder, URLs und Antwortformate haben. Am
StockInfo-REST-Rand müssen aber mindestens diese **Semantiken** unverändert
bleiben:

- stabile Instrument-/Listing-Identität: ISIN soweit vorhanden sowie kanonischer
  Ticker und MIC,
- stabiler Anzeigename und normalisierter Instrumenttyp,
- aktueller Preis mit **verpflichtender** Notierungswährung,
- Kurszeitpunkt, Abrufzeitpunkt sowie Cache-/Stale-Zustand,
- Daily-Punkte mit Datum, Schlusskurs und Währung,
- festgelegte Bedeutung des Schlusskurses, insbesondere adjusted gegen
  unadjusted.

Plugin-native Objekte oder Feldnamen dürfen diese Grenze nie überschreiten. Erst
der StockInfo-Kern validiert und normalisiert sie, dann serialisiert Pydantic das
öffentliche DTO. Ein unvollständiger Pflichtkern ist ein kontrollierter
`Unavailable`-/Fehlerfall und kein Response mit geratenen Ersatzwerten.

### T-21 würde StockPortfolio derzeit brechen

Die offene Entscheidung 1 der Spec will `symbol` nullable machen. Im aktuellen
StockPortfolio-Vertrag ist `symbol` hingegen überall verpflichtend
(`src/api/types.ts:16-23`, `src/api/types.ts:39-45`), dient als Cache-Fallback
(`src/api/mappers.ts:54-57`) und ist für Positionen verpflichtend
(`src/types/portfolio.ts:26-37`). Auch die Symbol-Endpunkte werden aktiv genutzt.

T-21 darf deshalb nicht nur als interne StockInfo-Migration umgesetzt werden.
Es braucht eine der beiden expliziten Varianten:

1. Die bestehende REST-Version behält ein garantiertes, semantisch stabiles
   `symbol`; `ticker`, `mic` und Aliase kommen additiv hinzu.
2. Eine neue REST-Version führt `listing_id`, `ticker`, `mic` und optionale
   Anbieter-Aliase ein; StockPortfolio wird vor dem Abschalten des alten Vertrags
   migriert.

Ein nullable Yahoo-Alias unter demselben Feldnamen wäre keine
Providerentkopplung, sondern ein unbemerkter Consumer-Break. Gerade ein Plugin,
das Yahoo gar nicht kennt, zeigt, warum der öffentliche Bezeichner nicht mit
einem Yahoo-Alias gleichgesetzt werden darf.

## Fester Kern, dynamische Details

Mikes UI-Vorgabe löst den bisherigen Feldmengen-Widerspruch sinnvoll in zwei
Ebenen auf:

1. **Core:** geschlossen, versioniert und für alle Plugins gleich. Darauf dürfen
   StockPortfolio und andere Konsumenten rechnen.
2. **Details:** erweiterbar, typisiert und ausschließlich für aufklappbare
   Zusatzinformationen. Unbekannte Detailfelder darf ein Konsument ignorieren.

Für Rückwärtskompatibilität sollten die heute öffentlichen Felder `ter`,
`volatility`, `accumulating`, `provider`, `replication`, `fund_size`,
`fund_domicile` und `fund_currency` zunächst bestehen bleiben. Zusätzliche
regionale Felder können additiv etwa als `details` geliefert werden. Ein Eintrag
braucht mindestens:

- stabilen, bei fremden Feldern namespaceten Schlüssel,
- Typ (`number`, `text`, `boolean`, gegebenenfalls Datum),
- wirksamen, bereits normalisierten Wert,
- kanonische Einheit und gegebenenfalls Währung,
- Bezeichnung bzw. Übersetzungsschlüssel,
- `overridable`,
- Herkunft `provider` oder `manual` sowie Quellenname und Stand.

Die Spec-Aussage „keine offene Feldmenge, zunächst“ ist damit nur noch für den
Core richtig. Für echte dynamische Details muss sie geändert werden. Derzeit ist
die Dynamik noch **nirgends durchgängig implementiert**:

- StockInfo verwirft unbekannte Plugin-Felder laut Spec.
- Backend und Override-Modell führen genau acht feste Felder
  (`app/models.py:100-143`).
- Das StockInfo-Dashboard iteriert genau dieselben acht Felder
  (`dashboard/src/types.ts:15-35`, `InstrumentDrilldown.vue:98-121`).
- StockPortfolio speichert nur `volatility`, `ter` und `accumulating` im
  Quote-Cache (`src/types/portfolio.ts:159-173`) und rendert TER/Volatilität fest
  (`src/components/PositionDrilldown.vue:281-297`).

Wenn „dynamisch“ nur bedeutet, dass eine Teilmenge dieser acht bekannten Felder
sichtbar ist, reicht der aktuelle Ansatz. Wenn Plugins B und C eigene regionale
Kennzahlen ergänzen dürfen, ist eine generische Detail-Pipeline samt generischem
Override-Endpunkt erforderlich.

## Manuelle Ergänzungen: Die gewünschte Semantik existiert bereits

Für die acht bekannten Felder tut StockInfo heute genau das Beschriebene:

- Ein Quellenwert gewinnt.
- Ist der Quellenwert `None`, füllt der manuelle Wert die Lücke
  (`app/services/quote_cache.py:34-81`).
- `/instruments` liefert die wirksamen Werte plus Hinweise auf manuelle bzw.
  verdeckte Eingaben (`app/models.py:146-193`).
- Auch `/quote` legt die Overrides vor der REST-Antwort in Quellenlücken
  (`app/services/quote_cache.py:339-385`).

StockPortfolio bekommt damit bereits den wirksamen Wert und muss die
Override-Regel nicht selbst kennen. Diese Regel sollte für dynamische Details in
einer einzigen generischen Merge-Funktion fortgeführt werden. `null` heißt
„Quelle hat keinen Wert“; ein falscher Standardwert des Plugins darf nicht als
Lücke behandelt werden.

## Drei konkrete Consumer-Risiken beim Profilwechsel

### 1. StockPortfolio rät fehlende Währung als EUR

Die Mapper ersetzen eine fehlende Währung derzeit mit `EUR`
(`src/api/mappers.ts:12-26`, `src/api/mappers.ts:33-50`). Für Kanada- oder
Russland-Profile ist das gefährlich: Ein fehlendes `CAD`, `USD` oder `RUB` wird
nicht als unvollständiger Kurs sichtbar, sondern als Euro-Kurs berechnet. Für den
stabilen Core muss `currency` bei einem verwertbaren Preis Pflicht sein;
StockPortfolio darf an dieser Stelle nicht raten.

### 2. StockPortfolio hält eigene Caches über den DB-Wechsel hinweg

Eine frische StockInfo-Datenbank leert nicht den Quote-/History-Cache im Browser.
Ist dessen alter Stand nach StockPortfolios TTL noch „frisch“, kann er nach dem
Wechsel zunächst weiter angezeigt werden. Der REST-Vertrag sollte daher eine
stabile `dataset_id` oder `generation_id` bereitstellen, etwa im Health-/Info-
Endpunkt. Ändert sie sich, verwirft StockPortfolio seine abgeleiteten Kurs- und
Historien-Caches sofort. Die Portfolio- und Benutzerdaten bleiben erhalten.

### 3. Lokal gespeichertes Symbol kann zum neuen Listing veraltet sein

StockPortfolio zeigt `position.symbol`, nicht das Symbol der letzten
Quote-Antwort (`PositionsTable.vue:210-276`). Bei vorhandenen Positionen und
einem Profil, das dieselbe ISIN auf ein anderes Listing abbildet, bleibt damit
die alte Beschriftung bzw. der alte Link sichtbar, obwohl bereits der neue Kurs
verwendet wird. Im primären Kanada-Neustart-Szenario existieren diese Positionen
noch nicht; für einen späteren Profilwechsel braucht es aber entweder einen
Abgleich über die kanonische Listing-ID oder eine klar als benutzerdefiniert
behandelte Anzeige.

## Regionale StockInfo-Plugins machen StockPortfolio noch nicht regional

StockInfo kann mit A/B/C weltweit passende Daten liefern. StockPortfolio selbst
ist derzeit jedoch fachlich auf EUR festgelegt
(`src/types/portfolio.ts:114-135`): Fremdwährungspositionen werden ausdrücklich
aus Summen ausgeschlossen (`src/domain/rebalancing.ts:72-111`). Außerdem
formatiert der Drilldown den Einzelkurs noch fest als EUR
(`src/components/PositionDrilldown.vue:242-245`).

Das widerspricht nicht dem Plugin-Modell, aber es begrenzt die Aussage:

- Ein kanadisches StockInfo-Profil B ist realistisch und sinnvoll.
- Ein kanadischer Nutzer kann StockInfo damit verwenden.
- Soll derselbe Nutzer StockPortfolio mit CAD als Basiswährung verwenden, ist
  dafür ein eigenes StockPortfolio-Vorhaben nötig. Das löst kein StockInfo-
  Plugin.

## Installation: Profilwahl muss der einfache Weg sein

Die Paketliste in `sources.yaml` ist technisch tragfähig, verlangt im Beispiel
aber weiterhin Paket, Resolverkette, Quotenkette und Providerkonfiguration. Für
das Regionalmodell sollte der Normalfall eher so einfach sein:

```yaml
profile:
  package: stockinfo-profile-canada==1.2.3
  id: canada
```

Das Profil bringt getestete Standardketten mit; nur Secrets und bewusste
Abweichungen werden zusätzlich konfiguriert. Der fortgeschrittene Nutzer darf
die Rollen weiterhin einzeln überschreiben. Für den Plugin-Entwickler bleibt
`data/plugins/` der noch kürzere Testweg: Datei ablegen, Profil/Quelle nennen,
neu starten.

Akzeptanzkriterien für die Installation sollten aus Nutzersicht formuliert sein:

1. Eine Datei bzw. eine fest versionierte Paketzeile eintragen.
2. Container neu starten.
3. `/sources` zeigt Profil, Version, aktive Rollen und einen verständlichen
   Selbsttest.
4. Bei Fehlern läuft die letzte gültige Plugin-Umgebung und Datenbankgeneration
   weiter; es gibt keine halb installierte Umgebung und keine leere DB.

Ein Marktplatz oder eine Laufzeit-Umschaltung ist dafür nicht nötig. Ein
einzeiliges Profil plus eindeutige Diagnose ist wichtiger als zusätzliche
Installationsmechanismen.

## Erforderliche Contract-Tests über die Projektgrenze

Die Plugin-Contract-Tests allein garantieren nicht, dass StockPortfolio stabil
bleibt. Zusätzlich nötig sind:

1. Ein versionierter OpenAPI-/REST-Contract des festen Core.
2. Dieselben Consumer-Fixtures für Profil A, B und C: andere Werte und Quellen,
   aber identische Pflichtfelder, Typen und Einheiten.
3. Ein End-to-End-Test „Profil A + DB → nummeriertes Backup → Profil B + frische
   DB → vorhandene StockPortfolio-Position per ISIN neu laden“.
4. Ein Test, dass manuelle Lückenfüller über `/quote` und `/instruments` als
   wirksame Werte identisch ankommen.
5. Ein Test, dass zusätzliche Detailfelder einen älteren Consumer nicht brechen.
6. Laufzeitvalidierung am Consumer-Rand oder mindestens strikte serverseitige
   Response-Validierung. StockPortfolio castet `response.json()` aktuell nur auf
   TypeScript `T` (`src/api/client.ts:114-136`); das prüft zur Laufzeit nichts.

## Empfehlung an Claude für die Spec

1. Das Betriebsmodell „Profilwechsel = nummeriertes Backup + frische DB“ als
   eigene Invariante aufnehmen.
2. T-19 aus dem kritischen Pluginwechsel-Pfad entfernen und auf den seltenen
   manuellen Einzelinstrument-Korrekturweg begrenzen.
3. A/B/C als explizit wählbare Quellenprofile über den Rollenketten definieren.
4. Vor T-21 einen öffentlichen, pluginunabhängigen REST-Core festschreiben und
   die StockPortfolio-Abhängigkeit ausdrücklich nennen.
5. Die geschlossene Feldmenge auf den Core begrenzen; für aufklappbare Details
   eine additive, typisierte Erweiterungsfläche vorsehen, falls „dynamisch“
   wirklich plugin-eigene Felder meint.
6. Profil-/Datenbankgeneration im REST-Info-Vertrag sichtbar machen, damit
   Consumer ihre abgeleiteten Caches invalidieren können.
7. Die Installation auf eine Profilzeile plus Neustart und Diagnose optimieren;
   die detaillierte Rollenverdrahtung bleibt der Expertenmodus.

**Fazit:** Das von Mike beschriebene Modell ist realistisch und konsequent. Es
verschiebt die schwierige Grenze an die richtige Stelle: Nicht Daten zwischen A,
B und C migrieren, sondern jede StockInfo-Datenbank eindeutig an ein
Quellenprofil binden. Die harte, dauerhaft zu schützende Kompatibilitätsgrenze
ist stattdessen das REST-Core-DTO zu StockPortfolio. Dynamische Details und
manuelle Lückenfüller können darüber additiv liegen, dürfen aber Identität,
Preis, Währung und Historiensemantik nie verändern.

---

# Verbindliche Präzisierung: Mindestvertrag plus offene Detailmenge

**Weiterer Input von Mike am 2026-08-20:** Künftige REST-Antworten können
zusätzliche Detaildaten enthalten, deren Bedeutung heute noch nicht bekannt ist.
Die heute bekannten Basisdaten bilden den Mindestvertrag, den jedes Profil
erfüllen muss.

Damit ist die zuvor noch bedingt formulierte Feldentscheidung getroffen:

- Der **Mindestvertrag/Core** ist geschlossen, versioniert und für jedes Plugin
  verpflichtend.
- Die **Detailmenge** ist ausdrücklich offen, additiv und darf mit neuen Plugins
  und neuen StockInfo-Versionen wachsen.

Die Spec-Passage „Keine offene Feldmenge, zunächst“ ist daher fachlich überholt.
Unbekannte, korrekt deklarierte Detailfelder dürfen nicht protokolliert und
verworfen werden. Sie müssen normalisiert, gespeichert und per REST ausgeliefert
werden.

## Forward-Compatibility-Regeln

1. Neue Details sind niemals neue unstrukturierte Top-Level-Felder. Sie liegen
   in einem stabil typisierten Container, etwa `details: [...]`.
2. Jeder Detaileintrag hat eine bekannte Hülle: Schlüssel, Werttyp, Wert,
   Einheit/Währung, Bezeichnung, Überschreibbarkeit, Herkunft und Stand.
3. Plugin-eigene Schlüssel sind namespaced, damit zwei Plugins nicht zufällig
   verschiedene Bedeutungen unter demselben Namen ablegen.
4. Alte Consumer ignorieren unbekannte Details. Neue oder generische Consumer
   können sie im aufgeklappten Bereich rendern, ohne dafür das Basislayout zu
   ändern.
5. Details dürfen keine Rebalancing-, Preis- oder Identitätsberechnung
   beeinflussen. Wird ein heutiges Detail später fachlich unverzichtbar, wird es
   bewusst in eine neue Core-Vertragsversion aufgenommen.
6. Das Hinzufügen eines Details ist keine Breaking Change. Änderungen an Name,
   Typ, Einheit oder Semantik eines bestehenden Detail-Schlüssels sind dagegen
   eine Migration bzw. brauchen einen neuen Schlüssel.

Eine mögliche feste Hülle wäre beispielsweise:

```json
{
  "key": "stockinfo-profile-canada.management_fee",
  "kind": "number",
  "value": 0.18,
  "unit": "percent",
  "currency": null,
  "label": { "en": "Management fee", "de": "Verwaltungsgebühr" },
  "overridable": true,
  "origin": "provider",
  "source": "canada-provider",
  "as_of": "2026-08-20T08:00:00Z"
}
```

Die konkrete JSON-Form ist noch zu entscheiden; entscheidend ist die stabile
Hülle um einen offenen Schlüsselraum. `FieldSpec` und `Reading` im vorhandenen
Plugin-Vertrag liefern dafür bereits einen großen Teil der benötigten
Beschreibung. Die Persistenz und die REST-/UI-Pipeline müssen diese Information
aber erhalten, statt sie am heutigen Acht-Felder-Katalog abzuschneiden.

## Übergang ohne Bruch für StockPortfolio

Die heute von StockPortfolio gelesenen Felder bleiben in der bestehenden
REST-Version erhalten. Der neue `details`-Container kommt additiv hinzu. Soweit
bekannte Werte vorübergehend sowohl als bestehendes Feld als auch als generisches
Detail projiziert werden, müssen beide Darstellungen aus **demselben wirksamen
Wert** erzeugt werden; zwei unabhängig gepflegte Wahrheiten wären nicht
vertretbar.

Langfristig kann eine neue REST-Hauptversion den Core wirklich minimal halten
und alle Metadaten ausschließlich über `details` liefern. Das ist aber eine
koordinierte Consumer-Migration und darf nicht beiläufig mit T-21 passieren.

**Aktualisierte Empfehlung an Claude:** Die offene Entscheidung 5 nicht nur als
Frage nach Provenienz betrachten. Die Architektur braucht jetzt ausdrücklich
einen stabilen Mindestvertrag und eine persistierte, offene Detailmenge. Der
Core-Katalog validiert die Pflichtdaten; der Detailvertrag validiert die Hülle,
nicht eine für alle Zukunft abschließende Liste von Feldnamen.
