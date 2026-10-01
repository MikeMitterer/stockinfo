# T-86 · Containerstart bei Rechteproblemen absichern

**Warum dieses Ticket:** Mike hat am 2026-10-01 entschieden, dass sich die
Images nach den Unraid-Vorgaben richten und Rechteprobleme beim Start klar
abfangen. StockPortfolio hat dabei einen Absturz mit einem `/data`-Ordner im
Besitz von `root` gefunden und in seinem T-72 behoben. Mike: „Dann hat
wahrscheinlich StockInfo das selbe Problem - leg dort ein entsprechendes
Ticket an“.

**Stand der Prüfung (von StockPortfolio aus, nur gelesen):** Den Kernfall
deckt StockInfo bereits ab. `docker/entrypoint.sh` startet als root, übergibt
`/data` an `stockinfo` (UID 99 / GID 100) und gibt die Rechte mit `setpriv`
ab. Offen sind die Randfälle, die StockPortfolio in T-72 zusätzlich abfängt:

1. **`chown` scheitert stumm** (`|| true`), etwa auf NFS/SMB. Ist `/data`
   dann nicht beschreibbar, startet die App und scheitert erst später, ohne
   Hinweis auf Ordner und IDs.
2. **Kein Schreibtest** vor dem Start der App.
3. **Start mit `--user`:** `chown` und `setpriv` scheitern ohne Root-Rechte;
   die Meldung kommt von `setpriv`, nicht als verständlicher Hinweis.
4. **Fehlende SETUID/SETGID-Fähigkeit** (`--cap-drop`): gleiches Bild.
5. **Feste IDs:** UID 99 / GID 100 sind nicht über `PUID`/`PGID` änderbar,
   wie es viele Unraid-Images anbieten, falls Appdata einem anderen Benutzer
   gehört.
6. **`chown -R` bei jedem Start**, auch wenn alles schon passt.

Diese Punkte sind aus dem Code abgeleitet. Die Messung unten stellt sie im
StockInfo-Container nach.

**Messung (Claude, 2026-10-01):** Image `mangolila/stockinfo:latest`
(1.3.0, enthält den aktuellen `entrypoint.sh`), `/data` als `tmpfs`, damit
Eigentümer und Rechte genau festliegen. Ein Container je Fall, danach entfernt.

| Fall | Ergebnis |
|---|---|
| `/data` gehört `root` (frischer Appdata-Ordner) | ✅ startet; `/data` und `stockinfo.db` gehören 99:100; App-Prozesse 99:100; `/operational` 200 |
| `/data` gehört UID 1000, Modus 700 (ältere Daten) | ✅ startet; Eigentümer danach 99:100 |
| `--user 1000:1000`, `/data` nicht beschreibbar | ❌ Exit 127, nur `setpriv: setresuid failed: Operation not permitted` |
| `--user 1000:1000`, `/data` beschreibbar | ❌ Exit 127 mit derselben Meldung; startet also auch dann nicht, wenn es könnte |
| `--cap-drop CHOWN`, `/data` gehört `root` | ❌ Exit 3, `sqlite3.OperationalError: unable to open database file`; kein Hinweis auf Ordner oder IDs (Punkt 1 und 2) |
| `--cap-drop SETUID --cap-drop SETGID` | ❌ Exit 127, nur die `setpriv`-Meldung (Punkt 4) |

Ergebnis: Die Unraid-Vorgabe 99:100 erfüllt StockInfo mit der Vorlage
(`/mnt/user/appdata/stockinfo` → `/data`, kein `--user`). Ein frischer
Ordner im Besitz von `root` führt nicht zum Absturz wie bei StockPortfolio
vor T-72. Offen bleiben die Randfälle: Start mit `--user` ist gar nicht
möglich, und auf Speicher ohne `chown` endet der Start mit einer
SQLite-Meldung statt eines verständlichen Hinweises. `PUID`/`PGID` fehlen
(Punkt 5); `chown -R` läuft bei jedem Start (Punkt 6, nicht gemessen).

**Auswirkung:** Unter Unraid mit Appdata auf dem Array oder Cache fällt nichts
auf. Auf Netzlaufwerken, mit `--user` oder eingeschränkten Fähigkeiten endet
der Start unklar oder die App scheitert später beim Schreiben.

