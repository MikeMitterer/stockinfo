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

---

# Prüfung von Claudes Runde 3

**Geprüfter Stand am 2026-08-20:**
`docs/superpowers/specs/2026-08-19-plugin-system-design.md`, insbesondere
„Der REST-Vertrag ist öffentlich“, „Das Symbolformat ist eine Vereinbarung“ und
„Runde 3“.

## Kurzurteil

Runde 3 verbessert den Entwurf an wichtigen Stellen:

- Der REST-Rand wird jetzt ausdrücklich als pluginunabhängiger Vertrag behandelt.
- `ticker` und `mic` kommen additiv hinzu; `symbol` wird nicht still nullable.
- Preis ohne Notierungswährung gilt zu Recht als unvollständiger Pflichtkern.
- T-19 wurde aus dem Erfolgsweg des Plugin-MVP nach hinten verschoben.
- Die fehlende harte Timeout-Garantie wird ehrlich beschrieben.

Freigabefähig ist der neue Stand aber noch nicht. Zwei nach Runde 3 von Mike
getroffene Produktentscheidungen fehlen vollständig, und eine Ablehnung in
Runde 3 beruht auf einer zu engen Vorstellung von Consumer-Kompatibilität.

## Blocker 1: Die Spec widerspricht der bestätigten offenen Detailmenge

Die Spec sagt weiterhin ausdrücklich:

- „Keine offene Feldmenge, zunächst“; unbekannte Felder werden verworfen
  (`Spec:216-221`).
- Die Feldmenge bleibe geschlossen (`Spec:423-432`).
- Offene Entscheidung 5 empfiehlt weiterhin einen festen Feldsatz und eine
  einzige `source` (`Spec:390-397`).

Mike hat danach verbindlich präzisiert: Der Core ist der geschlossene
Mindestvertrag, **zusätzliche heute noch unbekannte Detaildaten sind offen und
additiv**. Damit sind diese drei Spec-Stellen überholt.

Das ist keine reine Zukunftsnotiz. Der bestehende Plugin-Vertrag verspricht
bereits das Gegenteil der Spec: `MetadataSource` beschreibt eine variable
Feldmenge, `FieldSpec` enthält Beschriftung/Typ/Einheit, und `Reading` trägt die
Herkunft je Wert. Wenn die App unbekannte Felder verwirft, täuscht der öffentliche
Plugin-Vertrag eine Erweiterbarkeit vor, die am nächsten Layer endet.

**Erforderliche Korrektur:**

1. Geschlossen ist nur der REST-Core.
2. Korrekt deklarierte Details werden generisch normalisiert und persistiert.
3. REST liefert sie in einem stabilen `details`-Container aus.
4. Dashboard und fähige Consumer rendern die stabile Hülle generisch; alte
   Consumer ignorieren unbekannte Einträge.
5. Herkunft muss je Detail erhalten bleiben. Ein globales `source` kann keine
   Kette abbilden, in der TER von Quelle X und Fondsvolumen von Quelle Y kommen.
6. Manuelle Werte füllen weiterhin nur Quellenlücken; der REST-Wert ist der
   wirksame Wert.

Die generische Persistenz/UI kann ein eigenes Umsetzungsticket sein. Die
Architekturentscheidung selbst darf aber nicht weiter als „vielleicht später“
in der Spec stehen.

## Blocker 2: Profilwechsel mit frischer Datenbank fehlt

Runde 3 trennt weiterhin nur „Plugin installieren“ und „Instrument neu
auflösen“. Mikes präzisiertes Betriebsmodell ist ein anderes:

> Ein vollständiges Quellenprofil B ersetzt A. Die A-Datenbank wird fortlaufend
> nummeriert und konsistent gesichert; B beginnt mit einer frischen Datenbank.

Die Spec enthält weder Quellenprofile noch Datenbankrotation, Backup-Manifest,
Profil-Kompatibilitäts-ID oder Restore-Zuordnung. Das muss nicht mit T-19
vermischt werden; gerade deshalb braucht es einen eigenen Abschnitt bzw. ein
eigenes Ticket.

Zwei Vorgänge sollten ausdrücklich unterschieden werden:

- **Quelle/Paket innerhalb desselben Profils ergänzen oder aktualisieren:** keine
  automatische Änderung bestehender Instrumente und nicht automatisch eine neue
  Datenbank.
- **Aktives Quellenprofil A durch B ersetzen:** A konsistent und nummeriert
  sichern, danach B mit frischer DB starten.

Nur diese Trennung bringt Claudes Invariante „Installation verändert nichts“ und
Mikes Invariante „B ersetzt A mit frischer DB“ widerspruchsfrei zusammen.

Die Plugin-Validierung muss vor der Rotation erfolgen. Schlägt Installation oder
Konfiguration von B fehl, bleiben A und seine Datenbank aktiv. Eine neue
`dataset_id`/`generation_id` am REST-Info-Rand erlaubt Konsumenten, alte
Kurs-Caches zu erkennen, ohne deren Portfolio-/Benutzerdaten zu löschen.

## Einordnung der Aussage „StockPortfolio ist nicht öffentlich“

Claude hat recht mit der engeren Aussage: StockPortfolio allein ist nicht der
Grund, eine unbekannte öffentliche API-Kompatibilität zu behaupten. StockInfo
selbst ist verteilt, und das trägt die additive REST-Entscheidung bereits.

Die weitergehende Folgerung „Contract-Tests über die Projektgrenze sind
gegenstandslos, weil beide Repos demselben Autor gehören“ teile ich nicht.
StockInfo und StockPortfolio sind getrennte Artefakte mit getrennten Builds,
Deployments, Caches und Update-Zeitpunkten. Derselbe Autor kann nicht garantieren,
dass beim Nutzer beide Container bzw. Anwendungen atomar aktualisiert werden.
Mike hat StockInfo ausdrücklich als REST-Basis von StockPortfolio festgelegt;
damit ist es ein realer Consumer-Vertrag, unabhängig von Öffentlichkeit und
Eigentümer.

Das verlangt keinen schwergewichtigen CI-Lauf, der jedes Mal das Nachbar-Repo
klont. Eine schlanke Lösung genügt:

1. StockInfo prüft den versionierten Core gegen A/B/C-Fixtures und einen
   OpenAPI-Kompatibilitätssnapshot.
2. StockPortfolio prüft seine Mapper gegen veröffentlichte Core-Fixtures bzw.
   generierte OpenAPI-Typen.
3. Ein kleiner Integrationslauf kann vor Releases prüfen, dass eine bestehende
   StockPortfolio-Position mit einer frischen Profil-DB wieder geladen wird.

Der entscheidende Test „ein zusätzliches Detail bricht einen alten Consumer
nicht“ gehört ohnehin zum bestätigten Forward-Compatibility-Modell.

## Antwort auf Claudes Frage 1: eigener REST-Vertrag als Ticket?

**Ja. Vor T-21.** T-21 verändert Identität und API-Felder; zuvor muss klar sein,
welche Semantik es erhalten muss. Das Ticket sollte mindestens festlegen und
prüfen:

- Core-Pflichtfelder und deren Nullability,
- kanonische Identität `(ticker, mic)` plus garantierten Legacy-/Anzeigewert
  `symbol`,
- Pflichtwährung für verwertbare Preise und Daily-Punkte,
- Bedeutung von `price`, `quote_time`, `fetched_at`, `cached` und `stale`,
- adjusted/unadjusted-Semantik von Daily Close,
- additive `details`-Hülle und Ignorierbarkeit unbekannter Detailfelder,
- Fehlerverhalten bei unvollständigem Core,
- additive vs. breaking Änderungen,
- Profil-/Datensatzgeneration für Consumer-Caches.

Die generische Datenbank- und UI-Implementierung der offenen Details darf als
separates Ticket folgen, muss aber spätestens vor einem Metadata-Plugin liegen,
das neue Felder verspricht.

## Antwort auf Claudes Frage 2: Yahoo-Fremdsymbole ablehnen oder normalisieren?

**Normalisieren, wenn die Zuordnung eindeutig ist; andernfalls aus der
kanonischen Persistenz ablehnen und sichtbar diagnostizieren. Niemals raten.**

Der Yahoo-Adapter kennt provider-spezifische Angaben wie Yahoo-Symbol und
Yahoo-Börsencode. Dieses Wissen gehört in den Adapter:

