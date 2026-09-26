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
freigegeben. T-73 ist umgesetzt und unabhängig geprüft — **approved**, Claude,
Runde 1, `a559c09`. Keine Befunde, die die Freigabe verhindern; ein
nicht blockierender Doku-Hinweis (fehlendes Inhaltsverzeichnis in
`docs/rest-core-contract.md`, Altlast vor T-73) steht unten. Noch nicht deployed;
menschlicher Abschluss steht aus.

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
| Plugin mit zusätzlichem Typ, kein Asset dieses Typs vorhanden | `future-type` ohne gespeicherte Instrumente, keine Fachabfragen | ✅ |
| Konfiguration/Plugin-Menge geändert | Neue Konfiguration erst nach echtem Neustart sichtbar | ✅ |
| Leerzustand und fehlerhafte Quelle | Leer, unbekannt, falsche Rolle, Baufehler, Ausfall/Erholung und ungültige Deklaration geprüft | ✅ |
| Neuer unbekannter Typ | Offene Strings, keine Host-Enumeration; Rollenklassen getrennt, Duplikate entfernt | ✅ |
| Vertrag, Fixture und Doku | Core 4.4.0, Snapshot, drei echte HTTP-Fixtures und dokumentierte Semantik | ✅ |

## Für Mike

Keine fachliche Rückfrage zur Anforderung offen. Von Mike nach `30-doing`
eingeplant und anschließend zur Umsetzung aktiviert. Technischer Review ist
durch (approved); menschlicher Abschluss (Verschieben nach `40-done/`) steht aus.
T-73 ist das letzte Element der aktuellen `priority_chain`; danach `portfolio_review`.

## Doku-Abgleich

README/API-Tabelle, REST-Referenz/Typkatalog, Plugin-Anleitung/SUPPORTED_TYPES
und Vertrags-README/Fixtures aktualisiert. Datei- und Überschrifteninventar
abgeglichen; historische Entwürfe und UI-Anleitungen benötigen keine Änderung.


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
Begleitdateien: neuer API-Test, `tests/test_contract_openapi.py`, OpenAPI-Snapshot,
HTTP-Fixtures (drei), README, REST-Referenz, Plugin-Anleitung, Vertrags-README.
Budget: vier Produktdateien, zehn Test-/Dokudateien, höchstens 800 Diff-Zeilen
ab T-74-Prüfabschluss. Keine Plugin-API-Änderung, Datenmigration, UI-Arbeit,
Netzabfrage zum Ermitteln der Typen oder Änderungen in StockPortfolio.

Lessons: SI-CX-01 (frische Testdatenbank), SI-R-02 (kein hypothetischer
Kompatibilitätsbau), SI-T-66 (deklarierte Typen und heutige Verfügbarkeit
unterscheiden), AL-R-02 (alle konfigurierten Rollenklassen inventarisieren).
Lokale Fassungen vom 2026-09-11; AL-R-02 weiterhin `needs_review`.


## Prüfnachweise · Codex, 2026-09-26

15 API-Fälle mit echten Plugin-Dateien und Lifespan bestanden, Erstprobe vor
Implementierung 404. Drei HTTP-Fixtures auf frischen Datenbanken aufgezeichnet
und gegen die laufende API verglichen.

Voller Backend-Lauf: **1228 passed, 35 skipped, 10 failed**. Acht Fehler waren
DNS-Sperren zu justETF/OpenFIGI/Yahoo; Wiederholung mit Netzwerkfreigabe:
**8 passed**. Die anderen beiden betreffen `tests/test_yaml_profile.py`:
`test_die_tagesreihe_faellt_auf_die_datei_durch` und
`test_die_manuelle_history_kommt_als_tagesreihe`. Gegen einen separaten Archivstand
von **3d64132 vor T-73** identisch reproduziert: `period=1m` enthält am 26.09.
nur die Werte vom 26./27.08., die Tests erwarten auch den 25.08. Keine Regression
von T-73; im Ticket ausdrücklich offen gehalten, nicht nebenbei geändert.
Logs: `/private/tmp/stockinfo-t73-full-tests.log` und
`/private/tmp/stockinfo-t73-network-tests.log`. Vorbestehende Starlette-Warnung.

Prüfung: `.venv/bin/python -m pytest tests/test_api_instrument_types.py -q`.
Ruff Check für alle fünf Python-Dateien grün. Neue Dateien, Router und neue
Modellklassen formatgeprüft. Vollformatierung von `models.py` und dem bestehenden
OpenAPI-Test war bereits in 3d64132 rot; keine flächige Formatänderung.
Vollständiges AST-Bezeichnerinventar einschließlich eingebettetem Plugin geprüft:
englische Bezeichner; deutsche Testnamen als Projektausnahme. JSON-Schema bleibt
offen für Typstrings. `git diff --check` grün.

Gelesen: `/Users/macminipro/.codex/skills/code-standards/SKILL.md`, Referenzen
`architecture.md`, `python.md`, `quality.md`, `documentation.md`.
Vorhandene Registry, Rollenableitung und Generationsleser verwendet; Warnlog bei
ungültiger Deklaration. Lessons wie oben umgesetzt, keine neue globale Lesson.
Scope: vier Produktdateien, zehn Test-/Dokudateien, unter 800 Zeilen.

## Unabhängiger Review · Claude, Runde 1, 2026-09-26

**Ergebnis: approved.** Geprüft am eingefrorenen Stand `a559c09`. Volles
Ergebnis mit Belegen steht in
[STATUS](../STATUS.md#inbox--codex--t-73-runde-1--approved); hier nur die
Kurzfassung.

- `specs_by_name()`/`describe_chain` als **ein** Lesepfad bestätigt, keine
  zweite Registry-Sicht. Für alle vier eingebauten Specs nachgerechnet, dass
  `spec.roles` und `roles_of(declaration)` je Rolle übereinstimmen — der
  `invalid_declaration`-Zweig für „keine passende Deklaration“ ist Absicherung,
  aktuell nicht erreichbar, kein Bug.
- Die drei HTTP-Fixtures sind kein Beiwerk: ein eigener Test lädt sie und
  vergleicht sie live gegen echte Responses — selbst nachvollzogen.
- Eigener Testlauf: `tests/test_api_instrument_types.py` **15 passed**;
  voller Backend-Lauf **1236 passed, 35 skipped, 2 failed**. Die zwei Ausfälle
  liegen in `tests/test_yaml_profile.py`, einer Datei außerhalb des T-73-Diffs —
  keine Regression. Ursache (kalenderabhängiges `period=1m`-Fenster) selbst
  nachvollzogen, nicht nur geglaubt. Mein Lauf hatte durchgehend Netzzugriff
  und deckt damit auch die acht separat nachgezogenen Netzfälle ab.
- Formatbefund verifiziert: `app/models.py` und `tests/test_contract_openapi.py`
  waren schon vor T-73 (`3d64132`) nicht vollformatiert, an Stellen fern jeder
  neuen Klasse — keine Ausweitung durch dieses Ticket.
- AST-Bezeichnerinventar aller fünf berührten Python-Dateien selbst gezählt:
  0 deutsche Bezeichner außerhalb zulässiger Testnamen.

Nicht blockierend: `docs/rest-core-contract.md` hat weiterhin kein
Inhaltsverzeichnis trotz jetzt elf Abschnitten — Altlast aus T-24/T-21, von
T-73 nur um einen Abschnitt vergrößert, kein neuer Befund dieses Tickets.

Unabhängiger Review ist erledigt; menschlicher Abschluss bleibt offen.
