# T-77 · README lokal nach Docker Hub übertragen

Beim Kopieren des README nach Docker Hub brechen relative Bild- und
Dokumentlinks. Ein lokales Script soll sie beim Veröffentlichen automatisch
auf GitHub beziehen. Zugangsdaten werden lokal gelesen und ausschließlich an Docker Hub gesendet;
sie erscheinen nicht in Ausgaben oder Prozessargumenten.

**Auftrag:** Mike ersetzt die diskutierte GitHub-Automatisierung durch ein
lokales Script nach Skill-Konventionen. Präzisierung: keine eigenen Targets;
der erfolgreiche bestehende Docker-Hub-Push ruft das Script auf.
**Stand:** Grundfassung **und** Docker-Beschreibung/403-Diagnose von Claude
unabhängig approved (Runde 1: StockInfo `535e7a7`, ProjectTools `8780252`;
Runde 2: StockInfo `efeab04`, ProjectTools `a1908f7`). Offen ist Mikes
Abschlussbestätigung. Keine GitHub Action angelegt.
Die neue Beschreibung wurde lokal geprüft, noch nicht nach Docker Hub übertragen.

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
  --preview
./.libs/ProjectTools/src/bash/dockerhub-readme.sh \
  --publish
```

| Parameter | Bedeutung |
|---|---|
| `--project-dir` / `-C` | Projektwurzel; Vorgabe ist das Arbeitsverzeichnis, nicht der Scriptort |
| `--readme` / `-s` | Quelldatei relativ zur Projektwurzel; Vorgabe `docker/README.md` |
| `--github-repository` / `-g` | GitHub `owner/repository`; sonst aus dem `origin` des Verbrauchers |
| `--ref` / `-b` | Bereits veröffentlichter GitHub-Branch oder Commit; Vorgabe `master` |
| `--repository` / `-r` | Docker-Hub-Repository; überschreibt die automatische Ermittlung |
| `--username` / `-u` | Login-Benutzer, falls abweichend vom Docker-Hub-Namespace |
| `--token-file` / `-t` | Lokale Token-Datei; Vorgabe siehe unten |
| `--description` / `-d` | Optionale Kurzbeschreibung; sonst bleibt sie unverändert |
| `--output` / `-o` | Vorschauziel, relativ zum Projekt; Vorgabe `docker/preview/README.md` |

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


**Zwischenprüfung nach Bash-/Isolationsauftrag:** 23 ProjectTools-Tests und
7 StockInfo-Integrationstests bestanden. ShellCheck für den neuen Bash-Einstieg,
Bash-Syntax, Ruff Check/Format und beide Skill-Validatoren bestanden.
Aktuelles konvertiertes README: 24.980 UTF-8-Bytes. Test-Installationen erfolgten
in temporären Werkzeugcaches aus lokalen Wheels; keine globale Installation
und keine Änderung der StockInfo-`.venv`. Die Befunde zum Python-Direktaufruf
und zu fehlenden Eingaben sind durch CLI-Tests abgedeckt. Kein Live-Upload.
Doku-Abgleich schließt jetzt ausdrücklich auch die isolierte Werkzeugumgebung
und die prinzipielle Vorgehensweise im code-standards-Skill ein.

Zwischenstand ProjectTools: `3005e11` (Vorgänger `3c4e025`).

Damals erfasste Skill-Prüfstände (aktuelle Werte siehe STATUS.md):
- `makefile-conventions/SKILL.md`: `d9e6ee6615e28ae5336a71a1810b305a4bc90e6ed7ed4e1a8d96ee1d6bd10c66`
- `code-standards/SKILL.md`: `93b2b62cbacc9ac73f0188afd8fb97146bed4a90db54e9bc0f3d96bc5776c7c6`
- `code-standards/references/python.md`: `97829547aefe04bc9e379dffb6b853a912a90e57a80fcd5d44184ae5397d5b53`


### CLI-Gestaltung nach Mikes Befund

Der bisherige Standards-Nachweis war zu pauschal: Technische Tests und native
Parser-Hilfe belegten nicht die verlangte Farbgestaltung und das Look-and-feel.
Mike hat dies ausdrücklich beanstandet. Die erneute Review-Übergabe wurde deshalb
vor Freigabe weiter zurückgehalten.

Jetzt: Bash reicht die BashLib-Farben an Python weiter. Der native argparse-Parser
bleibt die einzige Quelle der Optionen. Ein Formatter richtet Kurzoption, `|`,
Langoption und Erklärung aus; Gruppen „Aktionen“, „Repository“, „Dateien“, „Hilfe“
und Beispiele gliedern die Ausgabe. Überschriften sind hellblau, Optionen und
Pfade gelb, Beispiele/Erfolg grün, Fehler rot. Die Hilfe nennt den tatsächlich
aufgerufenen Bash-Einstieg. `NO_COLOR`, Pipes und nicht-interaktive Ausgaben
bleiben ohne ANSI-Sequenzen. Es kommt keine neue Python-Abhängigkeit hinzu.

Beleg: tatsächliche Hilfe und Vorschau im Pseudoterminal betrachtet. Vier
zusätzliche CLI-Prüffälle prüfen Terminalfarben, feste Spalten, Beispiele,
NO_COLOR, Pipe-Ausgabe und rote Fehlermeldung ohne Traceback. Aktueller Stand:
**27 ProjectTools-Tests plus 7 StockInfo-Tests bestanden (34 insgesamt)**.
Ruff Check/Format und ShellCheck bestanden. Die frühere Behauptung vollständiger
CLI-Konformität ist damit durch konkrete Ausgaben und Tests ersetzt.


### Defaults und Zielermittlung für weitere Projekte

Vorschau: `--preview` reicht im Projektverzeichnis aus. Quelle ist `docker/README.md`,
GitHub-Branch `master`, Ziel `docker/preview/README.md`. Fehlende Zielordner
werden angelegt; `--output` überschreibt den Pfad. StockInfo ignoriert den
Vorschauordner in Git. Verbraucher wie StockPortfolio sollten das ebenfalls tun.

Upload: `--publish` ermittelt das Ziel aus `DOCKERHUB_REPOSITORY`, sonst aus
`IMAGE_NAME` (Umgebung/Makefile) und `NAMESPACE` + `NAME` in `docker/build.sh`.
Die Werte müssen zusammen genau ein Repository ergeben. Das Script liest nur
literale Zuweisungen und führt keine Buildscripts oder Make-Ausdrücke aus.
Fehlende, berechnete oder widersprüchliche Werte erfordern `--repository`;
der explizite Parameter hat Vorrang. Das GitHub-Repository bestimmt keine
Docker-Hub-Namensräume. Docker-Hub-Präfixe und Tags werden entfernt, andere
Registries abgewiesen. Der Push-Hook übergibt weiterhin sein tatsächliches Ziel.

Doku-Abgleich: StockInfo README, AGENTS und diese Übertragungsnotizen sowie
ProjectTools README und Makefile-Skill beschreiben die aktuellen Defaults.


Abschließende Prüfung: **36 ProjectTools-Tests + 7 StockInfo-Tests = 43 grün**.
Ruff Check/Format, ShellCheck und Diff-Whitespace-Prüfung bestanden. AST-Inventar
aller Python-Bezeichner geprüft: englisch, außer erlaubten deutschen Testnamen.
Echter Bash-Aufruf mit nur `--preview` erzeugt `docker/preview/README.md`
mit **24.929 UTF-8-Bytes**. Die statische Erkennung an den tatsächlichen
Projektdateien liefert `mangolila/stockinfo` und `mangolila/stockportfolio`.
Keine echten Zugangsdaten gelesen, kein Live-Upload. Aktuelle Commitstände
und Skill-Hashes stehen in der erneuten Review-Übergabe in STATUS.md.

### Unabhängiger Review Runde 1 · Claude, approved

Vollständiges Ergebnis in `STATUS.md` unter „INBOX → codex · T-77 Runde 1 ·
approved". Kurzfassung: Übergebener Stand `a7e37ba` (StockInfo) und
ProjectTools `8780252` unabhängig nachgestellt, nicht nur gelesen — unter
anderem echter Erstlauf in leerer, isolierter Cache-`.venv`, Symlink-Schutz,
`.mo`-Neukompilierung, AST-Bezeichnerinventar und Skill-Hash-Gegenrechnung.

Ein Fund: `git diff --check` war entgegen der Zusage nicht clean —
`docs/release-notes.md` trug seit dem allerersten Commit `6f31bbc` eine
Leerzeile am Dateiende. Mechanisch und verhaltensneutral; als
Verifier-Selbstheilung mit `style(review): drop trailing blank line in
release-notes.md` (`535e7a7`) behoben und erneut geprüft (43 Tests grün,
`git diff --check` clean). `535e7a7` ist der geprüfte Endstand.

Kein weiterer Befund. T-77 ist das einzige Element seiner `priority_chain`;
Zustand geht auf `portfolio_review` an Mike.


### Laufzeitnachtrag: HTTP 403 beim ersten echten Upload

Mike meldet einen 403 bei `dockerhub-readme.sh -p`. Der bisherige Fehlertext
unterscheidet nicht zwischen Anmeldung, Änderung und Rücklesen. Die lokale
HTTP-Gegenprobe bestätigt diese Diagnose-Lücke für alle drei Schritte.
Die neue Meldung nennt den jeweiligen Schritt mit POST/PATCH/GET und gibt
bei 403 einen Hinweis auf Login, Repository-Zugriff und Token-Rechte.
Antwortkörper und Auth-Header bleiben verborgen. Drei neue Tests prüfen
Schrittunterscheidung und Geheimnisschutz (vor Korrektur alle drei rot).

Die Ursache des tatsächlichen Docker-Hub-403 ist noch unbestätigt. Für den
Beschreibungs-Upload benötigt ein PAT Read, Write, Delete; reine Push-Rechte
reichen dafür nicht aus (Referenz: README von peter-evans/dockerhub-description).
Mike wurde nur nach der Berechtigungsstufe gefragt; keine echten Tokens
wurden ausgelesen und kein echter Upload zur Diagnose ausgelöst.

Doku-Abgleich: Die Token-Anforderung steht bereits in StockInfo README,
ProjectTools README und Makefile-Skill. Keine Änderung dieser Zusage nötig.
Die neue Diagnose und ihre Grenzen sind hier und in STATUS.md festgehalten.

Prüfstand Diagnose: ProjectTools `9e6dfc4`, 46 Tests grün, Ruff Check/Format
und Diff-Prüfung bestanden. Der Live-403 ist damit noch nicht als behoben bestätigt.


### Eigene Beschreibung für Docker Hub

Mike bestätigt den erfolgreichen Live-Upload nach Anpassung der Token-Rechte.
Der 403 ist gelöst. Danach beauftragt er eine eigene Container-Beschreibung:
`docker/README.md` behandelt Docker Run/Compose, Datenvolume, Port, Einstellungen,
Updates, Logs und Unraid. Keine Python-/Node-Installation und keine Make-Build-
Anleitung für Nutzer des fertigen Images. Das Root-README bleibt Projekt-Doku.

Der gemeinsame Uploader verwendet nun standardmäßig `docker/README.md`.
`--readme` bleibt der explizite Override; fehlt die eigene Beschreibung, gibt
es keinen stillen Rückfall auf `README.md`. Andere Projekte wie StockPortfolio
müssen ihre eigene `docker/README.md` bereitstellen oder die Quelle ausdrücklich
wählen. Ausgabe bleibt `docker/preview/README.md`, GitHub-Branch bleibt `master`.

Bilder verweisen relativ zur Quelldatei auf bestehende Repo-Dateien, z. B.
`../unraid/screenshots/dashboard.png`. Die vorhandene Pandoc-Konvertierung
berücksichtigt den Quellordner und erzeugt Raw-GitHub-URLs. Keine Bildkopien
im Docker-Verzeichnis und kein separates Hosting. Das 25.000-Byte-Limit gilt
für die konvertierte Docker-Beschreibung, nicht mehr für das Root-README.

Doku-Abgleich: neue Docker-README gegen Dockerfile, Entrypoint und App-Settings;
Root-README, AGENTS, Make-Hilfe, ProjectTools README und Makefile-Skill angepasst.
Die vorherigen Prüfnachweise und Größenangaben oben beziehen sich auf die damals
veröffentlichte Root-README. Der jetzige Auftrag ändert diese Quellenwahl.


Aktueller Nachweis: **40 ProjectTools-Tests + 7 StockInfo-Tests = 47 grün**.
Default- und Kein-Fallback-Gegenproben waren vor Anpassung rot. Reale Vorschau
mit `--preview`: **6.232 UTF-8-Bytes**. GitHub-Repo-Link direkt unter der
Einleitung, Screenshot als absolute Raw-GitHub-URL. Lokale Dokument-/Bildlinks
auf Existenz geprüft; Compose-YAML eingelesen und Volume-Zuordnung bestätigt.
Ruff Check/Format und Diff-Prüfung gegen die freigegebenen Basen bestanden.
AST-Inventar: englische Bezeichner, deutsche Testnamen wie erlaubt.
Kein Containerstart oder Live-Upload für diesen Dokumentationsnachtrag.
