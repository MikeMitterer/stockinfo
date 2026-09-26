# T-77 · README lokal nach Docker Hub übertragen

Beim Kopieren des README nach Docker Hub brechen relative Bild- und
Dokumentlinks. Ein lokales Script soll sie beim Veröffentlichen automatisch
auf GitHub beziehen. Zugangsdaten werden lokal gelesen und ausschließlich an Docker Hub gesendet;
sie erscheinen nicht in Ausgaben oder Prozessargumenten.

**Auftrag:** Mike ersetzt die diskutierte GitHub-Automatisierung durch ein
lokales Script nach Skill-Konventionen. Präzisierung: keine eigenen Targets;
der erfolgreiche bestehende Docker-Hub-Push ruft das Script auf.
**Stand:** Implementiert und lokal geprüft; unabhängiger Review steht aus.
Keine GitHub Action angelegt und kein echter Image-/README-Upload ausgeführt.

## Übersicht

- [Umfang](#umfang)
- [Prüfung](#prüfung)
- [Übernahme in StockPortfolio und weitere Projekte](#übernahme-in-stockportfolio-und-weitere-projekte)
- [Doku und Lessons](#doku-und-lessons)

## Umfang

`--preview` erzeugt eine lokale Markdown-Vorschau ohne Docker-Hub-Zugriff.
Der Bash-Einstieg kann beim Erststart fehlende Python-Pakete herunterladen.
`--publish` überträgt sie mit einem lokalen Token an Docker Hub; der bestehende
`make push` ruft diese Aktion nach erfolgreichem Docker-Hub-Push auf.
Das Original-README bleibt unverändert. Pandoc liest
Markdown strukturiert; nur Link- und Bildziele werden umgeschrieben.
Der API-Aufruf aktualisiert die Übersicht, eine explizite Kurzbeschreibung
ist optional. Ohne Aktion zeigt das Script Hilfe.

Scope-Vertrag: Linkkonvertierung, lokaler Upload und Make-/Doku-Anbindung.
Auf Mikes Erweiterung: Script, gettext-Katalog und allgemeine Tests in
ProjectTools; StockInfo erhält den Push-Aufruf, Integrationstests, README,
ausgelagerte Release-Notizen und die Größenregel in AGENTS.md.
Keine App-, Datenbank- oder GitHub-Secrets-Änderung. Auf weiteren Auftrag
Hinweis im Makefile-Skill und wiederverwendbare Erkenntnisse in diesem Ticket.
Erweiterter Scope: zwei Repositories plus Skill, Bash-Einstieg, Paketdatei, zusätzliche Bootstrap-Tests und code-standards-Skill
zusätzlich zum Ausgangsumfang; Gesamtbudget einschließlich Board: 2.000 Diff-Zeilen. Der bisherige
Image-Push bleibt erhalten; andere Registries lösen keinen Hub-Upload aus.
Vorschau und API-Fehler werden gezielt geprüft.

[↑ Übersicht](#übersicht)

## Prüfung

| # | Nachweis | Ergebnis |
|---|---|---|
| 1 | Echte Pandoc-Konvertierung: Bilder, Dokumente, Anker, Code und Referenzlinks | Bestanden |
| 2 | HTTP-Grenze: Authentifizierung, PATCH, Fehler ohne Secret-Ausgabe | Bestanden |
| 3 | CLI, Make-Aufrufe, Namensinventar, Ruff und Doku-Abgleich | Bestanden |
| 4 | Vorschau des echten README; tatsächlicher Hub-Upload getrennt ausweisen | Vorschau: 24.980 Bytes; echter Upload nicht ausgeführt |

[↑ Übersicht](#übersicht)

## Übernahme in StockPortfolio und weitere Projekte

Die Implementierung liegt ausschließlich in **ProjectTools**:
`src/bash/dockerhub-readme.sh` kapselt die Einrichtung und startet
`src/python/dockerhub-readme.py`; deutsche Texte liegen unter
`src/python/locales/de/LC_MESSAGES/`, allgemeine Tests in
`tests/python/test_dockerhub_readme.py`. Der `.libs/ProjectTools`-Link des
Verbrauchers zeigt darauf. Keine Scriptkopie im Verbraucherprojekt anlegen.

### Voraussetzungen und Aufruf

Python 3.11+ und Pandoc bereitstellen. Der Bash-Einstieg legt eine eigene Werkzeug-`.venv`
im Benutzer-Cache bei Bedarf an, ergänzt fehlendes pip über ensurepip und installiert die
Paketliste `src/python/dockerhub-readme.requirements.txt`. Eine vorhandene
passende Umgebung wird ohne erneute Installation verwendet.
`PYTHON_BOOTSTRAP` wählt bei Bedarf den Python-Interpreter (Vorgabe `python3`).
Das Script braucht keine StockInfo-Konfiguration. Beispiel aus einem
beliebigen Verbraucherprojekt; Namespace, Repository und Branch ersetzen:

```bash
./.libs/ProjectTools/src/bash/dockerhub-readme.sh \
  --preview --ref main --output /tmp/dockerhub-readme.md
./.libs/ProjectTools/src/bash/dockerhub-readme.sh \
  --publish --ref main --repository namespace/project
```

| Parameter | Bedeutung |
|---|---|
| `--project-dir` / `-C` | Projektwurzel; Vorgabe ist das Arbeitsverzeichnis, nicht der Scriptort |
| `--readme` / `-s` | Quelldatei relativ zur Projektwurzel; Vorgabe `README.md` |
| `--github-repository` / `-g` | GitHub `owner/repository`; sonst aus dem `origin` des Verbrauchers |
| `--ref` / `-b` | Erforderlicher, bereits veröffentlichter GitHub-Branch oder Commit |
| `--repository` / `-r` | Docker-Hub-Repository; beim Upload erforderlich |
| `--username` / `-u` | Login-Benutzer, falls abweichend vom Docker-Hub-Namespace |
| `--token-file` / `-t` | Lokale Token-Datei; Vorgabe siehe unten |
| `--description` / `-d` | Optionale Kurzbeschreibung; sonst bleibt sie unverändert |
| `--output` / `-o` | Vorschauziel, relativ zum Projekt; Vorgabe `README.dockerhub.md` |

Keine Argumente zeigen Hilfe ohne Installation. Die Vorschau braucht keinen
Token; nur die erstmalige Paketinstallation kann Netz benötigen.
Sie schreibt eine neue Datei; das Quell-README wird nicht verändert.

### Linkumwandlung und Größenlimit

Pandoc verarbeitet Markdown strukturiert: relative Bilder werden Raw-GitHub-URLs,
Dokumentlinks GitHub-Datei-URLs. Referenzlinks und Unterverzeichnisse funktionieren;
Code, externe URLs und lokale Anker bleiben inhaltlich erhalten. Markdown wird
neu formatiert. Raw-HTML-Links werden nicht umgeschrieben; dort absolute URLs
verwenden. Der gewählte GitHub-Stand muss die verlinkten Dateien schon enthalten.

Docker Hub erlaubt **25.000 UTF-8-Bytes für die konvertierte Übersicht**, nicht
25.000 Zeichen und nicht die Größe der Quelldatei. Längere absolute URLs zählen
mit. Bereits `--preview` prüft diese Grenze. Die Fehlermeldung fordert dazu auf,
die Grenze in `AGENTS.md` des Verbrauchers festzuhalten; nichts wird abgeschnitten.
StockInfos Größenregel steht dort. Ältere Versionshinweise wurden in
`docs/release-notes.md` ausgelagert, damit das aktuelle README vollständig passt.
Die Vorschau deshalb bei künftigen README-Änderungen erneut ausführen.

### Upload und Push-Integration

Ein Image-Push synchronisiert Docker-Hub-Metadaten nicht automatisch. Das Script
holt über `/v2/auth/token` ein Zugriffstoken, aktualisiert `full_description` per
PATCH und liest das Ergebnis per GET zur Kontrolle zurück. Es setzt die
Kurzbeschreibung nur bei ausdrücklichem `--description`.

Token-Vorgabe: `DOCKER_PW_FILE`, sonst
`${DOCKER_CONFIG:-$HOME/.docker}/dockerhub.sec`. Personal Access Token mit
Berechtigung zum Ändern der Beschreibung (Read, Write, Delete) verwenden.
Token außerhalb des Repositorys aufbewahren. Es werden nur Dateipfade übergeben;
Token und HTTP-Antwortkörper erscheinen nicht in Ausgaben oder Prozessargumenten.
Keine GitHub-Secrets und keine GitHub Action erforderlich.

Den Aufruf **einmal im vorhandenen Push-Ablauf**, nach erfolgreichem Image-Push,
nur für Docker Hub einbauen. StockInfo erledigt das in `docker/build.sh`;
Make exportiert `PROJECT_TOOLS`. Kein weiteres Make-Target. Bei anderem
Arbeitsverzeichnis `--project-dir` explizit setzen. Andere Registries überspringen
README-Uploads. `DOCKER_README_AFTER_PUSH=1` ergänzt im Fehlerfall den Hinweis,
dass das Image bereits veröffentlicht wurde. Der Aufrufer übernimmt den Fehlercode;
nur `--publish` separat zu wiederholen genügt, kein neuer Image-Push erforderlich.

### Prüfnachweise und Grenzen

- ProjectTools: **23 Tests bestanden**, einschließlich zweier verschiedener
  Verbraucher, README im Unterordner und CLI-Fehler mit AGENTS.md-Hinweis.
- StockInfo: **7 Integrationstests bestanden**. Echtes Buildscript, äußere
  Git-/Docker-/Upload-Prozesse kontrolliert ersetzt; Erfolg, fehlgeschlagener
  Image-Push, fehlgeschlagener README-Upload, GHCR und ECR geprüft.
- Echte Pandoc-Konvertierung; HTTP-Ablauf mit `httpx.MockTransport` geprüft.
  Kein echter Docker-Hub-Schreibzugriff und keine tatsächlichen Tokens gelesen.
- Ruff Check/Format, Bash-Syntax, `make -n push`, deutsche Vorschau und
  `git diff --check` bestanden. AST-Inventar: 84 Script-, 32 HTTP-/Markdown-Test-,
  34 Bootstrap-Test- und 31 Integrationstest-Bezeichner; Bash-Zuweisungen/Funktionsköpfe inventarisiert.
  Fachliche Bezeichner englisch, erklärende Testnamen deutsch.

```bash
.venv/bin/python -m pytest -q tests/test_dockerhub_readme.py
.venv/bin/python -m pytest -q .libs/ProjectTools/tests/python/
```

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
unterscheiden. Der ausdrücklich beauftragte Hinweis steht im Makefile-Skill, Abschnitt
„Docker-Hub-README nach erfolgreichem Push“. Keine Board-Migration.

[↑ Übersicht](#übersicht)


**Doku-Abgleich:** README/Docker (Aufruf, Voraussetzungen, Token, Fehlerfall),
README/Einleitung und `docs/release-notes.md` (ältere Hinweise ausgelagert),
`AGENTS.md` (Größenregel), ProjectTools-README (Optionen und Grenzen),
Makefile-Skill (gemeinsamen Helfer verwenden) auf den implementierten Ablauf
abgeglichen. `docs/plugins.md` verweist weiterhin korrekt auf README/Docker;
REST-/Plugin-Verträge bleiben unverändert.

**Zurückgenommener erster Prüfstand:** ProjectTools `3c4e025`, Basis `ff45053`, Branch
`t-77-dockerhub-readme`. Dort war `AGENTS.md` bereits vor Arbeitsbeginn
unversioniert; unverändert gelassen und nicht mitcommittet.
Der lokale Makefile-Skill liegt außerhalb eines Git-Repositorys; SHA-256:
`b664731f9482a639aa235bd5ec7fe63c8dcc1323f7fb9ac5ae0dc5cc3687db5b`.
Skill-Validator: gültig. 27 lokale Dateiverweise in README, Release-Notizen,
AGENTS.md und diesem Ticket geprüft.


### Ergänzung: Bash-Einstieg und Vorprüfungen

Mike hat nach dem fehlgeschlagenen Python-Direktaufruf einen gekapselten
Bash-Einstieg beauftragt. StockInfo-Push, README, AGENTS.md und Makefile-Skill
verwenden jetzt `src/bash/dockerhub-readme.sh`. Die öffentliche Optionsliste
bleibt im Python-Parser; Bash reicht alle Argumente unverändert weiter.

Vor der Einrichtung werden Projektverzeichnis und lesbares UTF-8-README geprüft.
Bei `--publish` muss außerdem die Token-Datei lesbar und nach Entfernen von
Leerraum nicht leer sein. Fehler stoppen vor venv/pip/Upload. Die tatsächliche
Gültigkeit und Schreibberechtigung prüft Docker Hub beim Auth-/PATCH-Aufruf;
eine vorhandene Datei allein bestätigt keine gültigen Credentials.

Bash prüft Pandoc, legt eine eigene Cache-`.venv` an und installiert darin
`httpx` gemäß gemeinsamer Paketliste. Es installiert nichts global und löscht
keine vorhandene Umgebung. Nicht funktionsfähige/zu alte Werkzeug-venvs werden gemeldet.
Hilfe sowie ungültige Optionen verändern keine Umgebung. Auch die Python-Hilfe
funktioniert ohne httpx; direkte Aktionen mit fehlendem Paket verweisen auf Bash.

Der Erstlauf wurde mit echten leeren venvs und echten pip-Installationen geprüft.
Die Testpakete wurden einmal nach `/tmp` geladen; die Installationstests laufen
mit `PIP_NO_INDEX=1` und `PIP_FIND_LINKS` auf diese Wheels. Damit wird weder eine
bereits eingerichtete Umgebung als Erstlauf ausgegeben noch Docker Hub beschrieben.
Die Rücknahme der ersten, ungeclaimten Übergabe steht in STATUS.md; die nächste
Übergabe benennt die ergänzten Prüfcommits bei unverändertem Rundenverbrauch.


### Eigene Werkzeugumgebung (Mikes Präzisierung)

Die Projekt-`.venv` wird weder verwendet noch verändert. Der Bash-Einstieg
verwaltet ausschließlich
`${XDG_CACHE_HOME:-$HOME/.cache}/projecttools/dockerhub-readme/.venv`.
Ein Symlink an diesem Werkzeugverzeichnis oder direkt an dessen `.venv`
wird abgewiesen. Unterschiedliche Projekte nutzen denselben Werkzeugcache;
Projektwurzel, README und Repository werden unabhängig davon ausgewählt.

Bei neuem Runtime-Setup wählt der Einstieg einen verfügbaren Python-Interpreter
ab 3.11; auf diesem Mac ist `python3` noch 3.9, `python3.14` wird gefunden.
`PYTHON_BOOTSTRAP` überschreibt die Auswahl explizit. Eine defekte/zu alte
Werkzeugumgebung wird mit Fehler gemeldet, nicht blind gelöscht.

Die Isolation ist im Test belegt: Eine bestehende Projekt-`.venv/bin/python`
endet absichtlich mit Exit 42. Vorschau und Paketinstallation funktionieren
trotzdem; anschließend sind Inhalt und Dateiinventar der Projektumgebung
unverändert. Zusätzlich wird ein Symlink auf eine fremde venv abgewiesen.

Grundsatz auf Mikes Auftrag im `code-standards`-Skill samt Python-Referenz:
öffentlicher Bash-Einstieg, Hilfe ohne Installation, lokale Vorprüfungen,
werkzeugeigene venv für geteilte Helfer, Requirements-Datei als Paketquelle,
echte Erstlauf-/Wiederverwendungs-/Fehlertests. Der Makefile-Skill verweist
auf den gemeinsamen Bash-Einstieg. Die alten Commit-/Hash-Angaben oben sind
die zurückgenommene Erstübergabe; aktuelle Prüffassung steht in STATUS.md.


**Aktuelle Prüfung nach Bash-/Isolationsauftrag:** 23 ProjectTools-Tests und
7 StockInfo-Integrationstests bestanden. ShellCheck für den neuen Bash-Einstieg,
Bash-Syntax, Ruff Check/Format und beide Skill-Validatoren bestanden.
Aktuelles konvertiertes README: 24.980 UTF-8-Bytes. Test-Installationen erfolgten
in temporären Werkzeugcaches aus lokalen Wheels; keine globale Installation
und keine Änderung der StockInfo-`.venv`. Die Befunde zum Python-Direktaufruf
und zu fehlenden Eingaben sind durch CLI-Tests abgedeckt. Kein Live-Upload.
Doku-Abgleich schließt jetzt ausdrücklich auch die isolierte Werkzeugumgebung
und die prinzipielle Vorgehensweise im code-standards-Skill ein.

Aktueller ProjectTools-Prüfstand: `3005e11` (Vorgänger `3c4e025`).

Aktuelle Skill-Prüfstände (SHA-256, lokale Dateien außerhalb von Git):
- `makefile-conventions/SKILL.md`: `d9e6ee6615e28ae5336a71a1810b305a4bc90e6ed7ed4e1a8d96ee1d6bd10c66`
- `code-standards/SKILL.md`: `93b2b62cbacc9ac73f0188afd8fb97146bed4a90db54e9bc0f3d96bc5776c7c6`
- `code-standards/references/python.md`: `97829547aefe04bc9e379dffb6b853a912a90e57a80fcd5d44184ae5397d5b53`