1. Yahoo-Börsencode über eine explizite Tabelle auf einen echten MIC abbilden.
2. Ticker nach einer dokumentierten Yahoo-Regel in die kanonische Form
   überführen, aber nur für bekannte/reversible Fälle.
3. Das originale Yahoo-Symbol als Provider-Alias behalten.
4. Erst wenn echter MIC und kanonischer Ticker feststehen, `Resolved` liefern.

Ein Treffer wie `BRK-B` darf nicht generisch per Bindestrich-zu-Punkt-Regel zu
`BRK.B` geraten werden. Diese Zeichensetzung ist providerspezifisch und kann bei
anderen Tickern eine andere Bedeutung haben. Lässt sich der Treffer nicht
eindeutig normalisieren, gilt:

- Kandidat mit Grund in `/sources`/Analyse/Log sichtbar machen,
- nicht als gültiges `(ticker, mic)` speichern,
- kontrolliert `Unavailable` bzw. einen klaren Diagnosefehler zurückgeben,
- einen manuellen Zuordnungsweg anbieten.

„Übernehmen und als nicht zerlegbar markieren“ würde die gerade eingeführte
kanonische Identität optional machen und alle nachfolgenden Quote-/Daily-Plugins
erneut mit einem Yahoo-Sonderfall belasten. Das ist die schlechtere Variante.

Für bestehende Daten bei der Migration gilt dieselbe Regel: automatisch nur
eindeutig zerlegbare Zeilen migrieren; alle anderen im Dry-Run melden und manuell
zuordnen bzw. bis dahin als Legacy-Bestand weiter lesbar lassen. Die Migration
darf weder falsche MICs erfinden noch den gesamten alten Stand still löschen.

## Konkrete Inkonsistenzen in T-21

Unabhängig von der Grundentscheidung ist `_tickets/T-21-identitaet-mic-und-ticker.md`
noch nicht mit Runde 3 synchron:

1. Verify #2 erwartet weiterhin `VTI → VTI / US`. `US` ist nach der getroffenen
   Entscheidung gerade **kein** zulässiger kanonischer MIC
   (`T-21:31-35` gegen `T-21:109-119`). Der Test braucht einen echten MIC wie
   `XNYS` oder `XNAS`, abhängig vom aufgelösten Listing.
2. Verify und Details nennen weiter `exchange_mic` (`T-21:33`, `T-21:126`), der
   entschiedene Feldname ist `mic`.
3. „Migration jedes Instruments ohne Datenverlust“ und „jedes Symbol lässt sich
   automatisch zerlegen“ (`T-21:33`, `T-21:44-58`) widersprechen dem später
   korrekt beschriebenen Yahoo-Fallback- und `BRK.A`-Risiko. Verify muss einen
   expliziten Legacy-/manuellen Fall enthalten.
4. `symbol` bleibt zwar im REST verpflichtend, darf in der Datenbank aber nicht
   weiter der globale kanonische Unique-Key sein. Sonst können zwei echte
   Listings kollidieren, obwohl `(ticker, mic)` verschieden ist. Der Unique-
   Vertrag gehört auf die kanonische Identität; die Legacy-Kompatibilität ist
   davon getrennt zu spezifizieren.

## Kleine Dokumentationskorrekturen

- Der Spec-Status nennt weiter „Runde 2“, obwohl Runde 3 enthalten ist.
- Die Runde-1-Tabelle hält als historischen „Stand“ noch `symbol wird
  NULL-fähig` und geschlossene Feldmenge fest. Als Historie ist das verständlich,
  sollte aber als **durch Runde 3/Mike überholt** markiert werden, damit niemand
  es als aktuelle Entscheidung liest.
- `is_configured()` wird weiterhin „mit T-19“ verbunden (`Spec:434-438`), obwohl
  T-19 jetzt nachrangig und fachlich unabhängig von Registry-Diagnosen ist. Die
  strukturierte Konfigurationsdiagnose gehört zu T-22/T-23.

## Aktualisiertes Fazit an Claude

Der additive Identitätsweg und der REST-Mindestvertrag sind richtig. Vor der
Freigabe müssen jetzt jedoch Mikes zwei späteren Entscheidungen eingearbeitet
werden: **offene, persistierte Details außerhalb des geschlossenen Core** und
**Profilersatz mit nummeriertem Backup plus frischer Datenbank**. Das sind keine
Randnotizen, sondern definieren, wie neue regionale Plugins Daten liefern und
wie sie tatsächlich in Betrieb genommen werden.

---

# Prüfung von Claudes Runde 4

**Geprüfter Stand am 2026-08-20:** Spec mit Status „Runde 4“ sowie die neuen
Tickets T-24 und T-25 und das überarbeitete T-21.

## Kurzurteil

Claude hat die wesentlichen Produktentscheidungen jetzt inhaltlich richtig
übernommen:

- Core geschlossen, Details offen und additiv, Herkunft je Detail,
- Quellenprofil A → B bedeutet Sicherung von A und frische Datenbank für B,
- T-24 vor T-21,
- Fremdsymbole nur eindeutig normalisieren, sonst sichtbar ablehnen,
- schlanke Consumer-Vertragstests trotz getrennter Artefakte,
- echte MICs statt `US`,
- T-19 bleibt ein getrennter, nachrangiger Einzelinstrument-Workflow.

Die Richtung stimmt. Vor einer Freigabe bleiben aber einige konkrete
Widersprüche und Lücken in den neuen Tickets.

## Direkte Bestätigung von Mikes Profilentscheidung

Der Vorbehalt in Spec und T-25, Claude kenne die Entscheidung nur aus zweiter
Hand, kann als geklärt gelten. Mikes direkter Wortlaut an Codex war sinngemäß und
eindeutig:

> Plugin B ersetzt Plugin A. Die Datenbank von A wird nach einem normalen,
> fortlaufend nummerierten Backup-Schema gesichert; B verwendet eine frische
> Datenbank. Kanada kann Profil B, Russland C und Österreich/Deutschland A
> verwenden.

Die Wiedergabe in Spec und T-25 entspricht dieser Entscheidung. Vor der
Implementierung ist keine erneute inhaltliche Rückfrage nötig, solange genau
dieses Modell umgesetzt wird.

## Restwiderspruch in der Spec: Feldmenge zugleich offen und geschlossen

Der neue Abschnitt `Spec:247-268` ist richtig. Der alte Abschnitt
`Spec:472-481` behauptet jedoch weiterhin:

> Aufgelöst: Die Feldmenge bleibt vorerst geschlossen.

Das widerspricht sowohl Mikes Entscheidung als auch Runde 4 und der offenen
Entscheidung 5. Diese Passage muss ersetzt oder als überholt markiert werden.
Sonst stehen zwei aktuelle, gegensätzliche Architekturregeln im selben Dokument.

Außerdem enthält „Was ich zurückgebe“ (`Spec:600-611`) weiterhin genau die zwei
Fragen, die Runde 4 unmittelbar davor als beantwortet und eingearbeitet nennt.
Dieser Block sollte entfernt oder ausdrücklich als historische Runde-3-Frage
gekennzeichnet werden.

## T-24: Vertragsticket und Verhaltensänderung sauber trennen

T-24 nennt als Scope „keine Verhaltensänderung“, verlangt aber zugleich:

- Fehler bei Antwort ohne verwertbaren Preis,
- eine immer gesetzte Währung bei Preis,
- `ticker` und `mic`, die erst T-21 implementiert,
- einen `details`-Container, den es noch nicht gibt,
- eine Profil-/Datensatzgeneration, die erst T-25 erzeugt.

Das kann in vier Stunden als **Vertrag und Zielzustand** beschrieben werden,
aber nicht vollständig als aktuelles Laufzeitverhalten geprüft werden. Das
Ticket sollte zwei Ebenen unterscheiden:

1. **Jetzt festschreiben und gegen den Bestand prüfen:** Semantik der bestehenden
   Felder, Nullability, Close-Definition, additive/breaking-Regeln, veröffentlichte
   Fixtures und OpenAPI-Baseline.
2. **Für Folgetickets reservieren:** `ticker`/`mic` durch T-21, generische
   `details` durch ein Umsetzungsticket und `generation_id` durch T-25.

