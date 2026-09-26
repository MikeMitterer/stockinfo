# T-73 · Verfügbare Asset-Typen für REST-Konsumenten

StockPortfolio muss die von StockInfo-Plugins unterstützten Asset-Typen für
seine Linkfilter dynamisch über REST abfragen können. Seine bisherige feste
Auswahl stock/etf ist unvollständig. Eine neue feste Liste der heute bekannten
Typen würde bei der nächsten Plugin-Erweiterung wieder veralten.

Beispiel: Ein Plugin unterstützt crypto oder einen künftig hinzukommenden Typ.
Dieser muss auswählbar sein, auch wenn noch kein entsprechendes Asset in der
Instrumentenliste oder im Depot vorhanden ist.

**Stand:** Konsumentenanforderung aus StockPortfolio, Mike am 2026-09-26:
„Die Typen kommen aus dem neuen Plugin … das ist dynamisch. Du musst die
Möglichen Typen über das REST-Api abfragen“. Mike hat anschließend beauftragt:
„Danach T-73 nach doing - Wichtig!“ Das Ticket liegt deshalb in `30-doing`;
Mike hat mit „Ja und? Los gehts“ die Umsetzung gestartet. T-74 ist technisch
freigegeben. Codex setzt T-73 um, Claude prüft anschließend über STATUS.md.

## Beleg und Auswirkung

- Lokaler Plugin-Vertrag deklariert SUPPORTED_TYPES; REST-Core behandelt type
  als offene Zeichenkette und nennt stock, etf, etc, fund, crypto, bond als Beispiele.
- Am 2026-09-26 wurden openapi.json, GET /sources und GET /fields von
  https://stockinfo.int.mikemitterer.at geprüft (Version 1.0.0, Core 4.3.0).
- /sources enthält name, role, position, configured, reason, cost, data_version;
  keine vollständige Typmenge. Der lokale SourceEntry-Vertrag bestätigt das.
- /fields.details[].scopes[].instrument_types beschreibt nur die Anwendbarkeit
  einzelner Zusatzfelder. Die Antwort enthielt etc, etf, fund; sie ist deshalb
  kein vollständiger Typkatalog. Eine Liste aus /instruments wäre ebenso
  vom zufälligen Bestand abhängig.

## Erwartung aus Konsumentensicht

- Eine dokumentierte REST-Auskunft liefert die verfügbaren Asset-Typkennungen
  aus der tatsächlichen Plugin-Konfiguration, unabhängig vom Instrumentenbestand.
- Die Bedeutung von verfügbar (z. B. geladen, konfiguriert, ausführbar) ist
  eindeutig dokumentiert. Entfernte/gestörte Plugins und eine leere Menge haben
  erkennbare Zustände; keine stillschweigende feste Ersatzliste.
- Neue Typkennungen können ohne StockPortfolio-Release übernommen werden.
- StockInfo bleibt Quelle der Angaben. Depotgruppen bleiben davon unabhängig.
- Vertrag und HTTP-Fixture erlauben einen Offline-Test des Konsumenten.

## Verify

| Prüfung | Erwartung | AI |
|---|---|:--:|
| Plugin mit zusätzlichem Typ, kein Asset dieses Typs vorhanden | Typ über REST verfügbar | ➖ |
| Konfiguration/Plugin-Menge geändert | Antwort folgt der dokumentierten Semantik | ➖ |
| Leerzustand und fehlerhafte Quelle | Dokumentiertes, unterscheidbares Verhalten | ➖ |
| Neuer unbekannter Typ | Keine geschlossene Konsumenten-Enumeration notwendig | ➖ |
| Vertrag, Fixture und Doku | Vollständige konsumierbare Beschreibung | ➖ |

## Für Mike

Keine fachliche Rückfrage zur Anforderung offen. Von Mike nach `30-doing`
eingeplant und anschließend zur Umsetzung aktiviert. Aktuell kein weiterer
Handgriff erforderlich; technischer Review und menschlicher Abschluss stehen aus.

## Doku-Abgleich

Bei Umsetzung REST-Vertrag und Konsumentenanleitung aktualisieren. Bisher nur
Bedarf erfasst; keine Produktänderung und keine technische Freigabe.


## Scope-Vertrag und Umsetzung

Ergebnis: `GET /instrument-types` gibt die deklarierten Typen der laufenden
Plugin-Konfiguration für REST-Konsumenten zurück, auch bei leerem Bestand.

1. Katalog aus `SUPPORTED_TYPES` der konfigurierten, geladenen Rollenklassen
   für Resolver, Kurse, Tagesreihen und Metadaten. FX allein zählt nicht als
   Asset-Unterstützung. Sortierte Vereinigung ohne Duplikate oder Ersatzliste.
2. Je Quelle/Rolle Typen und `status`: `available`, `unavailable`,
   `unknown_source`, `unsupported_role` oder `invalid_declaration`.
   `complete` sagt, ob alle ausgewählten Deklarationen lesbar sind. Bekannte
   Typen bleiben bei Betriebsstörungen erhalten; die Auskunft garantiert
   keine erfolgreiche Beschaffung eines bestimmten Instruments.
3. Core 4.4.0, dokumentierter GET-Endpunkt ohne Query, `Cache-Control: no-store`,
   HTTP-Fixtures für vollständige, leere und unvollständige Auskünfte.
   Änderungen an Plugin-Dateien und Konfiguration wirken nach Neustart.

Produktdateien: `app/services/instrument_types.py`, `app/models.py`,
`app/routers/fields.py`, `contract/core-contract.json`.
Begleitdateien: neuer API-Test, `tests/test_contract.py`, OpenAPI-Snapshot,
HTTP-Fixtures (drei), README, REST-Referenz, Plugin-Anleitung, Vertrags-README.
Budget: vier Produktdateien, zehn Test-/Dokudateien, höchstens 800 Diff-Zeilen
ab T-74-Prüfabschluss. Keine Plugin-API-Änderung, Datenmigration, UI-Arbeit,
Netzabfrage zum Ermitteln der Typen oder Änderungen in StockPortfolio.

Arbeitsschritte: API-Gegenproben schreiben und rot ausführen; Katalog und
Route implementieren; Vertrag/Fixtures/Doku ergänzen; gezielte Tests und
Backend-Suite prüfen; eigenständigen Prüfstand über STATUS.md übergeben.

Lessons: SI-CX-01 (frische Testdatenbank), SI-R-02 (kein hypothetischer
Kompatibilitätsbau), SI-T-66 (deklarierte Typen und heutige Verfügbarkeit
unterscheiden), AL-R-02 (alle konfigurierten Rollenklassen inventarisieren).
Lokale Fassungen vom 2026-09-11; AL-R-02 weiterhin `needs_review`.
