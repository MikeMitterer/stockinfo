# T-78 · Unraid-Anleitung separat bereitstellen

Die Unraid-Installation steht bisher im allgemeinen README. Wie bei
StockPortfolio soll eine eigene `unraid/README.md` Installation,
Template-Einstellungen und lokale Template-Prüfung bündeln. Projekt- und
Docker-README führen mit kurzen Verweisen dorthin.

**Auftrag:** Mike: „StockPortfolio hast die Unraid-Sektion in ein eigenes
README ausgelagert. Check das und mach das hier gleich“.
**Stand:** Erste Fassung von Claude freigegeben (Runde 1, `68702c6`).
Mike hat die doppelte Installationskurzfassung ausdrücklich verworfen.
Root- und Docker-README enthalten jetzt ausschließlich einen Unraid-Verweis;
die Skill-Regel ist entsprechend korrigiert. Korrigierte Runde 2 wird übergeben.
Auf Mikes ausdrücklichen Auftrag in master integriert und gepusht (StockInfo
`27bab4f`, PersonalSkills `4a751d5`). Runde 2 bleibt offen; kein neuer
Docker-Hub-Upload und noch kein Ticketabschluss.

## Umfang

Die drei Benutzeranleitungen, zugehöriger AGENTS-Hinweis und Board-Nachweise,
höchstens 300 neue/geänderte
Zeilen ohne bestehende Status-Historie. Keine App-, Image- oder XML-Änderung.
StockPortfolio ist nur die gelesene Vorlage; dessen laufende Änderungen
bleiben unberührt. StockInfos Port, Datenablage und UID/GID gelten weiter.

## Prüfung

| # | Prüfung | Ergebnis |
|---|---|---|
| 1 | Unraid-Anleitung gegen Template, Dockerfile und App-Settings | Lokales und veröffentlichtes XML bytegleich, XML gültig; Port 8000, /data-Mount, UID/GID 99/100 und alle aufgeführten Defaults abgeglichen |
| 2 | README-Verweise, Abschnittsanker und Shell-Beispiele | 73 lokale Links/Anker gültig; drei Shell-Blöcke ausschließlich in unraid/README.md mit bash -n geprüft; Screenshot-Ziele beider READMEs identisch und öffentlich HTTP 200 |
| 3 | Docker-Hub-Vorschau mit absoluten Links und Größenprüfung | Echter Bash-Einstieg erfolgreich: 6.128 UTF-8-Bytes; neuer Unraid-Link und Swagger-Bild korrekt umgewandelt |

Template-Prüfstand: `/Volumes/DevLocal/DevUnraid/Production/Templates/templates/stockinfo.xml`,
letzter Dateicommit `87b89cd`. Öffentliche Fassung von
`https://raw.githubusercontent.com/MikeMitterer/unraid-templates/master/templates/stockinfo.xml`
am 2026-09-26 nach `/private/tmp/stockinfo-t78-published.xml` geladen und per
`cmp` verglichen. Container-/Hostpfade, Port, Image, Konfigurationswerte und
Verweise passen; kein XML-Änderungsbedarf. Keine AGENTS.md im Template-Repo
vorhanden. Kein Containerstart und kein Test auf einer laufenden Unraid-Box.

```bash
# #1: XML prüfen und lokale mit öffentlicher Fassung vergleichen
xmllint --noout /private/tmp/stockinfo-t78-published.xml
cmp /private/tmp/stockinfo-t78-published.xml \
  /Volumes/DevLocal/DevUnraid/Production/Templates/templates/stockinfo.xml

# #3: echte Konvertierung, ohne Docker-Hub-Zugangsdaten
LANGUAGE=de XDG_CACHE_HOME=/private/tmp/stockinfo-t77-default-preview \
  ./.libs/ProjectTools/src/bash/dockerhub-readme.sh --preview
wc -c docker/preview/README.md
```

## Doku-Abgleich

`README.md`, `docker/README.md` und die neue `unraid/README.md` werden
gemeinsam geprüft. Bestehende `#unraid`-Anker bleiben erreichbar; Hauptanleitung
und Docker-Beschreibung verweisen auf die neue Anleitung. AGENTS.md nennt sie
für künftige Unraid-Änderungen. Der bislang nur im Root-README enthaltene
Swagger-Screenshot ist gemäß Docker-Skill auch in der Docker-Beschreibung
ergänzt. Der neue GitHub-Link wird erst nach Veröffentlichung dieses Branches
erreichbar; deshalb noch kein Hub-Upload.

StockPortfolios gelesener Arbeitsstand enthält bereits `unraid/README.md`;
die Root-README hat dort noch eine längere Installationskurzfassung. Übernommen
ist die Trennung mit beidseitigen Verweisen, nicht dessen Browser-Datenspeicher
oder Containerport 8080. StockInfos persistente Daten und Quellenprofil-Ablauf
sind erhalten; der Checkout-/BashLib-Bedarf des lokalen Profilhelfers ist erklärt.

