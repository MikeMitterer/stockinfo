# T-79 · EUPL-Lizenz für StockInfo

Mike beauftragt am 2026-09-27 die Umstellung wie in StockPortfolio T-57,
einschließlich Docker und weiterer Auslieferungswege. Codex implementiert,
Claude prüft unabhängig. Stand: technisch umgesetzt und selbst geprüft;
Runde 1 zur unabhängigen Prüfung vorbereitet, keine Freigabe behauptet.

## Scope-Vertrag

Ergebnis: StockInfo wird unter EUPL 1.2 only angeboten und ausgeliefert.

1. Offizielle EN/DE-Texte und LICENSING.md nach StockPortfolio T-57;
   kommerzielle Zusatzlizenz entfernen, eigenständige MIT-Pakete erhalten.
2. Python/npm-Metadaten, Docker-Label und vorhandene Lizenzprüfung umstellen;
   neue Lizenzdokumente ins Image aufnehmen. Unraid-XML im Template-Repo abgleichen.
3. Root-, Docker- und Unraid-Anleitung konsistent halten; historische
   Release-Notizen mit damaligem Lizenzstand eindeutig kennzeichnen.

Erwartet: 5 Build-/Metadatendateien, bis zu 8 Lizenz-/Dokudateien,
1 externe XML-Datei, Boarddateien. Keine neue Testdatei erforderlich;
vorhandene Docker-Tests, echter amd64-Build, Image-Hashes, Hub-Vorschau.
Budget: 400 handgeschriebene Diff-Zeilen plus der ausdrücklich beauftragte
vollständige Austausch offizieller Lizenztexte (ca. 1.200 Diff-Zeilen).
Keine neue App-Funktion, kein Versionssprung, kein Image-/Hub-Push.
StockPortfolio bleibt unverändert. Quellcodezugang über das bestehende
GitHub-Repository und den im Image-Tag identifizierten Quellcommit.

## Prüfschritte

- [x] Lizenztexte bytegleich zu den EU-Originalen, Metadaten konsistent.
- [x] Docker-Build und tatsächliche Dokumente/Labels im Image geprüft.
- [x] Bestehende betroffene Tests und Shell-Prüfungen erfolgreich.
- [x] Doku-Abgleich und echte Docker-Hub-Vorschau geprüft.
- [x] Lokales Unraid-Template angepasst und XML geprüft.

## Offene persönliche Wiedervorlagen

Wie StockPortfolio T-57: Die interne Rechtevereinbarung zwischen Michael
Mitterer (Urheber) und MangoLila GmbH (Anbieterin/Lizenzgeberin) sowie die
österreichische Rechtsprüfung sind nicht als abgeschlossen nachgewiesen.
Die dort beschlossene Verbraucherklärung wird separat übernommen;
die offiziellen Lizenztexte bleiben unverändert.

## Lessons

Inventar aller lokalen Lessons; Codex-Fassungen SI-CX-01, SI-R-02, SI-T-66
und gemeinsame AL-R-02/AL-R-12 gelesen. Frische temporäre Containerdaten,
vollständiges Lizenz-/Dokumentinventar und eigene Artefaktprüfung vorgesehen.

## Umsetzung und Nachweise · 2026-09-27

Produktcommit `4ca54cf85fc1e671b07f5bb3e35ed88b93a56ba3`, Branch
`t-79-eupl-license`. Separates Template-Repository: `2b77de7`, Branch
`t-79-stockinfo-eupl`; nur `templates/stockinfo.xml`, AGPL → EUPL-1.2.
Beide Arbeitsbäume vor dem Nachweis-/Übergabenachtrag sauber.