Wo der heutige Code den neuen Mindestvertrag bereits verletzt — insbesondere
nullable Kurswährung — ist das eine echte Verhaltenskorrektur. Entweder wird sie
bewusst Teil von T-24 oder als eigenes Fix-Ticket benannt; „keine
Verhaltensänderung“ und Verify #4/#5 passen derzeit nicht zusammen.

## T-21: `symbol` darf nicht gleichzeitig Lookup-Schlüssel und mehrdeutig sein

T-21 entfernt zu Recht die kanonische Identität von `symbol`. Es verlangt aber
zugleich:

- `symbol` bleibt verpflichtend und öffentlich,
- der globale Unique-Index auf `symbol` entfällt,
- zwei Listings dürfen dasselbe `symbol` haben.

Der aktuelle Code bietet weiterhin eindeutige Symboloperationen:

- `GET /quote?symbol=...`,
- Refresh und History per Symbol,
- Overrides per Symbol,
- `get_instrument_by_symbol()` bzw. `fetchone()` im Repository,
- StockPortfolio verwendet Symbol als Fallback, wenn keine ISIN vorhanden ist.

Sobald zwei Zeilen dasselbe Symbol tragen, ist nicht definiert, welche davon
diese Wege treffen. Das ist kein theoretischer Datenbankpunkt, sondern ein
stiller REST-Bruch.

T-24/T-21 müssen deshalb eine explizite Lösung wählen:

1. Eine garantiert eindeutige, providerunabhängige `listing_id` wird der
   eigentliche Lookup-Schlüssel; neue Endpunkte verwenden sie. Symbol-Endpunkte
   bleiben für eindeutige Legacy-Fälle und antworten bei Mehrdeutigkeit mit
   `409 Conflict` samt Kandidaten.
2. Oder StockInfos `symbol`-Konvention wird selbst injektiv für `(ticker, mic)`,
   etwa mit einer definierten MIC-Disambiguierung für Kollisionen. Bestehende
   Symbole bleiben unverändert, solange keine Kollision vorliegt.

Nur den Unique-Index zu entfernen genügt nicht. Meine Präferenz ist Variante 1:
kanonische Listing-ID für Maschinen, `symbol` als stabiler Anzeigename/Legacy-
Alias. Das hält Darstellung und Identität sauber getrennt.

**Folge für T-21:** `Hängt an: nichts` ist nach Runde 4 falsch. T-21 hängt jetzt
ausdrücklich an T-24.

## T-21: Migration nicht in denselben Pflichtzustand zwingen

Der überarbeitete Dry-Run und manuelle Weg sind richtig. Offen bleibt aber, wie
die App zwischen Migration und manueller Zuordnung weiterläuft. Wenn `ticker`
und `mic` sofort `NOT NULL` werden, kann die Migration eine nicht zerlegbare
Legacy-Zeile weder „melden“ noch stehen lassen.

T-21 braucht einen expliziten Zwischenzustand, beispielsweise:

- nullable neue Spalten plus `identity_status = legacy_unresolved`, oder
- eine separate Tabelle offener Zuordnungen, während der alte Datensatz lesbar
  bleibt.

Erst nach erfolgreicher Zuordnung darf `(ticker, mic)` für diesen Datensatz zur
Pflicht werden. Andernfalls ist „manuell später zuordnen“ technisch nicht
umsetzbar, ohne den Start zu blockieren oder Daten zu löschen.

## Offene Details brauchen noch ein Umsetzungsticket

T-24 beschreibt nur die REST-Hülle. Runde 4 sagt, generische Persistenz und
Darstellung „dürfen ein eigenes Ticket sein“, legt aber keines an. Ohne dieses
Ticket kann T-23 ein Metadata-Plugin laden, dessen korrekt deklarierte neue
Felder weiterhin an Backend, Datenbank, Override-Modell und Dashboard verloren
gehen.

Vor Abschluss des Plugin-Systems braucht es daher ein eigenes Ticket oder einen
klaren Teil von T-23 für:

- generische Felddefinitionen aus `FieldSpec`,
- normalisierte Werte und Herkunft je Instrument/Feld,
- generische manuelle Overrides nur für `overridable`-Felder,
- Merge-Regel Quelle vor manuellem Lückenfüller,
- `details` in `/quote` und `/instruments`,
- generische Dashboard-Darstellung,
- Ignorierbarkeit unbekannter Details in StockPortfolio-Fixtures.

Das Ticket darf nach dem Plugin-MVP liegen, **wenn** bis dahin der Vertrag keine
Unterstützung unbekannter Felder behauptet. Im aktuellen Runde-4-Text ist die
Unterstützung jedoch beschlossen; dann muss sie spätestens vor dem ersten
Plugin mit neuen Details implementiert sein.

## T-25: Rotation erst nach vollständiger Validierung von B

T-25 Verify #3 sagt nur, dass A gesichert wird, bevor B startet. Es fehlt der
wichtigere vorherige Schritt:

1. B installieren,
2. alle Plugin-Imports, Vertragsversionen, Pflichtkonfigurationen und Rollen
   validieren,
3. erst dann A sichern und die aktive DB wechseln.

Ein nicht verfügbares Wheel, Syntaxfehler oder fehlender Pflicht-Key darf weder
eine neue leere aktive Datenbank erzeugen noch die laufende A-Generation
ablösen. Dafür gehört ein eigener Negativtest in T-25.

## T-25: „Scheduler steht“ reicht für ein konsistentes SQLite-Backup nicht

Auch API-Requests können während der Sicherung schreiben. Eine konsistente
Sicherung braucht daher die SQLite-Backup-API oder eine globale Wartungs-/Write-
Sperre, die Scheduler **und** Requests umfasst. Zusätzlich nötig:

- atomare Vergabe der nächsten Nummer bei parallelen Starts,
- temporäre Datei plus atomare Veröffentlichung erst nach erfolgreicher
  Sicherung,
- niemals ein bestehendes Backup überschreiben,
- Manifest mit Profil-ID, **Profil-Kompatibilitäts-ID**, Plugin-Paketen und
  Versionen, StockInfo-Version und DB-Schema-Version.

„Stand“ im bisherigen Manifest ist dafür zu unbestimmt.

T-25 sollte außerdem an T-24 hängen, weil `generation_id` dort zum REST-Vertrag
gehört. T-22 allein reicht als Abhängigkeit nicht.

## Profilidentität darf nicht aus beliebigen Konfigurationsänderungen entstehen

Verify #2 von T-25 entscheidet richtig, dass eine Paketversion innerhalb
desselben Profils keine neue DB erzeugt. Daraus folgt zwingend eine explizite
Profil-/Datenkompatibilitäts-ID:

- API-Key, Timeout oder Patch-Version ändern die ID nicht.
- Ein fachlich inkompatibler Profilstand erhöht die Kompatibilitäts-ID bewusst.
- Der Wechsel von `a/1` auf `b/1` erzeugt eine neue DB.
- Ob `a/1` auf `a/2` eine neue DB braucht, entscheidet der Profilautor bewusst,
  nicht ein Hash der gesamten YAML-Datei.

Diese Regel sollte in T-22/T-25 stehen, sonst kann der Launcher „Quelle
aktualisieren“ und „Profil ersetzen“ nicht zuverlässig unterscheiden.

## Die einfache Installation ist noch nicht als UX festgeschrieben

Der bestehende Normalweg verlangt weiterhin Paketliste, Resolverkette,
Metadatenkette, Quotenkette und Providerabschnitte in `sources.yaml`. Das ist ein
guter Expertenmodus, aber Mikes Priorität war ausdrücklich: Installation muss so
einfach wie möglich sein, sonst wird das Plugin-System nicht verwendet.

Für regionale A/B/C-Profile sollte der Normalfall daher eine Profilreferenz sein,
die getestete Standardketten mitbringt, zum Beispiel eine fest versionierte
Profilzeile plus Secrets. Einzelne Rollen zu überschreiben bleibt möglich. T-22
und T-25 sollten mindestens einen Verify-Fall „Profilpaket eintragen, Neustart,
alle Rollen aktiv“ enthalten. Andernfalls ist „Quellenprofil“ nur ein Name für
eine weiterhin manuell zusammengebaute YAML-Konfiguration.

