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

`--preview` erzeugt eine lokale Markdown-Vorschau ohne Token oder Netz.
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
Erweiterter Scope: zwei Repositories plus Skill, höchstens zwölf Produkt-/Test-/
Dokudateien plus Board und 1.200 Diff-Zeilen. Der bisherige
Image-Push bleibt erhalten; andere Registries lösen keinen Hub-Upload aus.
Vorschau und API-Fehler werden gezielt geprüft.

[↑ Übersicht](#übersicht)

## Prüfung

| # | Nachweis | Ergebnis |
|---|---|---|
| 1 | Echte Pandoc-Konvertierung: Bilder, Dokumente, Anker, Code und Referenzlinks | Bestanden |
| 2 | HTTP-Grenze: Authentifizierung, PATCH, Fehler ohne Secret-Ausgabe | Bestanden |
| 3 | CLI, Make-Aufrufe, Namensinventar, Ruff und Doku-Abgleich | Bestanden |
| 4 | Vorschau des echten README; tatsächlicher Hub-Upload getrennt ausweisen | Vorschau: 24.945 Bytes; echter Upload nicht ausgeführt |

[↑ Übersicht](#übersicht)

## Übernahme in StockPortfolio und weitere Projekte

Die Implementierung liegt ausschließlich in **ProjectTools**:
`src/python/dockerhub-readme.py`, deutsche Texte daneben unter
`src/python/locales/de/LC_MESSAGES/`, allgemeine Tests in
`tests/python/test_dockerhub_readme.py`. Der `.libs/ProjectTools`-Link des
Verbrauchers zeigt darauf. Keine Scriptkopie im Verbraucherprojekt anlegen.

### Voraussetzungen und Aufruf

Python 3.11+ aus der Projekt-`.venv`, `httpx` und Pandoc bereitstellen.
Das Script braucht keine StockInfo-Konfiguration. Beispiel aus einem
beliebigen Verbraucherprojekt; Namespace, Repository und Branch ersetzen:

```bash
.venv/bin/python .libs/ProjectTools/src/python/dockerhub-readme.py \
  --preview --ref main --output /tmp/dockerhub-readme.md
.venv/bin/python .libs/ProjectTools/src/python/dockerhub-readme.py \
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

Keine Argumente zeigen Hilfe. Die Vorschau braucht weder Token noch Netzwerk.
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

- ProjectTools: **10 Tests bestanden**, einschließlich zweier verschiedener
  Verbraucher, README im Unterordner und CLI-Fehler mit AGENTS.md-Hinweis.
- StockInfo: **7 Integrationstests bestanden**. Echtes Buildscript, äußere
  Git-/Docker-/Upload-Prozesse kontrolliert ersetzt; Erfolg, fehlgeschlagener
  Image-Push, fehlgeschlagener README-Upload, GHCR und ECR geprüft.
- Echte Pandoc-Konvertierung; HTTP-Ablauf mit `httpx.MockTransport` geprüft.
  Kein echter Docker-Hub-Schreibzugriff und keine tatsächlichen Tokens gelesen.
- Ruff Check/Format, Bash-Syntax, `make -n push`, deutsche Vorschau und
  `git diff --check` bestanden. AST-Inventar: 78 Script-, 32 Shared-Test-
  und 32 Integrationstest-Bezeichner; Bash-Zuweisungen/Funktionsköpfe inventarisiert.
  Fachliche Bezeichner englisch, erklärende Testnamen deutsch.

```bash
.venv/bin/python -m pytest -q tests/test_dockerhub_readme.py
.venv/bin/python -m pytest -q .libs/ProjectTools/tests/python/test_dockerhub_readme.py
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

**Gemeinsamer Prüfstand:** ProjectTools `3c4e025`, Basis `ff45053`, Branch
`t-77-dockerhub-readme`. Dort war `AGENTS.md` bereits vor Arbeitsbeginn
unversioniert; unverändert gelassen und nicht mitcommittet.
Der lokale Makefile-Skill liegt außerhalb eines Git-Repositorys; SHA-256:
`b664731f9482a639aa235bd5ec7fe63c8dcc1323f7fb9ac5ae0dc5cc3687db5b`.
Skill-Validator: gültig. 27 lokale Dateiverweise in README, Release-Notizen,
AGENTS.md und diesem Ticket geprüft.
