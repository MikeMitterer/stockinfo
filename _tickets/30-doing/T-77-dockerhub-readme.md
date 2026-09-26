# T-77 · README lokal nach Docker Hub übertragen

Beim Kopieren des README nach Docker Hub brechen relative Bild- und
Dokumentlinks. Ein lokales Script soll sie beim Veröffentlichen automatisch
auf GitHub beziehen. Zugangsdaten bleiben lokal und erscheinen nicht in
Ausgaben oder Prozessargumenten.

**Auftrag:** Mike ersetzt die diskutierte GitHub-Automatisierung durch ein
lokales Script nach Skill-Konventionen mit Makefile-Target.
**Stand:** Umsetzung durch Codex; keine GitHub Action angelegt.

## Übersicht

- [Umfang](#umfang)
- [Prüfung](#prüfung)
- [Doku und Lessons](#doku-und-lessons)

## Umfang

`make dockerhub-readme-preview` erzeugt eine lokale Markdown-Vorschau ohne
Token oder Netz. `make dockerhub-readme` überträgt sie mit einem lokalen
Token an Docker Hub. Das Original-README bleibt unverändert. Pandoc liest
Markdown strukturiert; nur Link- und Bildziele werden umgeschrieben.
Der API-Aufruf aktualisiert die Übersicht, eine explizite Kurzbeschreibung
ist optional. Ohne Aktion zeigt das Script Hilfe.

Scope-Vertrag: Linkkonvertierung, lokaler Upload und Make-/Doku-Anbindung.
Ein Python-Script samt gettext-Katalog, eine Testdatei, Makefile und README;
keine App-, Datenbank- oder GitHub-Secrets-Änderung. Budget: höchstens sieben
Produkt-/Test-/Dokudateien plus Board und 800 Diff-Zeilen. Docker-Images und
Tags werden nicht verändert. Vorschau und API-Fehler werden gezielt geprüft.

[↑ Übersicht](#übersicht)

## Prüfung

| # | Nachweis | Ergebnis |
|---|---|---|
| 1 | Echte Pandoc-Konvertierung: Bilder, Dokumente, Anker, Code und Referenzlinks | Offen |
| 2 | HTTP-Grenze: Authentifizierung, PATCH, Fehler ohne Secret-Ausgabe | Offen |
| 3 | CLI, Make-Aufrufe, Namensinventar, Ruff und Doku-Abgleich | Offen |
| 4 | Vorschau des echten README; tatsächlicher Hub-Upload getrennt ausweisen | Offen |

[↑ Übersicht](#übersicht)

## Doku und Lessons

README/Docker beschreibt den lokalen Ablauf, Voraussetzungen und Token-Datei.
Keine GitHub-Action einrichten. Vorhandene Helfer in BashLib und ProjectTools
auf Beschreibungssynchronisierung geprüft: kein entsprechender Helfer.
Der bestehende Image-Push verwendet `DOCKER_PW_FILE`; denselben Dateiort
übernimmt der neue Upload. Pandoc ist lokal bereits installiert.

Lokale Codex-Lessons SI-CX-01, SI-R-02, SI-T-66 und gemeinsame Regel AL-R-02
(Fassung 2026-09-11) berücksichtigt: echte Konvertierung prüfen, nur den
betroffenen Ablauf bauen und Vorschau von tatsächlicher Veröffentlichung
unterscheiden. Keine neuen globalen Regeln oder Board-Migration beauftragt.

[↑ Übersicht](#übersicht)
