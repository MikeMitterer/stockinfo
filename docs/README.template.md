# README-Vorlage für StockInfo

Hinweise an den Agenten, der `README.md` oder `README.de.md` schreibt oder
aktualisiert. Diese Datei enthält keinen Text zum Übernehmen: Jeder Abschnitt
beschreibt, was hinein gehört und woher die Angaben kommen. Formuliere selbst.

Die Datei hat zwei Teile: zuerst Anweisungen für die Arbeit, dann die
nummerierten Abschnitte des README in ihrer Reihenfolge. Nur die nummerierten
Abschnitte erscheinen im README.

## Anweisungen

**Allgemeine Regeln** (nur Belegtes, Mermaid für Zusammenhänge, Kopf
zentriert, Bedienelemente im Wortlaut der App) stehen im Skill
`readme-conventions` und werden hier nicht wiederholt.

**Abweichung vom Skill: Entwickleranleitung im README.** Der Skill hält
Make-Targets, Test- und Release-Abläufe aus dem README heraus. StockInfo hat
keine eigene Entwicklerdoku; laut `AGENTS.md` (Abschnitt „Dokumentation
gehört zur Änderung“) gehören Entwickleranleitungen ins Root-README,
Containeranleitungen in `docker/README.md`. Die Abschnitte 7 und 10 bis 13
bleiben deshalb im README. Eine Auslagerung in eine eigene Entwicklerdoku
unter `docs/` braucht eine eigene Entscheidung von Mike.

**Verbotene Begriffe** stehen mit Grund in `.docs-check.conf.sh` unter
`FORBIDDEN`; `make docs-check` prüft sie. Sie gelten auch für Codeblöcke.

**Zwei Sprachen.** `README.md` ist englisch, `README.de.md` die deutsche
Fassung, nach der GitHub-Konvention mit dem Sprachcode vor der Endung. Beide
folgen dieser Vorlage mit denselben Abschnitten in derselben Reihenfolge und
mit denselben Aussagen. Sie verlinken sich gegenseitig im Kopf. Bedienelemente
nennt die deutsche Fassung so, wie die deutsche Oberfläche sie zeigt
(`dashboard/src/i18n/`). Verlinkte Dokumente bleiben in ihrer Sprache; die
deutsche Fassung verlinkt dieselben Dateien.

**Eingehende Anker.** Andere Dateien verlinken auf Abschnitte von `README.md`
(etwa `#quick-start`, `#docker`, `#security-model`). `make docs-check` zeigt
sie. Wer eine Überschrift ändert, zieht diese Links mit.

**Feature-Liste:** Quelle sind die Abschnitte „What can it do?“ des
bisherigen README, die REST-Routen unter `app/routers/` und die Reiter des
Dashboards. Beim Aktualisieren `feat`-Commits seit dem letzten README-Commit
gegen die Liste abgleichen.

## 1. Kopf

Zentriert (`<div align="center">`): App-Icon
(`dashboard/public/stockinfo-icon.png`, 96 × 96), Name als Überschrift, fette
Zeile mit dem Zweck (Kurse per REST-API, Cache in SQLite), Sprachzeile
„English · Deutsch“, in der die jeweils andere Sprache auf ihre Datei
verlinkt. Danach `</div>`.

## 2. Überblick

Zwei bis drei kurze Absätze: was StockInfo liefert (Abfrage per ISIN oder
Symbol und Börse, JSON mit Preis, Währung, Zeitpunkt, Name und ETF-Kennzahlen)
und dass ein Dashboard dazugehört. Links auf das Docker-Image, `CHANGELOG.md`
und `docs/release-notes.md`. Darunter der Screenshot
`unraid/screenshots/dashboard.png`.

## 3. Schwester-App StockPortfolio

