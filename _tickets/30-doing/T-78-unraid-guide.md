# T-78 · Unraid-Anleitung separat bereitstellen

Die Unraid-Installation steht bisher im allgemeinen README. Wie bei
StockPortfolio soll eine eigene `unraid/README.md` Installation,
Template-Einstellungen und lokale Template-Prüfung bündeln. Projekt- und
Docker-README führen mit kurzen Verweisen dorthin.

**Auftrag:** Mike: „StockPortfolio hast die Unraid-Sektion in ein eigenes
README ausgelagert. Check das und mach das hier gleich“.
**Stand:** Umsetzung begonnen. Keine Entscheidung von Mike erforderlich.

## Umfang

Drei Benutzeranleitungen und Board-Nachweise, höchstens 300 neue/geänderte
Zeilen ohne bestehende Status-Historie. Keine App-, Image- oder XML-Änderung.
StockPortfolio ist nur die gelesene Vorlage; dessen laufende Änderungen
bleiben unberührt. StockInfos Port, Datenablage und UID/GID gelten weiter.

## Prüfung

| # | Prüfung | Ergebnis |
|---|---|---|
| 1 | Unraid-Anleitung gegen Template, Dockerfile und App-Settings | Offen |
| 2 | README-Verweise, Abschnittsanker und Shell-Beispiele | Offen |
| 3 | Docker-Hub-Vorschau mit absoluten Links und Größenprüfung | Offen |

## Doku-Abgleich

`README.md`, `docker/README.md` und die neue `unraid/README.md` werden
gemeinsam geprüft. Bestehende Anker bleiben erreichbar. Lokale Lessons
SI-CX-01, SI-R-02 und SI-T-66 gelten weiter: reale Vorschau, begrenzter
Dokuauftrag, keine behauptete Unraid-Live-Prüfung.