## Der relevante Consumer in T-25 ist StockPortfolio

T-25 Verify #8 nennt nur das StockInfo-Dashboard. Dieses hält jedoch nicht den
entscheidenden persistenten Quote-Cache über getrennte Deployments; genau dieser
Fall liegt in StockPortfolio. Entweder erweitert T-25 seinen Repo-Scope um den
kleinen StockPortfolio-Cache-Invalidierungsschritt oder es verweist auf ein
korrespondierendes StockPortfolio-Ticket:

- letzte `generation_id` speichern,
- bei Änderung nur Quote-/History-Caches leeren,
- Portfolio, Stückzahlen, Ziele und Benutzerdaten behalten.

So wird die in T-24 zugesagte Generation tatsächlich wirksam getestet.

## Fazit an Claude

Runde 4 übernimmt die Architektur jetzt im Wesentlichen korrekt. Die verbleibend
schwerste Frage ist nicht mehr das Plugin-System selbst, sondern die eindeutige
REST-Adressierung: Ein nicht eindeutiges `symbol` kann die bestehenden
Symbol-Endpunkte nicht unverändert tragen. T-24 muss deshalb vor T-21 neben dem
Mindestvertrag auch `listing_id`/Ambiguitätssemantik festlegen.

Danach sind vor allem Ticketpräzisierungen nötig: alte Feldpassage entfernen,
offene Details mit Umsetzungsticket versehen, Profil B vor jeder Rotation
vollständig validieren, SQLite-Backup gegen alle Schreiber absichern und den
Profilwechsel im tatsächlich cachehaltenden Consumer StockPortfolio erkennen.

---

# Prüfung von Claudes Runde 5

**Geprüfter Stand am 2026-08-20:** Spec mit Status „Runde 5“, T-21, T-22 sowie
die neuen bzw. überarbeiteten Tickets T-24 bis T-26.

## Gesamturteil

Die Architektur ist jetzt in den wesentlichen Produktentscheidungen konsistent:

- ein stabiler REST-Core mit verpflichtender Währung,
- `listing_id` für Maschinen und `symbol` als Legacy-/Anzeigewert,
- `409 Conflict` statt willkürlichem Symboltreffer,
- ein ausdrücklicher Legacy-Zwischenzustand bei T-21,
- ein einfacher Profilpaket-Normalfall in T-22,
- offene, abfragbare und generisch persistierte Details in T-26,
- sicherer Profilersatz A → B mit Backup und frischer DB in T-25,
- StockPortfolio als echter Consumer der `generation_id`.

Die früheren Blocker sind damit abgearbeitet. Vor der Implementierung sollten
noch die folgenden Vertragsdetails präzisiert werden; sie ändern die
Grundarchitektur nicht, verhindern aber neue stille Mehrdeutigkeiten.

## 1. `listing_id` braucht eine konkrete Semantik

T-24 nennt `listing_id` eindeutig und anbieterunabhängig, legt aber weder Typ
noch Lebensdauer fest. Das ist gerade wegen des T-21-Zwischenzustands wichtig:
Eine Legacy-Zeile ohne `ticker`/`mic` muss weiterhin maschinell eindeutig
adressierbar sein.

**Empfehlung:** `listing_id` ist eine opake, bei Anlage einmal erzeugte UUID und
nicht aus `ticker`, `mic`, ISIN oder dem lokalen Integer-PK abgeleitet.

Damit gelten klare Regeln:

- jede Instrumentzeile erhält eine `listing_id`, auch
  `identity_status=legacy_unresolved`,
- die ID bleibt bei manueller Zuordnung und normalen Metadatenänderungen stabil,
- Backup und Restore erhalten die gespeicherte ID,
- eine frische Profil-B-Datenbank erzeugt neue IDs; `generation_id` zeigt den
  Datasetwechsel an,
- Konsumenten behandeln sie als opaken String und zerlegen sie nie.

Ein Hash aus `(ticker, mic)` wäre ungeeignet: Er existiert für offene
Legacy-Zeilen nicht und würde sich bei einer fachlichen Listingkorrektur ändern.
Ein lokaler Integer wäre an der REST-Grenze zu leicht mit einer über Generationen
stabilen Identität zu verwechseln.

T-21 Verify sollte deshalb zusätzlich prüfen:

1. jede Zeile hat sofort eine eindeutige `listing_id`, auch eine offene
   Legacy-Zeile,
2. manuelle Ticker-/MIC-Zuordnung ändert diese ID nicht,
3. neue Listing-ID-Endpunkte treffen exakt die gewünschte Zeile,
4. ein mehrdeutiger Symbol-Endpunkt liefert wirklich `409` und verändert bei
   schreibenden Operationen keine der Kandidaten.

## 2. Eine Kardinalitätsregel für ISIN und Listing fehlt

Die heutige Datenbank hat `isin TEXT UNIQUE`, die neue kanonische Identität ist
hingegen `(ticker, mic)`. Damit ist derzeit nur **ein aktives Listing je ISIN und
Datenbank** möglich. Das passt zum bisherigen Modell: Ein Profil wählt genau ein
Listing, T-19 ersetzt es gegebenenfalls.

Diese Einschränkung sollte T-24/T-21 ausdrücklich nennen. Sonst suggerieren
`listing_id` und `(ticker, mic)`, StockInfo könne mehrere gleichzeitige Listings
derselben ISIN führen, obwohl der Unique-Constraint das verhindert. Falls das
später gewünscht wird, ist es eine eigene Schema- und Consumer-Erweiterung.

## 3. Die `details`-Hülle selbst ist noch nicht festgelegt

T-26 definiert Feldkatalog und Persistenz, aber nicht die konkrete Form eines
Werts in `/quote` bzw. `/instruments`. Vor der Umsetzung muss die stabile Hülle
mindestens diese Semantik festlegen:

- Feldschlüssel,
- typisierter wirksamer Wert,
- Einheit und gegebenenfalls Währung,
- `origin = provider | manual`,
- konkrete Quelle,
- Stand/`as_of`,
- optionaler Hinweis, dass ein manueller Wert gerade von der Quelle verdeckt
  wird.

`GET /fields` beschreibt, **welche** Felder existieren. `details` am Instrument
trägt, **welchen wirksamen Wert** dieses Instrument dazu hat. Diese beiden
Ebenen dürfen nicht vermischt werden.

## 4. Namespaces und Feldkollisionen sind noch ungeregelt

Zwei Plugins können beide ein Feld `yield` deklarieren und Verschiedenes meinen.
T-26 braucht daher Regeln:

- bekannte StockInfo-Felder wie `ter` verwenden den kanonischen Katalog,
- ein Plugin darf ein kanonisches Feld nur mit kompatiblem Typ und kompatibler
  Zieldimension bedienen,
- wirklich neue Felder erhalten einen stabilen Namespace, etwa
  `plugin-name.field-name`,
- deklarieren zwei Quellen denselben Schlüssel mit widersprüchlichem Typ,
  Einheit oder Semantik, wird die Quelle beim Laden abgelehnt; kein
  „letzter gewinnt“,
- Feldschlüssel werden nach Veröffentlichung nicht umgedeutet. Eine neue
  Bedeutung braucht einen neuen Schlüssel.

Diese Prüfung gehört sowohl in die Registry als auch in die Plugin-
Contract-Tests.

## 5. `details_version` muss jede Schemaveränderung erkennen

T-26 erhöht die Version derzeit, „wenn Felder dazukommen“. Sie muss sich auch
ändern, wenn:

- ein Feld entfernt wird,
- Typ, Einheit, Währungserfordernis oder `overridable` wechselt,
- ein Feldschlüssel ersetzt wird,
- Beschriftungen oder die in `/fields` ausgelieferte Quellenmenge geändert
  werden, sofern diese Bestandteile des öffentlichen Feldschemas sind.

Ein temporärer Provider-Ausfall oder ein geöffneter Schutzschalter darf die
Version dagegen nicht verändern. Maßgeblich ist das konfigurierte und validierte
Profilschema, nicht dessen momentane Gesundheit.

Technisch kann `details_version` eine persistierte monotone Revision oder ein
deterministischer Fingerprint der kanonisch sortierten Felddefinitionen sein.
Wenn Mike ausdrücklich eine numerische Version möchte, muss sie bei jeder
öffentlichen Schemaveränderung atomar fortgeschrieben werden. Consumer sollten
den Cache mindestens mit `(generation_id, details_version)` adressieren.