**Vergleich:** StockPortfolio `docker/entrypoint.sh` und
`docker/smoke-test.sh` (Branch `t-72-unraid-uid-gid`, Commit `eaf6db6` und
folgende) zeigen eine mögliche Lösung samt Rauchtest für alle Fälle. Über die
Lösung für StockInfo entscheidet, wer den Dienst kennt.

**Stand:** Mike, 2026-10-01: „ja, T-86 nach T-82 einplanen“. Aktiv auf
`t-86-container-start-rechte`, Coder `claude`, Verifier `codex`.

## Scope-Vertrag

- **Ergebnis:** Der Container startet in allen Fällen der Messung entweder
  als Nicht-Root-Prozess mit beschreibbarem `/data`, oder er bricht vor dem
  App-Start mit einer Meldung ab, die Ordner, IDs und Abhilfe nennt. Der
  Unraid-Standardfall verhält sich wie bisher (99:100).
- **Fachliche Änderungen (3):**
  1. `docker/entrypoint.sh`: `PUID`/`PGID` (Vorgabe 99/100, Ziffern, nicht 0);
     `chown -R` nur bei abweichendem Eigentümer, Fehlschlag als Warnung;
     Schreibprobe als Zielbenutzer auf `/data` und eine vorhandene Datenbank;
     verständliche Meldung, wenn der Rechtewechsel nicht möglich ist.
  2. Start mit `--user`: kein `chown`/`setpriv`, nur Schreibprobe, dann Start.
  3. Doku: `docker/README.md`, `unraid/README.md`, `README.md` nennen
     `PUID`/`PGID` und die Grenzen.
- **Dateien:** `docker/entrypoint.sh`, drei READMEs; Prüfskript
  `_tickets/30-doing/T-86-smoke.sh`; dieses Ticket. Dockerfile nur, falls die
  Laufzeit ein Werkzeug vermisst.
- **Budget:** 1–2 Produktdateien, 5 Test-/Dokudateien, 400 Diff-Zeilen.
- **Nicht-Ziele:** keine Änderung an App, Datenbankformat, Port oder Image-Name;
  kein Push, kein Release. Die Unraid-Vorlage bleibt unverändert, solange die
  Vorgaben 99/100 gelten; `PUID`/`PGID` sind dort optional über eigene
  Variablen setzbar (wird im Ticket geprüft, nicht vorab geändert).

**Akzeptanzfälle (Smoke, eigener Container je Fall, `tmpfs` als `/data`):**

| # | Fall | Erwartung | Vorher (Messung oben) |
|---|---|---|---|
| A1 | `/data` gehört `root` | startet, Dateien und Prozesse 99:100 | ✅ |
| A2 | `/data` gehört UID 1000 | startet, danach 99:100 | ✅ |
| A3 | `PUID=1234 PGID=4321` | Prozess und Dateien 1234:4321 | ❌ nicht vorgesehen |
| A4 | `PUID=abc` bzw. `PUID=0` | Abbruch vor App-Start, Meldung nennt `PUID` | ❌ |
| A5 | `--user 1000:1000`, `/data` beschreibbar | startet als 1000:1000 | ❌ Exit 127 |
| A6 | `--user 1000:1000`, `/data` nicht beschreibbar | Abbruch, Meldung nennt `/data` und 1000:1000 | ❌ nur `setpriv` |
| A7 | `--cap-drop CHOWN`, `/data` gehört `root` | Warnung zu `chown`, dann Abbruch mit Ordner und IDs | ❌ SQLite-Fehler |
| A8 | `--cap-drop CHOWN`, `/data` schon 99:100 | startet ohne Warnung (kein unnötiges `chown`) | ❌ nicht unterschieden |
| A9 | `--cap-drop SETUID --cap-drop SETGID` | Abbruch, Meldung nennt fehlenden Rechtewechsel | ❌ nur `setpriv` |
| A10 | Datenbankdatei vorhanden, gehört `root` mit 644, `chown` nicht möglich | Abbruch mit Hinweis auf die Datei | ❌ ungeprüft |
| A11 | jeder laufende Fall | kein App-Prozess mit UID 0 | ✅ |

## Nachweise (Claude, 2026-10-01)

Prüfskript: `./_tickets/30-doing/T-86-smoke.sh --run` baut aus dem
Arbeitsstand das Testimage `stockinfo-t86:smoke` (`linux/amd64`) und startet
je Fall einen eigenen Container; `IMAGE_REF` prüft stattdessen ein vorhandenes
Image. Am Ende entfernt es nur die eigenen Container und Volumes (nach jedem
Lauf geprüft: 0 übrig).

