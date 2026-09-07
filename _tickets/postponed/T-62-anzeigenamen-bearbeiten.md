# T-62 · Anzeigenamen eines Instruments bearbeiten

**Zurückgestellt auf Mikes Auftrag vom 2026-09-07.** Seit Verwendung des
Langnamens passt die Anzeige. Eine manuelle Namensbearbeitung wird aktuell
nicht benötigt; die ursprüngliche Spezifikation bleibt für einen späteren
Bedarf erhalten. Keine Umsetzung beauftragt.

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | zurückgestellt · Langname genügt | ~3–5 h inklusive Tests und Browserprüfung, Schätzung | Persistenter Anzeigename, API und Editor | — |

- **Angelegt:** 2026-09-07, auf Mikes Auftrag während der UI-Abnahme T-56
- **Anlass:** T-56, Frage A. Nach Aufnahme von `SAP.DE` sieht Mike
  `SAP SE                        I` und möchte den Namen selbst bearbeiten können.
- **Priorität:** Noch nicht in die aktive Prioritätskette eingeordnet.
  Dieses Ticket startet keine Implementierung und macht T-56 nicht erneut zum Gate.

**Löst:** Mike kann beispielsweise `SAP SE` als eigenen Anzeigenamen speichern.
Der Name bleibt bei Neuladen und Kurs-/Metadatenaktualisierung erhalten;
„Auf Quellennamen zurücksetzen“ entfernt die manuelle Vorgabe.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung ·
◑ teilweise · ➖ keine Live-Verifikation. Die KI trägt konkrete Belege nach.
Die folgenden Fragen sind Funktionsnachweise und brauchen keine Human-Spalte.

| # | Where | Look for | AI |
|---|---|---|:--:|
| 1 | Dashboard, Tabelle und mobile Karte | Bei `SAP.DE` den Anzeigenamen auf `SAP SE` ändern und speichern: Beide Ansichten zeigen den neuen Namen; der bisherige Klick zum Öffnen der Details funktioniert weiterhin | ➖ |
| 2 | Öffentlicher Schreibweg → DB → Bestandsliste | Nach Speichern, Browser-Neuladen und normalem App-Neustart bleibt `SAP SE` erhalten | ➖ |
| 3 | Kurs- und Metadatenaktualisierung | Die Quelle liefert nach der Bearbeitung einen anderen Namen: Der manuelle Anzeigename bleibt sichtbar, der aktuelle Quellenname bleibt separat verfügbar | ➖ |
| 4 | Dashboard, Zurücksetzen | „Auf Quellennamen zurücksetzen“ zeigt den aktuell gespeicherten Quellennamen, auch nach Neuladen; wiederholtes Zurücksetzen ist unschädlich | ➖ |
| 5 | Editor und API | Abbrechen verändert nichts; reine Leerzeichen werden als Name abgewiesen; Speichernfehler bleiben sichtbar und der Entwurf erhalten. Rücksetzen ist eine ausdrückliche Aktion | ➖ |
| 6 | Bestehende manuelle Kennzahlen | Namensänderung/-rücksetzen löscht keine Kennzahlen; Kennzahlenänderung löscht keinen Anzeigenamen. Für Kennzahlen gilt weiterhin „Quelle gewinnt“ | ➖ |
| 7 | Identität und Isolation | Änderung betrifft genau das gewählte Instrument, auch bei zwei Listings mit gleichem Symbol; unbekanntes Ziel wird abgewiesen. Keine Änderungen an ISIN, Ticker, MIC, Kursen oder Historie | ➖ |
| 8 | Datenbankschema, normaler Produktstart | Frische DB und Bestands-DB starten regulär; Bearbeiten und Zurücksetzen funktionieren auf beiden. Bestehende Daten bleiben erhalten | ➖ |
| 9 | Browser DE/EN, Tastatur | Bearbeiten, Speichern, Abbrechen und Zurücksetzen sind in beiden Sprachen beschriftet und per Tastatur bedienbar; mobile Bedienung ohne unbeabsichtigtes Öffnen/Schließen der Details | ➖ |

---

## Details

### Vereinbartes Verhalten

1. **Eigener Anzeigename:** Eine optionale manuelle Vorgabe gewinnt vor dem
   Quellennamen. Der Quellenname bleibt getrennt gespeichert. Ohne Vorgabe gilt
   das bisherige Anzeigeverhalten. Führende und folgende Leerzeichen werden bei
   der Eingabe entfernt; eine danach leere Eingabe ist ungültig.
2. **Dauerhafte Speicherung:** Die Vorgabe gehört zum eindeutig ausgewählten
   Instrument und überlebt Refresh und Neustart. Zurücksetzen entfernt nur die
   Vorgabe und zeigt den zuletzt gespeicherten Quellennamen.