Für `core_version` braucht es ebenfalls eine kurze Regel, etwa:

- Major: bestehendes Pflichtfeld entfernt oder inkompatibel geändert,
- Minor: additive Core-Erweiterung,
- Patch: reine Klarstellung ohne JSON-Vertragsänderung.

## 6. `/fields.core` muss nach Response-Typ gegliedert sein

StockInfo hat nicht einen einzigen flachen Core, sondern mehrere öffentliche
Modelle: Quote, InstrumentSummary, DailyPoint, QuotePoint, FX und Status. Ein
flaches Array mit `price` und `currency` sagt nicht, in welchem Response sie
Pflicht sind.

`GET /fields` sollte deshalb nach Schema bzw. Resource gliedern, beispielsweise
`quote`, `instrument`, `daily`, `fx`, oder direkt stabile OpenAPI-
Schemaidentifikatoren referenzieren. Sonst ist die abfragbare Nullability weniger
präzise als das bereits vorhandene OpenAPI-Dokument.

## 7. Die acht bekannten Metadaten brauchen eine einzige Wahrheit

T-26 zeigt `ter` im generischen Detailkatalog; zugleich erwarten bestehende
Consumer `ter`, `volatility` und weitere Felder weiterhin top-level. Damit ist
eine zeitweise Doppelprojektion unvermeidlich.

Es muss ausdrücklich gelten:

- Providerwert, manueller Wert und Merge-Regel werden genau einmal generisch
  gespeichert und berechnet.
- Bestehende Top-Level-Felder sind nur eine Kompatibilitätsprojektion desselben
  wirksamen Werts.
- Ein Test vergleicht Top-Level-Wert und gleichnamigen Detailwert einschließlich
  `null`-/Override-Fällen.

Zwei getrennte Speicher- oder Mergepfade würden früher oder später
widersprüchliche REST-Antworten erzeugen.

## 8. T-26 braucht weitere Abhängigkeiten

T-26 hängt formal nur an T-24. Für die tatsächliche Implementierung verwendet es
aber:

- die eindeutige Instrumentadressierung aus T-21, insbesondere für generische
  Override-Endpunkte,
- die geladenen `FieldSpec`-Deklarationen und Kollisionsprüfung der Registry aus
  T-23.

Die Abhängigkeiten sollten entsprechend ergänzt werden. Die Reihenfolge in der
Spec erfüllt sie faktisch bereits; das Ticket sollte es auch ausdrücken.

## 9. T-25 muss „gleiches Profil“ an die Kompatibilitäts-ID binden

Verify #1 und #2 sagen pauschal, eine Quelle bzw. Paketversion im selben Profil
verwende dieselbe DB. Das ist nur richtig, solange die
**Profil-Kompatibilitäts-ID unverändert** bleibt.

Ein Wechsel von adjusted auf unadjusted Daily Close oder auf eine Quelle mit
anderer Listingauswahl darf nicht bloß deshalb alte Historien weiterverwenden,
weil der Profilname gleich lautet. Der Profilautor muss in diesem Fall die
Kompatibilitäts-ID erhöhen; dann gilt es fachlich als neue Generation mit frischer
DB.

Die beiden Verify-Zeilen sollten diesen Zusatz tragen.

## 10. Profilrotation braucht einen absturzfesten Zustandsübergang

T-25 sichert die Backup-Datei atomar, aber noch nicht den gesamten Übergang
`A aktiv → Backup A → B aktiv`. Ein Abbruch zwischen diesen Schritten darf beim
nächsten Start weder A erneut rotieren noch B mit As Datenbank öffnen.

Erforderlich ist ein kleiner, persistenter Zustandsautomat bzw. ein atomarer
Active-Profile-Marker mit mindestens:

- bisher aktive Profil-/Kompatibilitäts-ID,
- gewünschtes validiertes Zielprofil,
- Backup-Nummer und Status,
- Pfad der aktiven Datenbank,
- Ziel-`generation_id`.

Der Neustart muss jeden Zwischenzustand deterministisch fortsetzen oder auf A
zurückrollen können.

Außerdem braucht „A bleibt aktiv, wenn B ungültig ist“ eine gespeicherte
Last-known-good-Konfiguration samt Plugin-Umgebung. Die geänderte
`sources.yaml` zeigt sonst weiterhin auf B; nur die alte Datenbank zu behalten
reicht nicht, um A wieder zu starten.

## 11. `generation_id` beim Restore festlegen

Beim Zurückholen eines Backups sollte jede **Aktivierung** eine neue
`generation_id` erhalten, auch wenn im Backup eine alte ID gespeichert war.
Andernfalls kann ein Consumer bei einer wiederholten Wiederherstellung denselben
Identifier sehen und einen Cache behalten, obwohl sich der Dateninhalt geändert
hat.

Die fachlichen Listing-IDs innerhalb des Backups bleiben erhalten; die
Aktivierungs-/Datasetgeneration wird neu vergeben. Das trennt Datenidentität von
Betriebsereignis.

## 12. StockPortfolio-Arbeit braucht ein eindeutiges Ticket

T-25 lässt weiterhin offen, ob sein Scope erweitert oder auf ein
StockPortfolio-Ticket verwiesen wird. Vor Umsetzung sollte eine Variante gewählt
werden. Der Abnahmetest #8 kann nicht in einem Ticket mit Repo-Scope „StockInfo
(Backend + Dashboard)“ grün werden, wenn im Nachbar-Repo keine Änderung
autorisiert und verfolgt wird.

Das StockPortfolio-Ticket sollte neben `generation_id` auch festhalten:

- keine EUR-Ersatzwährung bei fehlender Kurswährung,
- mittelfristig `listing_id` als bevorzugten Maschinen-/Cache-Schlüssel,
- weiterhin Fallback auf ISIN/Symbol für alte gespeicherte Positionen,
- nur Kurs-/History-Caches invalidieren, niemals Portfolio und Ziele.

## 13. Zwei kleine Spec-Korrekturen

1. `Spec:331-332` sagt noch, eine neue API-Version mit `listing_id` sei erst
   nötig, wenn `symbol` seine Bedeutung verliert. Direkt danach wird
   `listing_id` verbindlich eingeführt. Gemeint ist vermutlich: keine
   **breaking Hauptversion** nötig, weil das Feld additiv ist. So sollte es dort
   stehen.
2. Die Aussage, Symbolkollisionen könnten „nur“ bei US-Börsen entstehen, gilt
   für die heutige Tabelle. Regionale Plugins können weitere MICs und
   Symbolkonventionen einführen. Die Laufzeitprüfung und `409`-Regel müssen daher
   allgemein gelten; „derzeit nur US“ ist die belastbare Formulierung.

## Aufwandseinschätzung

Die Ein-Tages-Timeboxes für T-21, T-25 und T-26 wirken nach der jetzt korrekt
erkannten Tiefe zu knapp:

- T-21 umfasst Migration, Zwischenzustand, UUID, neue Endpunkte,
  Ambiguitätsfehler und manuelle UI.
- T-25 umfasst Launcher-State-Machine, konsistente Sicherung, Restore,
  Last-known-good und StockPortfolio-Koordination.
- T-26 umfasst Backend-Persistenz, Typvalidierung, Overrides, REST, Dashboard und
  Kompatibilitätstests.

Das ist kein Architekturproblem, aber ein Planungsrisiko. Sinnvoller sind
kleinere Untertickets oder realistischere Timeboxes, statt die Sicherheitsfälle
unter Zeitdruck wegzulassen.

## Schlussfazit an Claude

Runde 5 kann architektonisch freigegeben werden, sobald die Semantik von
`listing_id`, Feldnamespace/Kollisionen und Versionsänderungen festgeschrieben
ist. Die übrigen Punkte sind konkrete Ticketnachschärfungen, keine erneute
Grundsatzdiskussion.

Besonders wichtig vor dem ersten Code: opake UUID für jede Zeile einschließlich
Legacy-Zwischenzustand; `details_version` bei jeder öffentlichen
Schemaveränderung; ein absturzfester Profilwechsel mit Last-known-good; und ein
explizit verfolgtes StockPortfolio-Ticket für Generation und Cache.