| # | Rot: `IMAGE_REF=mangolila/stockinfo:latest` (alter Entrypoint) | Grün: Testimage aus `docker/entrypoint.sh` neu |
|---|---|---|
| A1 | ✓ | ✓ 99:100 |
| A2 | ✓ | ✓ 99:100 |
| A3 | ✗ Prozess 99:100 | ✓ 1234:4321 |
| A4a/b | ✗ startet trotzdem | ✓ Exit 1, Meldung nennt `PUID` |
| A5 | ✗ `setpriv: setresuid failed` | ✓ 1000:1000 |
| A6 | ✗ Exit 127 | ✓ Exit 1, Ordner, IDs, Abhilfe `--user` |
| A7 | ✗ Exit 3, SQLite-Fehler | ✓ Warnung zu `chown`, dann Exit 1 mit Ordner und IDs |
| A8 | ✓ | ✓ ohne Warnung |
| A9 | ✗ `setpriv`-Meldung | ✓ Exit 1, nennt SETUID/SETGID und `--user` |
| A10 | ✗ Exit 3, SQLite-Fehler | ✓ Exit 1, nennt `/data/stockinfo.db` |
| A11 | – | ✓ in allen laufenden Fällen trifft der App-Prozess den Zielwert, nie 0:0 |

- **Gefundener Fehler während der Umsetzung:** Die erste Schreibprobe
  `: > Datei` beendete `dash` bei fehlendem Schreibrecht mit Exit 2, bevor
  die Meldung kam (A6, A7 rot). Ersetzt durch `touch`; danach grün.
- **Wiederholung:** Drei weitere Läufe grün, davon zwei mit vorhandenem
  Testimage und einer mit Neubau. Ein Lauf direkt nach einem Neubau meldete
  bei A1 einmal „No such container“; das ließ sich nicht wiederholen und
  betraf den Docker-Aufruf, nicht den Entrypoint.
- **Benanntes Volume wie `make up`:** Start, Neustart, `healthy`,
  `/operational` 200, Daten erhalten; eine als root angelegte Datei gehörte
  nach dem Neustart wieder 99:100; keine Entrypoint-Meldung im Log.
- **Statisch:** `shellcheck -s sh docker/entrypoint.sh` und
  `shellcheck _tickets/30-doing/T-86-smoke.sh` ohne Befund; Skript ohne
  Argument zeigt Hilfe.
- **Meldungssprache:** Die Entrypoint-Meldungen sind englisch wie die übrige
  Containerausgabe (App-Logs, `docker/README.md`). `code-standards` sieht für
  einfache Skripte Deutsch vor; hier ist der Entrypoint Teil der
  ausgelieferten, englisch dokumentierten Containeroberfläche. Bewusste
  Abweichung, zur Prüfung durch den Verifier und Mike.

## Doku-Abgleich

- `docker/README.md` → *Storage and permissions*: Start als root nur zur
  Vorbereitung, `PUID`/`PGID`, `chown` nur bei Bedarf, Warnung bei NFS/SMB,
  Abbruch mit Meldung, `--user`. *Configuration*: Zeile `PUID` / `PGID`.
  Docker-Hub-Vorschau 8.691 Byte, unter der Grenze.
- `unraid/README.md` → *Data and source profiles*: frischer Appdata-Ordner
  im Besitz von `root` funktioniert; `PUID`/`PGID` als eigene Variablen für
  abweichende Eigentümer; Abbruch mit Meldung.
- `README.md` → Docker-Abschnitt: `PUID`/`PGID` und Verweis auf die
  Containeranleitung.
- **Unraid-Vorlage** `DevUnraid/Production/Templates/templates/stockinfo.xml`
  geprüft, nicht geändert: Pfad `/data`, Port 8000, keine `--user`- oder
  Capability-Parameter; mit den Vorgaben 99/100 deckt sie A1 ab.
  `PUID`/`PGID` lassen sich in Unraid über „Add another Variable“ setzen.
  Ob die Vorlage die beiden Felder fest anbieten soll, entscheidet Mike.

## Umfang

Geplant / tatsächlich: 3 / 3 fachliche Änderungen; 1 Produktdatei
(`docker/entrypoint.sh`, Dockerfile unverändert); 5 Test-/Dokudateien
(Smoke, drei READMEs, Ticket). Diff-Zeilen siehe OUTBOX.
