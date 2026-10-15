# README-Vorlage für StockInfo

Hinweise an den Agenten, der `README.md` oder `README.de.md` schreibt oder
aktualisiert. Diese Datei enthält keinen Text zum Übernehmen: Jeder Abschnitt
beschreibt, was hinein gehört und woher die Angaben kommen. Formuliere selbst.

Die Datei hat zwei Teile: zuerst Anweisungen für die Arbeit, dann die
nummerierten Abschnitte des README in ihrer Reihenfolge. Nur die nummerierten
Abschnitte erscheinen im README.

## Anweisungen

**Allgemeine Regeln** (Ausschlüsse, Kürze, nur Belegtes, Mermaid, zentrierter
Kopf, Absatzregel, Sprachfassungen, Bedienelemente im Wortlaut der App,
eingehende Anker) stehen im Skill `docs-conventions` und werden hier nicht
wiederholt. Verbotene Begriffe stehen mit Grund in `.docs-check.conf.sh` unter
`FORBIDDEN`.

**Sprachen.** `README.md` ist englisch, `README.de.md` deutsch. Die deutsche
Fassung verlinkt dieselben Dokumente; englische Ziele bekommen den Zusatz
„(englisch)“. Bedienelemente kommen aus `dashboard/src/i18n/en.ts`
beziehungsweise `de.ts`.

**Wohin was gehört.** Was das README nach dem Skill nicht aufnimmt, steht in
genau einem dieser Dokumente; das README verlinkt nur:

| Inhalt | Dokument |
|---|---|
| Voraussetzungen, Einrichten aus dem Checkout, Make-Targets, `.env`-Einstellungen, Dashboard-Entwicklung, REST-API-Referenz, Docker-Build und -Push, Tests, Release, Projektaufbau | `docs/development.md` (englisch) |
| Container starten, Compose, Speicher und Rechte, alle Container-Einstellungen, Sicherheit, Updates und Backups | `docker/README.md` (englisch; Docker-Hub-Regeln im Skill `docker-conventions`) |
| Installation über Unraid Apps, Template, appdata | `unraid/README.md` (englisch) |
| Quellenketten, Dateiquelle, Plugins | `docs/plugins.md`, `docs/plugin-authors.md` |
| Zusagen der REST-API | `docs/rest-core-contract.md` |
| Neuerungen eines Release | `docs/release-notes.md`, `CHANGELOG.md` |

**Funktionsliste.** Quelle sind die Seiten der Navigation
(`dashboard/src/components/AppHeader.vue`), die Bereiche der Einstellungen
(`settings.tab` in den i18n-Katalogen), die REST-Routen unter `app/routers/`
und die Standardquellen. Zahlen wie die Anzahl der Themes aus dem Code
(`THEME_IDS` in `@mmit/ux-foundation`). Beim Aktualisieren `feat`-Commits
seit dem letzten README-Commit gegen die Liste abgleichen.

## 1. Kopf

Zentriert: App-Icon (`dashboard/public/stockinfo-icon.png`, 96 × 96), Name
als Überschrift, fette Zeile mit dem Zweck, Sprachzeile, Link-Leiste zu
Funktionen, Schnellstart, Konfiguration, Docker-Anleitung und Entwicklerdoku.

## 2. Überblick

Zwei kurze Absätze: was StockInfo liefert (Abfrage per ISIN oder Symbol und
Börse, JSON mit Preis, Währung, Zeitpunkt, Name, ETF-Kennzahlen) und dass ein
Dashboard und die REST-API dazugehören. Darunter
`unraid/screenshots/dashboard.png` mit kursiver Bildunterschrift.

## 3. Warnung

Ein `> [!WARNING]`: keine Anmeldung, nicht ins Internet, nur im Heimnetz, von
außen per VPN. Quelle: Abschnitt „Security“ in `docker/README.md`.

## 4. Funktionen

Liste, je Eintrag fetter Name und kurze Beschreibung. Quelle siehe
Anweisungen. Eigene Werte verlinken auf Abschnitt 5.

## 5. Eigene Werte

Was der Detailbereich einer Zeile erlaubt, dass die Quelle Vorrang hat, und
wofür das gedacht ist (TER und Fondsgröße von ETFs außerhalb Europas). Bild
`unraid/screenshots/detail-area.png`.

## 6. Datenquellen

Tabelle der Standardquellen und wofür sie dienen; Hinweis auf
`sources.yaml`, `docs/plugins.md`, `docs/plugin-authors.md`. Pflicht: „Keine
offiziellen APIs“ samt Verantwortung des Betreibers. Quelle:
`app/providers/`, `docs/plugins.md`.

## 7. Schwester-App StockPortfolio

Dass StockInfo allein läuft und StockPortfolio optional ist und seine Daten
von StockInfo bezieht. Mermaid-Diagramm: Browser, StockPortfolio, Skripte,
StockInfo, Datenbank, Quellen. Vergleichstabelle (Zweck, läuft allein,
Docker-Image) und Link auf StockPortfolios Einrichtungsanleitung. Die
Überschrift bleibt „StockPortfolio: the companion app“; sie wird von
`unraid/README.md` verlinkt.

## 8. Schnellstart

`docker run` aus `docker/README.md`, Adressen von Dashboard und `/docs`, eine
`curl`-Abfrage. Dann ein Satz, was die Docker-Anleitung zusätzlich erklärt,
und der Link auf die Unraid-Anleitung.

## 9. Konfiguration

Tabelle der wichtigsten Punkte: Port, `/data`, `DEFAULT_EXCHANGE`,
`REFRESH_INTERVAL_HOURS`, `OPENFIGI_API_KEY`. Vorgaben aus
`docker/README.md`; dorthin für alle Einstellungen verlinken.

## 10. Entwicklung

Ein Satz und der Link auf `docs/development.md`.

## 11. Weitere Dokumentation

Liste mit Links und je einer kurzen Beschreibung: Docker-Anleitung,
Unraid-Anleitung, Quellenkonfiguration, Plugin-Anleitung, REST-Vertrag,
Entwicklerdoku, Changelog und Release Notes. Entwürfe unter
`docs/superpowers/` und das Ticket-Board nicht aufnehmen.

## 12. Support

Für den Eigengebrauch gebaut und frei geteilt; Issues und Pull Requests
werden gelesen, ohne Zusage auf Antwort, Fix oder neue Funktion.

## 13. Lizenz

Baustein `templates/license-eupl.md` aus dem Skill `docs-conventions`,
Wortlaut unverändert. Alle Werte und Links aus `LICENSING.md` und den dort
genannten Lizenzdateien; das bisherige README ist keine Quelle.