---

# Prüfung von Claudes Runde 6 und Antwort zu T-27

Geprüft wurden die mit Commit `4259c8d` überarbeitete Spec sowie T-20 bis T-27.

## Gesamturteil

Claude hat die 13 Punkte aus Runde 5 inhaltlich sauber übernommen. T-24 bis
T-26 bilden jetzt ein grundsätzlich stimmiges Modell:

- opake `listing_id` für jede Zeile, bei gleichzeitig genau einem aktiven
  Listing je ISIN,
- geschlossener, versionierter REST-Core und offene, separat versionierte
  Details,
- eine einzige generische Wahrheit hinter den acht bisherigen Top-Level-Feldern,
- frische Datenbank je inkompatiblem Profil mit Backup, Last-known-good und
  neuer `generation_id` je Aktivierung.

Die Architektur muss deshalb nicht erneut grundsätzlich geöffnet werden. T-27
ist aber noch nicht ausführungsreif: Testkit, interne Host-Tests und
Integrations-Harness sind in einem Ein-Tages-Ticket vermischt. Außerdem enthält
es zusammen mit T-23 noch einen technisch unmöglichen Hang-Test.

## Antwort 1: Fake → Real ist richtig, braucht aber eine Freshness-Regel

Fake → Real ist die richtige Grundlage. Ein bloßer `--real`-Schalter reicht
aber nicht, weil niemand zuverlässig bemerkt, dass er seit Monaten nicht mehr
gelaufen ist. Aufzeichnungen sollten mindestens folgende maschinenlesbare
Metadaten tragen:

- `recorded_at`,
- Zeitpunkt des letzten erfolgreichen Real-Laufs,
- Plugin- und Upstream-API-Version, soweit bekannt,
- kanonische Signatur der abgedeckten Szenarien.

Eine Altersprüfung ist sinnvoll, darf aber den normalen Offline-Test nicht nach
Kalenderzeit rot werden lassen. Sonst kann ein Contributor ohne Provider-Key
nach Ablauf der Frist nichts mehr bauen. Daher zwei Gates:

1. `make test-plugin-api` läuft strikt offline. Unerwartete Requests und
   Netz-Passthrough sind Fehler; fehlende Metadaten oder nicht bereinigte
   Secrets ebenfalls. Alter erzeugt höchstens einen klaren Hinweis.
2. Ein eigener Release-/Maintenance-Check schlägt bei überalterter oder nie real
   bestätigter Aufzeichnung fehl und verlangt `pytest --real` beziehungsweise
   eine Erneuerung.

Die Frist sollte pro Plugin festlegbar sein. Ein wenig veränderlicher
Referenzdienst braucht eine andere Frist als ein Provider ohne stabile
API-Version. Entscheidend ist außerdem: Der Real-Lauf gehört in den Release-
Prozess des **jeweiligen Plugins**. StockInfo kann nicht die Schlüssel und
Kontingente sämtlicher fremder Plugins besitzen.

„Dieselben Tests“ sollte dieselben Szenarien und semantischen Invarianten
bedeuten, nicht bytegleiche Antworten. Preis, Abrufzeitpunkt und teilweise
Metadaten ändern sich legitim. Beim Aufzeichnen müssen Header, Query-Parameter,
Body, Cookies und gegebenenfalls sensible Antwortfelder bereinigt werden.
Außerdem ist vor dem Commit roher Provider-Antworten zu prüfen, ob deren
Nutzungsbedingungen das erlauben.

Freshness beweist allein keine Gültigkeit. Maßgeblich bleibt ein erfolgreicher
Real-Lauf; die Altersgrenze sorgt nur dafür, dass er nicht vergessen wird.

## Antwort 2: drei Testebenen statt eines allwissenden Contract-Tests

Claudes Grenze ist im Kern richtig. Man kann sie präziser in drei Ebenen teilen:

1. **Plugin-Contract:** Typen, deklarierte Felder, Einheiten, Fehlerfälle,
   Secrets und das Verhalten bei ungültigen Eingaben. Dies gehört in das
   öffentliche Testkit.
2. **StockInfo-Integration:** Kettenreihenfolge, `NotResponsible`, `NotFound`,
   `Unavailable`, Merge, Registry, Schutzschalter, Persistenz und REST-
   Projektion. Dies sind Tests des Hosts und gehören in T-20, T-23, T-24 und
   T-26, nicht vollständig in das öffentliche Pluginpaket.
3. **Markt-Akzeptanz:** Vom Pluginautor kuratierte Golden Cases wie
   `ISIN -> erwarteter ticker, MIC, Name/Typ und Währung`. Sie sollen gegen
   Aufnahme und Real-API laufen. Nur hier lässt sich ein bekanntes kanadisches
   oder russisches Papier fachlich gegen eine unabhängige Erwartung prüfen.

Maschinell prüfbar sind durchaus fachliche Invarianten: ISIN-Prüfziffer,
Übereinstimmung von Anfrage- und Ergebnis-ISIN, echter MIC statt Sammelcode,
gültige Währung, endliche Zahlen, sinnvolle Datumsreihenfolge, keine doppelten
Tagespunkte, Typ-/Einheitenverträglichkeit und deklarierte Plausibilitätsgrenzen.

Nicht allgemein beweisbar ist, dass der Provider bei jedem zukünftigen Papier
das vom Nutzer gewünschte Listing gewählt hat. Auch ein formal korrektes
`(ticker, mic)` kann fachlich das falsche Listing sein. Golden Cases erhöhen die
Sicherheit erheblich, ersetzen aber nicht die Validierung durch jemanden, der
den Markt und das konkrete Papier kennt. Das sollte ausdrücklich als Grenze in
der Plugin-Dokumentation stehen.

## Antwort 3: T-27 muss vor Abschluss von T-23 greifen, aber geschnitten werden

„Vor dem ersten fremden Plugin“ ist zu spät. Laut T-23 ist die App selbst der
erste Plugin-Autor; yfinance und justETF sollen den Vertrag bereits über
denselben Weg benutzen. Das Testfundament muss daher vor oder parallel zu T-23
entstehen, und T-23 darf erst abgeschlossen werden, wenn seine Registry- und
Kettentests damit laufen.

Das aktuelle „hängt an nichts“ verdeckt jedoch Abhängigkeiten. Empfohlener
Schnitt:

- **T-27a, früh:** öffentlicher Contract-Runner, striktes Record/Replay,
  Secret-Scrubbing, Freshness-Metadaten, `FakeSource` und HTTP-Beispiel. Für die
  vollständige Rollenabdeckung braucht dieser Teil die in T-22 fehlenden
  Daily-/FX-Protokolle.
- **T-20/T-23:** Ketten- und Registry-Tests mit den Doubles. Die kaputten
  Plugin-Fixtures sind Abnahmemittel von T-23.
- **T-23-Integration oder T-27b, danach:** Ein Plugin in eine echte temporäre
  StockInfo-Instanz laden und einen Request bis zur REST-Antwort prüfen.
- **T-25:** injizierbare Uhr und Tests der Profilrotation. Diese Uhr ist
  Host-Infrastruktur und kein Bestandteil des öffentlichen Pluginvertrags.

Damit gibt es keinen Kreis „T-27 prüft T-23, hängt aber selbst an T-23“. T-27a
liefert die Werkzeuge; die jeweiligen Umsetzungstickets besitzen ihre
fachlichen Host-Tests.

## Verbleibender technischer Widerspruch: ein echter Hang öffnet so keinen Circuit

T-23 Verify `#5` und T-27 Verify `#8` behaupten sinngemäß: Ein Plugin hängt,
der laufende Aufruf wird nicht abgebrochen, aber der Schutzschalter greift ohne
echte Wartezeit. Das folgt aus dem beschriebenen In-process-Modell nicht.

Ein Circuit Breaker kann einen Fehler erst zählen, wenn der Aufruf fehlschlägt,
zurückkehrt oder ein übergeordneter Timeout den Aufrufer freigibt. Bei einem
wirklich endlos hängenden synchronen Aufruf und ohne Worker-/Future-Timeout
kehrt die Anfrage nie zurück; eine Fake-Uhr ändert daran nichts. Die Spec sagt
zugleich ausdrücklich, dass die Registry laufende Aufrufe nicht abbrechen kann
und I/O-Zeitgrenzen Sache des Plugins sind.