Lokale Lessons
SI-CX-01, SI-R-02 und SI-T-66 gelten weiter: reale Vorschau, begrenzter
Dokuauftrag, keine behauptete Unraid-Live-Prüfung. Keine neue unabhängige
Fehlerklasse; kein neuer Lesson-Eintrag. Kein Anwendungstestlauf für diese
reine Dokuänderung nötig. `git diff --check` bestanden.

## Unabhängiger Review · Claude, Runde 1, 2026-09-26

**Ergebnis: approved.** Geprüft am eingefrorenen Stand `68702c6`. Volles
Ergebnis mit Belegen steht in
[STATUS](../STATUS.md#inbox--codex--t-78-runde-1--approved); hier nur die
Kurzfassung.

- Link-/Anker-Inventar selbst per Script gerechnet (nicht `grep`): 73 lokale
  Links über die drei geänderten READMEs, 0 defekt.
- Template frisch von der Raw-URL geladen und per `cmp` gegen die lokale
  Datei verglichen: bytegleich. Alle zehn Config-Defaults gegen die neue
  Tabelle abgeglichen.
- Vier Icon-/Screenshot-URLs aus dem Template einzeln abgerufen: alle HTTP 200.
- Docker-Hub-Vorschau selbst neu erzeugt: 6.261 Bytes, deckungsgleich.
- Diff-Budget 187+/37− über 6 Dateien, klar unter den vereinbarten 300 Zeilen;
  kein App-, Dockerfile- oder Template-Diff.

Menschlicher Abschluss (Verschieben nach `40-done/`) steht noch aus.

## Historie: Abgleich mit unraid-conventions (zurückgenommen)

Das inzwischen benannte Skill verlangt unter „Installation per wget
dokumentieren“ den Download und die Bedienfolge in **beiden** Anleitungen.
Der bloße Verweis im Root-README war damit zu knapp. Root- und Unraid-README
enthalten jetzt denselben Befehl; der Hinweis auf gespeicherte Nutzereinstellungen
steht vor dem Download. Beide erklären Force Update ohne erneuten Download
der gespeicherten Vorlage. Die Docker-README verlinkt weiterhin die Detailanleitung.

Die zusätzliche Pflicht zum Template-Abgleich nach jedem Image-Push ist für
diesen Doku-Auftrag nicht ausgelöst: Es wurde kein Image gepusht. Zentraler
Templatepfad, lokale Testkopie ohne TemplateURL, getrennte Testdaten und
Appdata-Rechte entsprechen bereits dem Skill. Docker-Hub-Vorschau unverändert
6.261 Bytes. Doku-Abgleich: zwei Installationsabschnitte nachgezogen,
Docker-README und AGENTS.md unverändert passend.
Die vier Installations-/Testblöcke sind erneut mit `bash -n` geprüft;
Download-Befehle bytegleich und Hinweise jeweils vor dem Befehl. Links und
Überschriften sind gegenüber der 73-Link-Prüfung unverändert. Diff-Prüfung sauber.

Einordnung: neu konkretisierte Konvention aus dem aktualisierten Skill,
keine neue unabhängige Lesson-Episode. Claudes Runde-1-Freigabe bleibt auf
`68702c6` begrenzt; der Nachtrag erhält eine eigene Prüfung.

## Mikes Korrektur: eine einzige Unraid-Anleitung

Mike: „Die Unraid-Infos brauchen nicht doppelt sein!!! ein Verweis auf das
Unraid-Readme genügt. Wenn das Skill was anderes behauptet - dann passe das
entsprechend an“.

Die übernommene Skill-Regel widersprach dem gewünschten Auslagern. Die
Dopplung ist entfernt, einschließlich der Unraid-spezifischen Port-/Pfad-
Kurzfassung in den beiden verweisenden READMEs. `unraid/README.md` bleibt die
vollständige Anleitung; die Hinweise zum Schutz vorhandener Einstellungen
bleiben dort vor dem Download erhalten.

`unraid-conventions/SKILL.md` in PersonalSkills verlangt nun ausschließlich
`unraid/README.md` als Ort für Installation, Einstellungen, Datenablage, Updates
und lokale Template-Tests. Root-/Docker-README verlinken nur darauf. Codex und
Claude verwenden über ihre installierten Symlinks dieselbe korrigierte Quelle.
Skill-Validator bestanden, 73 lokale Links/Anker gültig, reale Hub-Vorschau
6.128 Bytes. Keine doppelte Befehlsanleitung mehr; Diff-Prüfungen sauber.

**Doku-Abgleich:** Root-/Docker-README und Skill korrigiert. Unraid-README
und AGENTS.md bereits passend. Die bisherige ungeclaimte Runde-2-Übergabe wurde
zurückgezogen, nicht als abgeschlossenes Review gezählt. Die neue Fassung
ersetzt sie. Der konkrete Lernpunkt ist direkt in der beauftragten Skill-Regel
verankert: Nutzervorgabe zur Auslagerung erhalten, keine Kopierpflicht ableiten.
