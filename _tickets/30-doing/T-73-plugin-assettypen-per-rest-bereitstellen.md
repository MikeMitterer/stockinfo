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
die Umsetzung folgt nach T-74. Endpunkt und Vertrag sind noch nicht umgesetzt.

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
eingeplant. Während T-74 im Review ist, bleibt T-74 der aktive Auftrag in STATUS.

## Doku-Abgleich

Bei Umsetzung REST-Vertrag und Konsumentenanleitung aktualisieren. Bisher nur
Bedarf erfasst; keine Produktänderung und keine technische Freigabe.
