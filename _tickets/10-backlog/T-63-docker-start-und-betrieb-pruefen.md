# T-63 · Docker-Start und Betrieb prüfen

Die Docker-Verifikation aus T-16 #9 ist noch offen. Dieses Ticket prüft den
aktuellen Container mit eigener Konfiguration und eigenen Testdaten.
Die Tests wurden noch nicht ausgeführt und sind noch nicht eingeplant.

## Für dich

Aktuell kein Handgriff nötig. Zuerst erfolgt die technische Prüfung; ein
Befund wird hier mit reproduzierbarem Aufruf dokumentiert.

### Bisheriger Auftrag

Mike, 2026-09-07: „Kennzeichne es als erledigt - erstelle ein eigenes Ticket für die Docker-Tests“.
[T-16](solved/T-16-review-fixes-und-etf-quellen-testen.md) ist damit abgeschlossen;
dessen fehlender Docker-Nachweis wird nicht als bestanden übernommen.

## Umsetzung und technische Nachweise

| Repo | Time-box | Scope | GH-Issue |
|---|---|---|---|
| StockInfo | 1–2 h | Lokale Container-Verifikation, keine Produktänderung | — |

### Voraussetzungen und Ablauf

Docker muss erreichbar sein. Den vorhandenen lokalen Buildweg verwenden,
Image-Tag, Commit, Architektur und sämtliche ausgeführten Befehle im Nachweis
festhalten. Eigenen Containernamen, freien Port sowie ein temporäres
Datenverzeichnis verwenden. Das Dateiprofil aus `examples/` und das YAML-Plugin
in die Testumgebung kopieren. Keine laufende Instanz voraussetzen.

### Verify

Legende: ➖ keine Live-Verifikation. Alle Zeilen laufen ausschließlich in der
isolierten Docker-Testumgebung.

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | Image über den bestehenden lokalen Buildweg bauen | Build erfolgreich; Image-ID, Architektur und Commit festgehalten | ➖ |
| 2 | Container mit frischem Volume und eigener `--env-file` starten | Kein Konfigurationsfehler; insbesondere gültiges `strict_exchange` akzeptiert | ➖ |
| 3 | Start mit separater Env-Datei und nachgestelltem Leerraum am booleschen Wert wiederholen | Verhalten des ursprünglichen T-16-Befunds festhalten; `ValidationError` als offenen Befund dokumentieren | ➖ |
| 4 | `/health`, `/ready`, `/fields` und Dashboard über den veröffentlichten Testport abrufen | Dienst bereit; Feldkatalog und gebaute UI ohne Vite erreichbar | ➖ |
| 5 | Instrument aus der kopierten YAML-Vorlage per REST aufnehmen und abrufen | Identität, Kurs und Detailwerte entsprechen der Vorlage | ➖ |
| 6 | Eigenen Container entfernen und mit demselben Testvolume neu erstellen | Instrument und gespeicherte Werte bleiben erhalten | ➖ |
| 7 | Eigene Ressourcen aufräumen und Produktionsdaten vergleichen | Testressourcen beendet; Produktions-DB unverändert | ➖ |

Vor dem Lauf konkrete kopierbare Befehle je Prüfnummer ergänzen; die
Port- und Pfadwerte stammen aus der tatsächlich angelegten Testumgebung.
Ein fehlgeschlagener Check bleibt sichtbar. Notwendige Produktkorrekturen
gesondert eingrenzen.

### Side-Effects

Nur lokale Testimages, eigener Container und temporäre Daten. Kein Registry-Push,
Deployment oder Release. Bestehenden Container `stockinfo`, Betriebskonfiguration
und Produktionsdaten nicht verändern. Kein neues Makefile-Target.
Ein optionales Smoke-Skript gehört neben dieses Ticket; vorher vorhandene
Prüfwerkzeuge auf Wiederverwendung prüfen.

### Auflösung

Offen. Keine Docker-Tests ausgeführt.