Für das gewählte einfache In-process-Modell sollten daraus zwei ehrliche Tests
werden:

- Eine Quelle liefert/erzeugt wiederholt `Unavailable`; danach öffnet der
  Circuit, weitere Aufrufe werden unterdrückt und Half-open/Reset wird mit
  Fake-Uhr geprüft.
- Ein absichtlich endlos hängendes Plugin ist als **nicht beherrschbare Grenze**
  dokumentiert und wird nicht mit einem vermeintlich wirksamen Circuit-Test
  versehen.

Soll auch der erste hängende Aufruf zeitlich begrenzt zum Client zurückkehren,
braucht das Design ausdrücklich einen Executor-/Worker-Timeout samt Begrenzung
hängender Threads oder echte Prozessisolation. Das wäre eine andere, deutlich
größere Architekturentscheidung.

## Kleine Restkorrekturen

1. Das T-26-Beispiel zeigt `core` weiterhin als flaches Array, während T-24 es
   korrekt nach `quote`, `instrument`, `daily` und `fx` gliedert. T-26 sollte
   dieselbe Form zeigen.
2. Im selben Beispiel steht noch, `details_version` erhöhe sich nur, wenn Felder
   dazukommen. Die Tabelle darunter sagt korrekt: bei jeder öffentlichen
   Schemaänderung.
3. T-26 lässt als API-Typ sowohl monotone Zahl als auch Fingerabdruck offen.
   Der REST-Vertrag muss einen Typ wählen. Empfehlung: nichtnegative, innerhalb
   einer `generation_id` monotone Ganzzahl; gecacht wird immer unter
   `(generation_id, details_version)`.
4. Das StockPortfolio-Folgeticket ist entschieden, aber noch nicht angelegt.
   T-25 Verify `#8` bleibt deshalb zu Recht offen; vor Umsetzung/Abnahme muss
   das Ticket im Nachbar-Repo tatsächlich existieren.
5. Ein Tag für Recorder, Scrubbing, Fake/Real, Doubles, kaputte Plugins,
   HTTP-Beispiel und Integrations-Harness ist nicht realistisch. Der Schnitt in
   T-27a/T-27b macht den Aufwand erst seriös schätzbar.

## Schlussfazit an Claude

Runde 6 ist für den fachlichen Plugin-, Profil- und REST-Vertrag akzeptiert.
Für T-27 lautet die Entscheidung: Fake → Real plus getrennte Freshness-Gates,
automatische Plausibilitätsprüfungen plus plugin-eigene Golden Cases, und das
Testfundament vor Abschluss von T-23. Vor Umsetzung bitte den unmöglichen
Hang-Test korrigieren, T-27 nach öffentlichem Testkit und Host-Integration
schneiden sowie die drei kleinen `/fields`-Widersprüche beseitigen.

---

# Konkreter Vorschlag zur umfassenden Testbarkeit

Dieser Abschnitt ist als umsetzbarer Zielzustand für Spec und Tickets gedacht.
„Testbar“ sollte nicht nur heißen, dass ein Plugin eine Basisklasse erbt. Ein
Plugin muss isoliert, in einer Quellenkette, in einer echten StockInfo-Instanz
und am stabilen REST-Rand prüfbar sein.

## 1. Alle fünf Pluginrollen brauchen Contract-Suiten

Der jetzige SDK-Code besitzt `ResolverContract` und `MetadataContract`. Für eine
vollständig austauschbare Quellenstruktur müssen nach T-22 dieselben
Testmöglichkeiten für alle öffentlichen Rollen existieren:

| Rolle | Verbindliche Tests |
|---|---|
| Resolver | Zuständigkeit, bekannt, unbekannt, Fehler, gültiger Ticker und echter MIC |
| Metadata | deklarierte Felder, Typ, Einheit, Währung bei Beträgen, Herkunft, Plausibilität |
| Quote | Preis und Pflichtwährung, Zeitpunkte, endliche Werte, Fehler statt Raten |
| Daily | Datum, Schlusskurs, Währung, Sortierung, keine Duplikate, adjusted/unadjusted-Semantik |
| FX | Base/Quote, positive endliche Rate, Zeitpunkt, Identitätsfall und Fehlerfall |

Gemeinsame Tests für jede Rolle:

- stabiler eindeutiger Quellenname und unterstützte `api_version`,
- gültige Konfiguration sowie verständliche Diagnose bei fehlender
  Pflichtkonfiguration,
- kein Durchreichen fremder Exceptions,
- nur deklarierte Ergebnisarten und Felder,
- klarer Unterschied zwischen „nicht zuständig“, „nicht gefunden“ und
  „vorübergehend nicht verfügbar“, soweit die Rolle diese Zustände kennt,
- keine Änderung globalen Zustands zwischen zwei Testfällen.

Damit wird vermieden, dass ein alternatives Plugin zwar die ISIN auflösen kann,
für Quote, Historie oder FX aber erneut implizit an yfinance gebunden bleibt.

## 2. Ein Szenarioformat für Offline, Real und Golden Cases

Ein Pluginautor sollte seine Fälle nur einmal beschreiben müssen. Ein Fall
enthält mindestens:

- stabile Fall-ID,
- Anfrage,
- erwartete Ergebnisart,
- bei einem bekannten Papier die unabhängig festgelegten Kernwerte wie ISIN,
  Ticker, MIC, Instrumenttyp und erwartete Währung,
- optionale Plausibilitätsregeln für dynamische Werte,
- Kennzeichnung, ob der Fall im Real-Modus laufen darf und welche Credentials
  er benötigt.

Dasselbe Szenario läuft dann in zwei Betriebsarten:

1. **Replay:** deterministisch und strikt ohne Netz, auf jedem Commit.
2. **Real:** gegen den echten Provider, manuell, geplant oder vor einem
   Pluginrelease.

Der erwartete Ticker/MIC darf dabei nicht aus der aufgezeichneten Antwort als
Erwartung erzeugt werden. Sonst bestätigt der Test nur, dass ein möglicherweise
falscher Treffer reproduzierbar falsch ist. Golden-Erwartungen sind kleine,
bewusst geprüfte Daten und getrennt von Provider-Aufzeichnungen zu pflegen.

## 3. HTTP-Testbarkeit als empfohlener Bauweg vorgeben

Record/Replay wird unnötig schwierig, wenn jedes Plugin seine HTTP-Bibliothek
beliebig und fest verdrahtet. Der Pluginvertrag muss keine bestimmte Bibliothek
erzwingen, das SDK sollte aber einen klaren Referenzweg anbieten:

- Beispielplugins erhalten Client/Transport und Uhr per Konstruktor,
- das SDK stellt einen kleinen Replay-Transport oder Adapter bereit,
- Real- und Replay-Modus tauschen nur diesen Transport aus,
- ein Offline-Test blockiert zusätzlich Socketzugriffe; fehlende Aufzeichnungen
  dürfen niemals still ins Netz fallen.

Für abweichende HTTP-Bibliotheken darf ein Autor einen eigenen Adapter
verwenden. Entscheidend ist die nach außen prüfbare Eigenschaft, nicht die
konkrete Bibliothek. Die Dokumentation sollte den injizierbaren Referenzweg
zeigen, weil er für neue und per Vibe-Coding erstellte Plugins erheblich
einfacher und sicherer ist als ein selbstgebauter Mock-Aufbau.

## 4. Wiederverwendbare Doubles, aber Host-Tests beim Host belassen

Das SDK sollte kleine skriptbare Doubles liefern:

- vorgegebene Antworten pro Anfrage,
- Aufrufprotokoll für Reihenfolge und Anzahl,
- `Resolved`, `NotResponsible`, `NotFound`, `Unavailable`, Exception und
  ungültige Antwort,
- kontrollierbare Verzögerung, aber **kein** behaupteter Abbruch eines endlos
  hängenden synchronen Aufrufs,
- Fake-Uhr für TTL, Circuit-Reset und Half-open.

Die Doubles sind Werkzeug. Die Verantwortung für die Kettensemantik bleibt bei
StockInfo:

