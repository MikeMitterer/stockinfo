# T-26: Plugin-Felder bis zur Detailansicht

Auftrag Mike: Codex implementiert, Claude verifiziert; T-26 blockiert den
Feldpunkt F in T-56. Bestehender Arbeitsbranch bleibt erhalten.

1. Plugin-Vertrag: Felddeklarationen um anwendbare Instrumenttypen ergänzen;
   globale Vorgaben bleiben kompatibel. Validierung von Typ, Einheit,
   Namespace und Konflikten beim Laden. Kein Fonds-Wissen im Dashboard.
2. Core-Katalog: aus konfigurierten, validierten Metadatenquellen ableiten,
   unabhängig von kurzfristiger Erreichbarkeit. Schema und monotonen Zähler
   atomar in SQLite speichern; `/fields` liefert den tatsächlichen Katalog.
3. Persistenz: generische Quellenwerte und manuelle Werte je Instrument/Feld,
   Herkunft und Zeitstempel. Bestehende acht Werte verlustlos übernehmen;
   bisherige API-Felder aus derselben Merge-Funktion projizieren.
4. Beschaffung: alle passenden Metadatenquellen feldweise zusammenführen;
   unbekannte deklarierte Felder erhalten. Fehlgeschlagene Abfragen löschen
   keine gespeicherten Werte. Quellenvorrang bleibt je Feld erhalten.
5. REST: `details` in Kurs und Bestand, generische Overrides über eindeutige
   Listing-ID. Deklaration, Anwendbarkeit und Schreibrechte serverseitig
   prüfen; alte Override-Endpunkte auf denselben Speicher führen.
6. Dashboard: Katalog und Instrumentdetails generisch darstellen, DE/EN-
   Beschriftungen, Zahl/Text/Boolean, Herkunft, manuelle und verdeckte Werte.
   Keine Typ-Tabelle im Frontend; BTC-EUR erhält keine Fondsfelder.
7. Nachweise: Migration, unbekanntes Feld, zwei Quellen, Kollisionen,
   Schreibschutz, Null/False/0, Schemawechsel und Cache-Weg testen. Vollsuite
   mit isolierter Datenbank, Browserlauf mit Datei-Plugin und unverändertem
   Betriebsbestand. Compiler-/AST-Inventar und statische Checks.
8. Übergabe: Ticket nach aktuellem Template, Produktstand festhalten,
   STATUS `ready_for_claude`/`owner: claude`, konkreter Reviewauftrag.