Dass StockInfo allein läuft und StockPortfolio eine optionale Ergänzung ist,
die ihre Kurse von StockInfo bezieht. Vergleichstabelle (Zweck, läuft ohne die
andere App, Docker-Image). Link auf StockPortfolios Einrichtungsanleitung.
Quelle: StockPortfolios README.

## 4. Release-Highlight

Die wichtigsten Punkte des neuesten Release als kurze Liste. Quelle:
`CHANGELOG.md` und die `feat`/`fix`-Commits seit dem vorherigen Tag. Beim
nächsten Release ersetzen, nicht anhängen.

## 5. Inhalt und Funktionen

Inhaltsverzeichnis mit Links auf alle folgenden Abschnitte, dann die
Feature-Liste: je Eintrag fetter Name und kurze Beschreibung. Beim Eintrag zu
manuellen Werten der Screenshot `unraid/screenshots/detail-area.png`.

## 6. Wie Kurse abgerufen werden

Tabelle der Standardquellen und wofür sie dienen, Hinweis auf
`sources.yaml`, `docs/plugins.md` und `docs/plugin-authors.md`. Pflicht:
„keine offiziellen APIs“ samt Verantwortung des Betreibers, die Lücke bei
ETFs außerhalb Europas und der Hinweis zu Währung und Börse. Quellen:
`app/providers/`, `docs/plugins.md`, `docs/rest-core-contract.md`.

## 7. Voraussetzungen und Schnellstart

Python- und Node-Version aus `Makefile` (`PYTHON_BOOTSTRAP`) und
`dashboard/package.json`, dann die Schritte vom Klonen bis zum laufenden
Backend und Dashboard. Adressen aus `make hints`.

## 8. Sicherheitsmodell

Für wen StockInfo gedacht ist (Heimnetz, keine Anmeldung), was ein Angreifer
im Netz tun könnte und was der Betreiber dagegen tut. Ein
GitHub-Hinweis (`> [!WARNING]`) gegen den Betrieb im offenen Internet.
Quelle: bisheriger Abschnitt „Security model“ und `docker/README.md`.

## 9. REST-API und Konfiguration

Die wichtigsten Endpunkte mit je einem `curl`-Beispiel, Verweis auf Swagger
(`/docs`) und `docs/rest-core-contract.md`. Danach die Einstellungen aus
`.env.example` als Tabelle; Quelle der Namen und Standardwerte ist die
Settings-Klasse in `app/config.py`.

## 10. Dashboard, Docker und Unraid

Dashboard: Reiter und was sie zeigen. Docker: Bauen, Starten, Daten-Volume,
Veröffentlichen samt Docker-Hub-Beschreibung; Details in `docker/README.md`.
Unraid: ein Satz und der Link auf `unraid/README.md`.

## 11. Tests

Welche Make-Targets welche Teile prüfen, inklusive `make docs-check`, und was
die Online-Tests (`integration`) von `make check` unterscheidet.

## 12. Releases und Changelog

Wie ein Release entsteht (`make tag-patch`, `make tag-minor`,
`make tag-major`, `make changelog`) und wo die Änderungen stehen.

## 13. Projektstruktur

Kurzer Verzeichnisbaum der Teilprojekte (`app/`, `dashboard/`,
`plugin_api/`, `contract/`, `docker/`, `unraid/`, `docs/`, `scripts/`,
`tests/`) mit je einer Zeile.

## 14. Support

Für den Eigengebrauch gebaut und frei geteilt; Issues und Pull Requests
werden gelesen, ohne Zusage auf Antwort, Fix oder neue Funktion. Link auf die
Issues.

## 15. Lizenz

Rechteinhaber und Lizenzgeber, Lizenz (EUPL 1.2, nur diese Version), was sie
erlaubt und verlangt, Verweis auf die Verbrauchererklärung, MIT für
`plugin_api/`. Quelle: `LICENSE`, `LICENSE.de.txt` und `LICENSING.md`; jede
davon verlinken, keinen Lizenztext einfügen.
