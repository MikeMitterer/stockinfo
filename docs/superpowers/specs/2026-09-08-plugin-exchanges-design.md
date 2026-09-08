# T-30 · Deklarierte Handelsplätze und Rollenunterstützung

## Ergebnis und Abgrenzung

Ein externes Plugin kann einen bisher unbekannten MIC samt Anzeigenamen
deklarieren. Nach normalem Start lässt sich `DEMO.XBUD` über den regulären
Aufnahmeweg verwenden; REST und Exchanges zeigen den Handelsplatz samt
deklarierenden Quellen und Unterstützung je Rolle. Bestehende Core-Aliase
und gespeicherte Assets bleiben unverändert. Kein weltweiter ISO-Import.

Dieser Entwurf konkretisiert Mikes genehmigten Umfang in T-30. Der ältere
UI-Entwurf vom 2026-09-07 bleibt als Vorarbeit erhalten; dessen Ausschluss
neuer MICs im Aufnahmeweg ist durch den aktuellen Ticketumfang abgelöst.

## Vertragsform

Das öffentliche Plugin-Paket erhält zwei unveränderliche Datentypen:

- `ExchangeSpec(mic, name, region, currency)`: MIC in kanonischer Schreibweise,
  nichtleerer Name, Region aus den bestehenden Anzeigegruppen und Währung
  nach der bestehenden Währungsprüfung. Ein Plugin deklariert hier neue
  Handelsplätze. Es kann keine Core-Aliase setzen oder ersetzen.
- `MicCoverage(mics, scope="market")`: explizite MIC-Tupel je Quellenrolle;
  `scope="inventory"` kennzeichnet bestandsabhängige Dateiquellen.

`Source.EXCHANGES` ist ein optionales Tupel von `ExchangeSpec`, standardmäßig
leer. `Source.MIC_SUPPORT` ist eine optionale Zuordnung von Rollenkennungen
zu `MicCoverage`, standardmäßig leer. Ein fehlender Rolleneintrag bedeutet
„nicht angegeben“, ein vorhandener Eintrag mit leerem MIC-Tupel „keine“.
Nur tatsächlich implementierte Rollen dürfen genannt werden. FX verwendet
Währungspaare und erhält keine MIC-Unterstützungsangaben.

Die Deklarationen sind Klassenmetadaten. Sie benötigen weder erfundene
Ticker noch `handles()`-Aufrufe, Konstruktoren oder Netzabfragen. Der Host
validiert Typen und Werte zentral; dieselbe strukturelle Prüfung steht dem
Autor-Harness zur Verfügung. Katalogabhängige Konflikte prüft allein der Host.

Es handelt sich um eine optionale Erweiterung: bestehende API-2-Plugins
bleiben lauffähig und melden keine erfundene Unterstützung. `API_VERSION`
bleibt 2, das Plugin-Paket erhält die additive Version 0.3.0. Neue Beispiele
verlangen mindestens diesen Paketstand. `data_version` bleibt unverändert,
weil keine gespeicherte Bedeutung geändert wird. `/exchanges` liegt außerhalb
des geschlossenen REST-Core; dessen Versionsnummer bleibt unverändert.

## Katalog und Konflikte

Der feste Core-Katalog bleibt die unveränderliche Basis. Die Registry bildet
vor dem Bau der Quellen einen vollständigen Katalog aus den Deklarationen
der im aktuellen Profil konfigurierten, erfolgreich geladenen Quellen.
Nur Namen in einer zulässigen Kette tragen bei. Eine vorübergehend nicht
einsatzbereite Quelle verliert ihre Definition nicht; sie zählt jedoch nicht
als aktive Unterstützung. Nicht konfigurierte Plugins tragen nichts bei.

Eine Referenz auf einen Core-MIC gehört in `MIC_SUPPORT`. Eine identische
Definition ist unschädlich, eine abweichende Definition wird zurückgewiesen.
Mehrere identische neue Definitionen werden zusammengeführt und behalten
alle deklarierenden Quellennamen. Widersprechen sich neue Definitionen,
werden alle beteiligten Quellen als ungültig diagnostiziert: kein erster
oder letzter Gewinner. Der Konfliktvergleich erfolgt vor Veröffentlichung
des neuen Katalogs, unabhängig von der Ladereihenfolge. Unbekannte MICs in
Unterstützungsangaben werden ebenfalls diagnostiziert.