- EU-Originale frisch heruntergeladen und bytegleich geprüft:
  [EN](https://interoperable-europe.ec.europa.eu/sites/default/files/custom-page/attachment/2020-03/EUPL-1.2%20EN.txt),
  [DE](https://interoperable-europe.ec.europa.eu/sites/default/files/inline-files/EUPL%20v1_2%20DE.txt).
  SHA-256 EN `6fc9e709ccbfe0d77fbffa2427a983282be2eb88e47b1cdb49f21a83b4d1e665`,
  DE `208705beb6df6c418b821f73b2cf192d9d5c6837a1a59391a261c7abe2fb0dce`.
- `docker build --platform linux/amd64 -f docker/Dockerfile -t stockinfo-t79-eupl:local .`
  erfolgreich, einschließlich `npm ci`, `vue-tsc` und Vite-Produktionsbuild.
  Anschließend `make build` auf sauberem Produktcommit erfolgreich:
  `mangolila/stockinfo:1.1.0-260927.1948.4ca54.ahead37`, Image-ID
  `sha256:60c7db176b41e07bcb1e05a8414a8c3203f2c148de54bfbd2a1bf5c731028988`.
  Der echte Build-Helfer bestätigt Architektur amd64, Quell-/Lizenzlabels
  und alle fünf Dokumenthashes. Nach weiteren Boardcommits ist vor einem
  späteren Push ein neuer `make build` gemäß bestehendem Commit-Riegel nötig.
- Zusätzlich Image-Hashes selbst gegen den Arbeitsstand verglichen:
  LICENSE, LICENSE.de.txt, LICENSING.md und beide unveränderten MIT-Texte.
  OCI-Lizenzlabel `EUPL-1.2`, Source-Label GitHub/stockinfo.
  `/app/COMMERCIAL-LICENSE.md` fehlt nach direkter Prüfung im Image.
- `.venv/bin/python -m pytest -q tests/test_dockerhub_readme.py`: **7 passed**.
  Erster Sandboxlauf: 6 passed, frischer Dependency-Download gesperrt;
  Wiederholung mit Netzwerkfreigabe vollständig erfolgreich.
- `bash -n docker/build.sh` und Diff-Whitespace-Prüfung außerhalb der
  unveränderten Original-Lizenztexte erfolgreich. ShellCheck meldet dieselben
  neun Hinweise (SC2034/SC2155/SC1091) wie die Fassung auf master, per JSON
  nach Code und Meldung verglichen; kein neuer Hinweis, kein grüner Gesamtlint
  behauptet. Vollständiges Inventar der Bash-Zuweisungen, lokalen Variablen
  und Funktionsköpfe: englische Bezeichner.
- Lokale Markdown-Dateilinks und Abschnittsanker aller fünf geänderten
  Anleitungen/Erklärungen geprüft. npm-Paket und Lock-Root beide EUPL-1.2.
- `./.libs/ProjectTools/src/bash/dockerhub-readme.sh --preview` erfolgreich,
  `docker/preview/README.md`: **6.983 UTF-8-Bytes**, absolute Lizenz-/Doku-Links.
- Zentrales Unraid-XML geparst und Lizenzfeld geprüft. Keine Port-, Mount-,
  Variablen- oder Image-Referenzänderung; kein Live-Unraid-Test erforderlich
  für das einzelne Metadatenfeld. Kein Git-/Image-Push oder Hub-Upload.

Vorhandene Buildmeldungen: sechs npm-Audit-Funde (3 moderate, 2 high,
1 critical) im unveränderten Abhängigkeitsbestand und Vite-Chunk über 500 kB.
Kein Dependency-Audit oder Fix im Lizenzauftrag behauptet. Kein App-Verhalten
geändert; deshalb keine vollständige Backend-/Dashboard-Suite oder Browser-
Abnahme. Die einmaligen Hash-Prüfcontainer starteten keine App und berührten
keine Arbeitsdatenbank.

## Doku-Abgleich

Dateiinventar aller Markdown-/Lizenz-/Paket-/Docker-Dateien und Überschriften
der Anleitungen erstellt, Lizenzzusagen gezielt verfolgt.

- README.md / Docker und License: EUPL, fünf ausgelieferte Dokumente,
  Rechte-/Anbieterangaben und eigenständige MIT-Pakete.
- docker/README.md / Support and license: gleiche Lizenzzusagen, tatsächliche
  Imagepfade und Quellcommit-Zugang; Containerbenutzung bleibt dort.
- unraid/README.md / License: gleiche App-Lizenz, eigenständiges Template-Repo
  getrennt. Das zentrale XML wurde tatsächlich angepasst, nicht nur erwähnt.
- LICENSING.md: Rechteaufteilung und Verbraucherklärung aus StockPortfolio
  T-57, Quellzugang und Buildanleitung passend zu StockInfo. Keine Behauptung,
  StockInfo habe StockPortfolios HTTP-Downloads oder Quellarchiv übernommen.
- docs/release-notes.md: damalige AGPL-Entscheidung als Historie erhalten;
  irreführenden Link von AGPL auf die heutige EUPL-Datei korrigiert.
- Plugin-Anleitung, REST-Referenz, Contract-README und historische Specs
  benötigen keine Änderung: kein API-/Pluginvertrag oder Nutzungsweg geändert,
  keine abweichende aktuelle Lizenzzusage. Beide MIT-Lizenzdateien bytegleich.
- Aktuelle Produktdateien enthalten keinen COMMERCIAL-LICENSE-Verweis oder
  AGPL-Lizenzanspruch mehr. AGPL im EUPL-Kompatibilitätsanhang und historische
  Ticket-/Release-Angaben sind keine aktuelle Projektlizenz und bleiben erhalten.

## Umfang und Standards

Geplant/tatsächlich: drei fachliche Änderungen; 5/5 Build-/Metadatendateien,
8/8 Lizenz-/Dokudateien (einschließlich Löschung); 1/1 externe XML-Datei.
Produktdiff 1.255 Zeilen, davon 1.049 rein offizielle Lizenztexte und
206 übrige Zeilen. Innerhalb des vorher benannten Budgets; keine neue Schicht.

Gelesen: `/Users/macminipro/.codex/skills/code-standards/SKILL.md`,
Referenzen `shell.md`, `documentation.md`; Docker-, Docker-Build-, Unraid-
und Git-Konventionen. `requesting-code-review` wird über die verbindlich
zugeordnete Instanz Claude und STATUS.md umgesetzt, kein Ersatzprüfer erfunden.

| Gruppe | Ergebnis |
|---|---|
| Architektur | ✅ bestehende Auslieferungs-/Prüfwege, keine neue Abstraktion |
| Shell | ✅ bash -n, Inventar, echter make-build; ShellCheck nur belegte Altbefunde |
| CLI | ➖ keine neue Option oder Schnittstelle |
| Frontend | ✅ nur npm-Lizenzmetadaten, npm ci und Produktionsbuild erfolgreich |
| Python | ✅ nur Lizenzmetadatum; kein Python-Code geändert |
| Persistenz | ➖ nicht berührt |
| Qualität | ✅ 7 vorhandene Tests, Original-/Image-Hashes, echter Build |
| Dokumentation | ✅ inhaltlicher Abgleich, lokale Links/Anker und Hub-Vorschau |