3. **Bedienung:** Bearbeiten-Knopf mit vorbelegtem Eingabefeld, Speichern,
   Abbrechen und ausdrücklichem Zurücksetzen. Tabelle und mobile Karte verwenden
   denselben Editor beziehungsweise denselben Schreibweg.

### Codebefund und Ansatz

- `dashboard/src/components/InstrumentsTable.vue` zeigt `item.name` als Knopf
  zum Öffnen der Details. Ein Editor muss diesen bestehenden Handgriff erhalten.
- `InstrumentCard.vue` zeigt denselben Namen in der mobilen Ansicht.
- `IsinEditor.vue` bietet bereits ein Bedienmuster mit Naive UI,
  Fokus, Enter und Escape; es ist eine Referenz, keine fertige Namensbearbeitung.
- `app/repository.py` schreibt gelieferte Namen beim Aktualisieren in
  `instruments.name`. Ein direktes Überschreiben dieses Feldes schützt einen
  manuellen Namen nicht gegen spätere Quellenlieferungen.
- `instrument_overrides` in `app/db.py` hält bereits manuelle Werte getrennt
  vom Quellenbestand. Die bestehende Speicherung kann nach Prüfung erweitert
  werden. `apply_overrides()` in `app/services/quote_cache.py` lässt jedoch
  bisher Quellenwerte gewinnen: **Für den Anzeigenamen gilt die umgekehrte
  Vorrangregel**, ohne die Kennzahlenregel zu verändern.
- Der vorhandene Overrides-Endpunkt schreibt einen vollständigen Satz;
  ausgelassene Felder werden gelöscht. Ein neuer Namen-Schreibweg darf deshalb
  weder andere Overrides verlieren noch durch deren Speicherung verloren gehen.

Vor dem ersten Produktedit wird der konkrete Scope-Vertrag ergänzt: Schemafeld,
Adressierung des Instruments, Request-/Response-Felder und ein vollständiges
Dateiinventar. Insbesondere ist festzulegen, wie Anzeigename und Quellenname in
den Dashboard-Antworten getrennt transportiert werden; eine Änderung der Bedeutung
von `name` im geschlossenen Core-Vertrag ist nicht stillschweigend enthalten.

Erwartete Bereiche: DB-Schema und bestehender Upgrade-Weg, Repository,
`quote_cache.py`, Dashboard-Router und Modelle, Dashboard-Typen, ein gemeinsamer
Editor/Schreibweg, Tabellen-/Kartenverdrahtung und DE/EN-Kataloge. Bestehende
Repository-/Overrides-/API- und Dashboardtests werden gezielt ergänzt.

### Entscheidende Akzeptanzfälle vor Flächenarbeit

Zuerst einen dünnen Pfad über den öffentlichen Schreibweg bis zur Bestandsliste
rot/grün belegen: Quellennamen speichern → `SAP SE` manuell setzen → Quelle
liefert einen geänderten Namen → weiterhin `SAP SE` lesen → zurücksetzen →
geänderten Quellennamen lesen. Ein minimaler Mutant „Quelle gewinnt auch beim
Anzeigenamen“ muss genau diesen Nachweis röten. Der Refresh-Beleg muss wirklich
einen abweichenden Namen liefern; ein unveränderter Quellenwert beweist die
Vorrangregel nicht.

Danach Browserbeleg in beiden Ansichten sowie frischer und bestehender DB über
den normalen Start. Prüfungen laufen mit isolierten Testdatenbanken. Die
Verify-Zeilen erhalten konkrete Testnamen beziehungsweise Browserbelege; grüne
Gesamtsuiten allein ersetzen sie nicht. Keine neue Testinfrastruktur erforderlich.

### Nicht-Ziele

- Keine automatische Bereinigung von Yahoo-/anderen Quellennamen oder geratenen
  Endungen wie `I` und `S`.
- Keine Umbenennung von Symbolen, Identitäten oder Einträgen in Quelldateien.
- Keine generische Stammdatenverwaltung und keine Änderung der bestehenden
  Vorrangregel für manuelle Kennzahlen.
- Kein Umbau von Plugins oder `ux-foundation`.

### Side-Effects

Eine additive Schemaerweiterung und ein Dashboard-Schreibvertrag sind erwartet.
Die manuelle Vorgabe muss in der normalen Datenbanksicherung enthalten sein.
Quellendaten, weitere manuelle Werte und bestehende Identitätszuordnungen dürfen
durch Bearbeiten oder Zurücksetzen nicht verändert werden.

### Auflösung

Nach `postponed/` verschoben. Der ursprüngliche Anlass ist durch den passenden
Langnamen entfallen; eine manuelle Namensbearbeitung wurde nicht implementiert.