Neue MICs verwenden den eigenen MIC als App-Suffix (`DEMO.XBUD`). Das ist
eine stabile App-Schreibweise, keine Anbieterkennung. Sie darf keinen
bestehenden Alias einer anderen Börse überdecken. Anbieterübersetzungen
bleiben im Plugin. Bestehende Börsen behalten ihre bisherige Schreibweise,
einschließlich der US-Plätze ohne Alias.

Die bestehenden Parser und die Ausgabe des Aufnahmepfads lesen denselben
aktiven Katalog. Ein zweiter REST-Katalog, der nur mehr Zeilen anzeigt, genügt
nicht. Register-/Profilwechsel invalidieren den aktiven Katalog; bei einem
Neustart ohne Plugin verschwinden dessen alleinige Definitionen und Angaben.
Die gespeicherten Zeilen werden dabei weder gelöscht noch umgeschrieben.

## REST und Oberfläche

`GET /exchanges` behält `catalog`, `default_exchange` und
`default_exchange_kind`. Börseneinträge erhalten zusätzlich alle
deklarierenden Quellen sowie Unterstützungsangaben mit Quelle, Rolle,
Deklarationsumfang und aktueller Einsatzbereitschaft. Die bestehende
`provenance` bleibt für Core-Einträge Core; bei mehreren identischen
Plugin-Deklarationen wird die erste alphabetische Quelle als stabiler
Repräsentant verwendet, die vollständige Liste verhindert Informationsverlust.
Unbekannte Abdeckung wird zusätzlich je aktiver Quelle/Rolle ausgewiesen,
damit eine leere Trefferliste nicht „keine Unterstützung“ behauptet.

Die UI zeigt MIC, Handelsplatz, Region und Quellenunterstützung. Namen und
Rollen machen Kursabruf und Tageshistorie unterscheidbar. Bestandsabhängig,
nicht einsatzbereit und nicht angegeben bleiben unterscheidbar. Es wird kein
erfolgreicher Live-Abruf versprochen. App-Suffix und Währung bleiben als
Zusatzinformation erhalten; der MIC ist die primäre Kennung.
Sammelcodes wie `US` stehen separat mit ihren Mitgliedern. Standardsymbol,
Suche und schmale Fenster werden berücksichtigt. Alle Texte DE/EN.

## Umsetzung in prüfbaren Schritten

1. Zuerst ein roter Akzeptanzfall mit echtem Verzeichnis-Plugin, frischer
   Datenbank und normalem Lifespan: `DEMO.XBUD` aufnehmen, Identität/Symbol
   speichern und Deklaration aus `/exchanges` lesen. Ohne Deklaration bleibt
   derselbe Eingang abgewiesen. Danach den kleinsten vertikalen Pfad bauen.
2. Konflikte, ungültige Angaben, Rollenunterschiede und Plugin-Entfernung
   ergänzen; jeden neuen Schutz durch einen gezielten Mutanten gegenprüfen.
   Entry-Point-Ladeweg zusätzlich prüfen. Keine Test-Transportinfrastruktur.
3. REST-Daten im Dashboard darstellen; Komponententests und Browserlauf
   für DE/EN und schmales Fenster. Autor-Harness und ausführbares Beispiel
   dokumentieren. Abschließend normale lokale Suite, ESLint und Build.

Entscheidende Orakel: neue MIC-Aufnahme bis Persistenz; identische versus
widersprüchliche Deklaration in beiden Reihenfolgen; Core-Alias und alte
Assets unverändert; Entfernen einer von zwei deklarierenden Quellen;
keine Unterstützung ohne Deklaration oder bei inaktiver Quelle; Rolle und
Bestandsabhängigkeit korrekt im REST und UI.

## Umfang zur Vorprüfung

Erwartet sind Plugin-Vertrag/Validierung/Harness/Beispiel, Core-Katalog und
Registry, Startverdrahtung, REST-Modelle und Dashboard-Route sowie
Dashboard-Typen/Exchanges/i18n. Dazu gezielte Backend-, Plugin- und UI-Tests
und Autorendokumentation. Voraussichtlich 16–20 Produktdateien sowie
8–10 Test-/Dokumentationsdateien und 1400–1800 manuelle Diff-Zeilen.

Damit liegt die Schätzung über dem allgemeinen 800-Zeilen-Riegel und berührt
mehrere öffentliche Flächen. Vor Produktcode geht dieser Entwurf als
Scope-Checkpoint an Claude. Der Checkpoint entscheidet über `continue`,
`reduce` oder `split`; er ist keine technische Freigabe der Implementierung.