- T-20 testet die Aggregation der Ergebnisarten bis zum richtigen HTTP-Status.
- T-23 testet Reihenfolge, Registry, Fehlerisolation und Circuit Breaker.
- T-26 testet Merge, Persistenz, Overrides und REST-Projektion der Details.
- T-25 testet Profilrotation, Backup, Restore und Generation mit eigenen
  Fehlerpunkten.

So wird das öffentliche SDK nicht mit internen StockInfo-Implementierungsdetails
beladen.

## 5. Ein echter Host-Harness

Zusätzlich zu isolierten Contracts braucht es einen kleinen Integrationslauf:

1. temporäres Datenverzeichnis und leere Datenbank erzeugen,
2. Beispielplugin als Datei und als Entry-Point laden,
3. Profil/Quelle validieren,
4. StockInfo-App mit Testkonfiguration starten,
5. Papier über den öffentlichen REST-Endpunkt aufnehmen,
6. Quote, Instrument, Details und `/fields` abfragen,
7. prüfen, dass Core, `listing_id`, `generation_id`, Herkunft und unbekanntes
   Detailfeld korrekt ankommen,
8. Instanz und temporäre Daten vollständig abbauen.

Dieser Lauf braucht keinen echten Serverprozess; eine In-process-ASGI-App mit
temporärem Dateisystem genügt. Entscheidend ist, dass Registry, Container,
Service, Repository und Pydantic-REST-Modell gemeinsam durchlaufen werden. Ein
isolierter Contract-Test kann Fehler zwischen diesen Schichten nicht finden.

## 6. Profilwechsel mit deterministischen Fehlerpunkten testen

T-25 ist sicherheitskritischer als ein normaler Unit-Test. Der
Profilwechsel-Service sollte deshalb benannte Fehlerpunkte besitzen, die nur im
Test aktiviert werden:

- nach Validierung von B,
- während der temporären Sicherung,
- nach Veröffentlichung der Sicherung,
- nach Schreiben des Übergangsmarkers,
- nach Anlegen der frischen Datenbank,
- direkt vor und direkt nach Aktivierung von B.

Für jeden Punkt: Abbruch simulieren, neuen Prozesszustand erzeugen und Recovery
ausführen. Danach darf genau eine vollständige Generation aktiv sein, kein
Backup überschrieben sein und A muss über Last-known-good vollständig startbar
bleiben. Restore derselben Sicherung zweimal muss zwei neue `generation_id`s,
aber dieselben enthaltenen `listing_id`s ergeben.

Diese Tests benötigen temporäre Verzeichnisse, eine injizierbare Uhr und
kontrollierte UUID-Erzeugung. Reale Wartezeiten oder Manipulation der
Systemuhr gehören nicht in die Suite.

## 7. Installation und Testbarkeit verbinden

Weil die Installation so einfach wie möglich bleiben muss, sollte der Nutzer
nicht selbst pytest-Kommandos zusammensuchen. Vorgeschlagen ist ein einheitlicher
Preflight, den Launcher und Entwickler verwenden:

```text
stockinfo plugin check <paket-oder-datei>
```

Der Check läuft ohne dauerhafte Änderung der aktiven Instanz und liefert
maschinenlesbare sowie verständliche Diagnosen für:

- Import und Manifest/Entry-Point,
- unterstützte API-Version,
- eindeutige Namen und Felddeklarationen,
- Pflichtkonfiguration ohne Ausgabe von Secrets,
- Rollenabdeckung des Profils,
- kurzer Offline-Selbsttest, sofern das Plugin Testfälle mitliefert.

Der Profilwechsel verwendet denselben Preflight vor jeder Rotation. Damit gibt
es keine zweite, abweichende Validierungslogik. Ein erfolgreicher Check beweist
nicht die fachliche Richtigkeit des Providers, verhindert aber, dass ein
Syntaxfehler, fehlendes Wheel oder unvollständiges Profil die aktive
Datenbankgeneration ablöst.

## 8. REST- und StockPortfolio-Kompatibilität

StockInfo veröffentlicht versionierte JSON-Fixtures für mindestens:

- Instrumentliste,
- Quote,
- Daily History,
- FX,
- `/fields`,
- Fehler `404`, `409` und `502`,
- Antworten mit und ohne offene Details.

StockInfo prüft die Fixtures gegen seine Pydantic-/OpenAPI-Modelle.
StockPortfolio prüft seine Mapper gegen exakt diese veröffentlichten Fixtures,
ohne das StockInfo-Repo zur Testzeit zu klonen. Ein kleiner Release-Smoke-Test
lädt zusätzlich eine bestehende StockPortfolio-Position gegen eine frische
Profil-Datenbank.

Unbekannte Detailfelder müssen ignoriert oder generisch dargestellt werden;
fehlende Core-Pflichtfelder müssen dagegen sichtbar fehlschlagen. Genau diese
Asymmetrie ist der wichtigste Consumer-Vertrag des Pluginmodells.

## 9. Empfohlene Test-Gates

| Zeitpunkt | Pflicht |
|---|---|
| jeder StockInfo-Commit | SDK-Contracts, Host-Unit-/Integrationstests, REST-Fixtures, kein Netz |
| jeder Plugin-Commit | Contract-Suite und Replay-Golden-Cases, kein Netz |
| geplant/vor Pluginrelease | Real-Golden-Cases und Freshness-Prüfung |
| StockInfo-Release | Host-Harness, OpenAPI-Kompatibilität, Profilwechsel-Recovery |
| StockPortfolio-Release | Mapper gegen veröffentlichte Fixtures, Generation-/Cache-Test |

Provider-Ausfälle dürfen den normalen Build nicht rot machen. Ein Real-Test
darf sehr wohl fehlschlagen und die Veröffentlichung des betroffenen Plugins
blockieren; er darf aber nicht die gesamte Offline-Entwicklung von StockInfo
lahmlegen.

## 10. Vorgeschlagener Ticketzuschnitt

T-27 sollte nicht als ein Tag Arbeit umgesetzt werden:

1. **T-27a – Contract-Kit:** vollständige Contracts für alle Rollen,
   Szenarioformat, Golden Cases und Doubles.
2. **T-27b – HTTP Fake→Real:** injizierbarer Referenztransport,
   Record/Replay, Socket-Sperre, Secret-Scrubbing und Freshness-Gate.
3. **T-23 – Host/Registry:** kaputte Plugin-Fixtures, Ketten- und
   Circuit-Tests sowie Preflight.
4. **T-23b oder eigenes Integrationsticket:** temporärer Host-Harness vom
   Plugin bis zur REST-Antwort.
5. **T-25:** Recovery-/Crash-Matrix für den Profilwechsel.
6. **StockPortfolio-Ticket:** Consumer-Fixtures, `generation_id` und gezielte
   Cache-Invalidierung.

T-27a/T-27b entstehen vor oder parallel zu T-23; T-23 darf ohne diese
Abnahmewerkzeuge nicht als fertig gelten.

## Definition of Done für „umfassend testbar“

Die Pluginstruktur ist erst umfassend testbar, wenn mindestens Folgendes
nachgewiesen ist:

- jede öffentliche Rolle hat eine Contract-Suite,
- ein echtes HTTP-Beispiel läuft offline per Replay und optional real,
- der Offline-Lauf kann technisch nicht ins Netz ausweichen,
- Aufzeichnungen enthalten keine Secrets und besitzen Freshness-Metadaten,
- bekannte reale Listings werden gegen unabhängig gepflegte Golden Cases
  geprüft,
- kaputte Plugins verhindern weder App-Start noch Nutzung gesunder Quellen,
- ein Plugin wird einmal vollständig bis zur REST-Antwort durchlaufen,
- offene Detailfelder überleben Registry, Merge, Datenbank, Overrides und REST,
- Profilwechsel und Restore bestehen die Crash-Matrix,
- StockPortfolio besteht die veröffentlichten Core-Fixtures und reagiert
  korrekt auf eine neue `generation_id`,
- die Grenze eines endlos hängenden In-process-Plugins ist ehrlich dokumentiert.

Mit diesem Zuschnitt ist die Pluginstruktur nicht nur theoretisch testbar. Ein
kanadischer oder russischer Autor kann sein Plugin lokal mit einem einfachen
Offline-Befehl prüfen, den echten Provider gezielt gegenprüfen und vor der
Aktivierung denselben Preflight verwenden, den StockInfo selbst nutzt.
