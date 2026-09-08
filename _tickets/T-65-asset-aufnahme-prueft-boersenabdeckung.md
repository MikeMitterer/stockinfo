# T-65 · Asset-Aufnahme prüft die Börsenabdeckung

Die Exchanges-Seite zeigt die vom aktiven Profil abgedeckten Börsen. **Die
Asset-Aufnahme prüft diese Abdeckung bisher nicht.** Außerdem verwendet die
Oberfläche beim Hinzufügen den Kurs-Endpunkt statt des Aufnahme-Endpunkts.
Beide Wege müssen dieselbe aktuelle Auskunft verwenden.

Beispiel: Im reinen YAML-Profil ist Xetra ohne passende Kurse ausgegraut.
`SAP.DE` und `SAP.XETR` sollen dann mit verständlichem Grund abgelehnt werden,
ohne Kursabfrage oder neue Datenbankzeile. Nach Ergänzung passender Dateidaten
ist die Aufnahme möglich. Eine Börsenzusage garantiert weiterhin keinen Kurs
für jedes Wertpapier.

**Stand:** Beauftragt, noch nicht implementiert. Ergänzung zu T-21, aus dessen
Nachtrag auf Empfehlung von Claude im Scope-Checkpoint `f3b383b` getrennt.
Mike hat die Umsetzung ausdrücklich beauftragt; sie folgt unmittelbar auf die
Review-Korrekturen der Exchanges-Anzeige. Kein weiterer Handgriff von Mike
erforderlich. Codex entwickelt, Claude prüft.

## Rückmeldungen von Mike

- „Ja dann implementiere das - das gehört zur Vollständigen implementierung des Plugins dazu“
- „Vergiss die UI-Tests nicht“

## Umfang und technische Nachweise

Zwei fachliche Änderungen: Abdeckungsprüfung am Aufnahmeweg und Umstellung
der UI auf diesen Weg samt DE/EN-Fehleranzeige. Erwartet höchstens
**11 Produktdateien**, **6 Test-/Dokudateien**, **700 manuelle Diff-Zeilen**:
`app/exchange_catalog.py`, `app/container.py`, Aufnahme-/Cache-/Quote-Service,
Aufnahme-/Kursrouter, `useInstrumentActions.ts`, `api/client.ts`, DE/EN;
Profiltests, Aufnahme-Regressionen, UI-Aktionen/Fehlertexte, Autorenanleitung,
dieses Ticket. Der bestehende POST-Transport erhält einen optionalen Body.
Keine neue Produktschicht, kein neuer Endpunkt, Plugin-Hook, Schema,
Konfigurationsformat, DB-Umbau oder Abhängigkeit. Normale Kurs-Lesewege und
Refresh bleiben erhalten. Keine Änderungen an Arbeitsdaten.

Gemeinsame Wissensquelle ist die validierte aktuelle Plugin-Deklaration,
einschließlich Quellenbereitschaft und Rolle `quotes`. Metadaten allein,
fehlende/fehlerhafte Zusagen oder deaktivierte Quellen versprechen keine
Abdeckung. Bei Symbolen wird vor Abfrage geprüft, bei ISIN nach Auflösung
und vor Kursabfrage/Speicherung. Paar- und ISIN-only-Identitäten benötigen
keinen MIC. Bekannte Listings dürfen die Prüfung nicht durch den Cache umgehen.
Gültige Paar-Eingaben wie BTC-EUR und vorhandene Quellenfehler bleiben korrekt.

### Verify

Alle REST-Läufe auf frischer temporärer DB mit normalem App-Start. Online-
Außengrenzen dürfen in automatisierten Tests normale Fakes verwenden;
Datei-Plugin, Registry, Service, Router und Persistenz bleiben echt.
Browserläufe verwenden eigene Testprofile und keine Arbeitsdaten.

| # | Lauf / Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | Aufnahme per Alias, MIC und ISIN in Online/Fallback und YAML-only | Abgedeckt: gespeichert; unversorgt: strukturierte Ablehnung, keine Kursabfrage/DB-Zeile; `/exchanges` stimmt überein. | ➖ |
| 2 | YAML ergänzen/entfernen, Zusage defekt/fehlend, Metadaten allein | Folgender Request nutzt aktuellen Bestand; keine alte/erfundene Abdeckung, auch bei bestehendem Cache. | ➖ |
| 3 | BTC-EUR, ISIN-only, unbekanntes Papier, Quellenausfall | Bestehende Identitäts- und Fehlersemantik bleibt erhalten; kein geratenes Listing aus nacktem Ticker. | ➖ |
| 4 | UI in DE/EN und beiden Profilen, erfolgreiche und abgelehnte Eingabe | POST mit Identifier; verständlicher MIC-Fehler; Erfolg erscheint, Ablehnung erzeugt keine Asset-Zeile. Desktop/Mobil bedienbar. | ➖ |

Vor Implementierung je neuem Unterschied eine rote Akzeptanzprobe am
öffentlichen Eingang; danach grün und gezielter negativer Mutant. Zuletzt
betroffene Gesamtsuiten, Lint/Build, Browserprüfung und unabhängiges Review.

### Side-Effects

Neuaufnahmen an bekannten, aktuell nicht abgedeckten Börsen werden explizit
abgelehnt. Die UI verwendet den zugesagten Aufnahmeweg. Bestehende Assets
werden weder gelöscht noch umgezogen.
