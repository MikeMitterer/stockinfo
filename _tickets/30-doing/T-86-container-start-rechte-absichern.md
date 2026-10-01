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
  ausgelieferten, englisch dokumentierten Containeroberfläche.
  **Entscheidung Mike, 2026-10-01:** „english ist OK“.

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

Geplant / tatsächlich: 3 / 3 fachliche Änderungen; Produktdateien Runde 1:
1 (`docker/entrypoint.sh`), Runde 2: 2 (zusätzlich ein Kommentar in
`docker/Dockerfile`, Befund Codex); 5 Test-/Dokudateien (Smoke, drei READMEs,
Ticket). Diff-Zeilen siehe OUTBOX.

## Nacharbeit Runde 2 (Claude, 2026-10-01)

- **B1:** `PUID`/`PGID` fallen nur noch ohne Zuweisung auf 99/100 zurück
  (`${PUID-99}`); ein gesetzter leerer Wert bricht ab. `validateId` prüft
  Länge und Bereich 1 bis 4294967294 vor dem Vergleich mit 0. Neue Fälle
  A4c–A4g (PGID=0, beide leer, beide übergroß; übergroß darf weder
  „Illegal number“ noch „would run the app as root“ zeigen).
- **B2:** Die Abhilfe richtet sich nach dem Eigentümer des betroffenen
  Pfads (`remedyFor`): Gehört er root, nennt sie nur `chown -R UID:GID` auf
  dem Host; sonst zusätzlich `PUID`/`PGID` beziehungsweise `--user` mit den
  IDs des Eigentümers. Die SETUID/SETGID-Meldung nennt `/data`, die
  fehlenden Fähigkeiten und zwei ausführbare Wege. Fälle A6a/b, A7a/c, A9,
  A10 prüfen Pfad, IDs und Abhilfe; A7a und A10 verbieten „PUID=0“.
- **B3:** A7a verlangt zusätzlich die `chown`-Warnung; neu A7b
  (root-eigenes `tmpfs` Modus 777, `--cap-drop CHOWN`): Warnung und Start
  als 99:100. A1 und A8 verbieten die Warnung. Mutant „Warnung entfernt“:
  A7a und A7b rot, danach wiederhergestellt und erneut grün.
- **B4:** Alle Funktionen in Entrypoint und Smoke nennen Zweck, Parameter
  und Rückgabe; `T-86-smoke.sh --bogus` zeigt Fehlermeldung und Hilfe
  (Exit 2).
- **Dockerfile:** Kommentar zu den IDs beschreibt die Vorgabe 99/100 und
  `PUID`/`PGID`.
- **Läufe:** Rot gegen das Runde-1-Testimage (11 Fehlschläge, A7b grün, weil
  die Warnung dort schon existierte). Grün nach Neubau, zweimal; 0 eigene
  Container oder Volumes übrig. `shellcheck`/`sh -n`/`bash -n` sauber.
  Docker-Hub-Vorschau 8.691 Byte (READMEs unverändert; ihre Zusagen stimmen
  jetzt für alle Fälle).

## Nacharbeit Runde 3 und Restanalyse (Claude, 2026-10-01)

- **B2-Rest:** `remedyFor` prüft zuerst, ob der Pfad schon den Ziel-IDs
  gehört. Dann fehlt nur das Schreibrecht, und die Meldung rät zu
  `chmod -R u+rwX <host path>` statt zu `chown` oder `--user` mit denselben
  IDs. Neue Fälle: A6c (`--user 1000:1000`, `/data` 1000:1000 Modus 555),
  A7d (`/data` 99:100 Modus 555, Standardstart) und A10b (Datenbank 99:100
  Modus 444). Alle drei verlangen `chmod` und verbieten `chown -R` sowie
  den wirkungslosen `--user`- bzw. `PUID`-Rat. Gegen das Runde-2-Testimage
  rot (genau diese drei), nach Neubau grün; 0 Testreste.
- **Beschriftung:** Kopf und Hilfe des Smoke nennen „A1–A11 mit
  Unterfällen“.

**Restanalyse zu Beginn der Maximalrunde** (`max_review_rounds: 3`):

| Punkt | Stand | Einordnung |
|---|---|---|
| B1 IDs | erledigt in Runde 2, von Codex bestätigt | – |
| B2 Abhilfe | Rest „Eigentümer stimmt, Schreibbit fehlt“ in Runde 3 behoben, A6c/A7d/A10b | Blocker bis zur Prüfung |
| B3 Orakel | erledigt, Mutant belegt | – |
| B4 Doku/CLI | erledigt; Beschriftung A1–A11 in Runde 3 | – |
| Gruppenrecht | Ist `/data` nur über die Gruppe beschreibbar, greift die Schreibprobe korrekt; die Abhilfe nennt dann den Eigentümer-Weg. Nicht gemessen, kein beobachteter Fehlstart. | nicht blockierend |
| Unraid-Vorlage | geprüft, unverändert; ob `PUID`/`PGID` als feste Felder erscheinen, entscheidet Mike | nicht blockierend, außerhalb des Repos |

Warum drei Runden: Runde 1 brachte Grenzwerte und fehlende Orakel, Runde 2
deckte einen Abhilfefall auf, den die erste Eigentümerlogik nicht kannte.
Nächster Schritt: Codex prüft Runde 3; offen bleibt nur der B2-Rest.

## Verifier-Prüfung · Runde 1 (Codex, 2026-10-01)

**Ergebnis: `changes_requested`.** `8d91b4d` gegen `85d8f0b` unabhängig
geprüft. Kein Produktcode wurde im Review geändert. Der Diff umfasst sechs
Dateien mit +408/−14 Zeilen; `git diff --check` ist sauber.

**B1 · ID-Validierung übersieht leere Werte und meldet Überlauf als Root-ID.**
`docker/entrypoint.sh:78-81` setzt mit `${PUID:-99}` und `${PGID:-100}` auch
einen *ausdrücklich leeren* Wert auf die Vorgabe zurück. `PUID=` und `PGID=`
liefen im lokalen Testimage mit Exit 0 durch, obwohl der Scope Ziffern
verlangt. `validateId` in Zeile 37 verwendet danach `[ "$2" -ne 0 ]` ohne
Bereichsprüfung. Für `999999999999999999999999` erschien jeweils
`[: Illegal number` und anschließend fälschlich `PUID=0` beziehungsweise
`PGID=0 would run the app as root` (Exit 1). Bitte gesetzte leere Werte
ablehnen und übergroße IDs vor dem numerischen Vergleich mit korrekter
Variablen- und Wertmeldung abfangen. Die A4-Orakel brauchen beide Variablen
und diese Randwerte als negative Fälle.

**B2 · Fehlermeldungen erfüllen den zugesagten Abhilfevertrag nicht durchweg.**
Ohne `SETUID`/`SETGID` endet der Container vor dem App-Start, doch
`docker/entrypoint.sh:92` nennt nur IDs, Fähigkeiten und `--user`, nicht
`/data`. Scope-Vertrag und `docker/README.md` versprechen für diesen Fall
Pfad, IDs und Abhilfe; A9 prüft den Pfad nicht. Bei A7 gehört `/data` root,
`chown` ist gesperrt, und die Fehlermeldung empfiehlt dennoch als zweite
Option `PUID/PGID` auf den Eigentümer von `/data` zu setzen — das wäre 0
und wird von B1s ID-Regel abgelehnt. Bei A10 ist `/data` bereits 99:100;
dieselbe Empfehlung ändert an der root-eigenen Datenbankdatei nichts.
Bitte die Meldungen für diese Fälle passend machen und A7/A9/A10 auf die
jeweils zugesagten Angaben und eine ausführbare Abhilfe prüfen.

**B3 · Der Smoke misst zwei neue CHOWN-Zusagen nicht.**
`T-86-smoke.sh:162` verlangt für A7 nur den späteren Fehlertext;
`expectFailure` in Zeile 126 prüft keine `entrypoint WARNING`. Entfernte man
die Warnung, bliebe A7 grün. Der zweite zugesagte Zweig „`chown` scheitert,
aber `/data` ist schreibbar → Warnung und Start“ hat keinen Smoke-Fall.
Die unabhängige Gegenprobe mit root-eigenem `tmpfs` Modus 777 und
`--cap-drop CHOWN` zeigte Warnung und Exit 0; mit Modus 755 Warnung und
frühen Fehler. Bitte beide Orakel ergänzen, ohne fremde Container oder
Volumes in die Bereinigung einzubeziehen.

**B4 · Funktionsdokumentation und CLI-Hilfe aus dem Hausstandard fehlen.**
`code-standards/references/architecture.md` verlangt bei jeder neuen
Funktion Zweck, Parameter und Rückgabewert. Die fünf Funktionen in
`docker/entrypoint.sh` nennen keinen Rückgabewert; im neuen Smoke-Skript
fehlen Rückgabebeschreibungen, bei `usage` und `runSmoke` auch der
Funktionskommentar. `code-standards/references/cli.md` zeigt für unbekannte
Optionen Fehlermeldung *und* Usage; `T-86-smoke.sh --unknown` endet zwar mit
Exit 2, zeigt aber nur die Fehlermeldung. Bitte diese mechanischen Standards
im Coder-Stand nachziehen und Syntax, ShellCheck und betroffene CLI-Smokes
wiederholen.

**Unabhängig bestandene Nachweise:** `./_tickets/30-doing/T-86-smoke.sh --run`
baute `stockinfo-t86:smoke` für `linux/amd64` und meldete A1–A11 grün.
Gegen das bereits lokale `mangolila/stockinfo:latest` wurden A3, A4a/b,
A5–A7, A9 und A10 rot (acht Fälle), A1/A2/A8 blieben grün. `shellcheck -s sh`
für den Entrypoint, ShellCheck und `bash -n` für den Smoke, `sh -n` für den
Entrypoint sowie Hilfe ohne Argument und mit `--help` bestanden. Die
Testcontainer und Testvolumes sind entfernt; kein Image wurde gepusht.

**Standards und Doku-Abgleich:** Gelesen wurden
`/Users/macminipro/.codex/skills/code-standards/SKILL.md` mit
`architecture.md`, `shell.md`, `cli.md`, `quality.md` und
`documentation.md`, außerdem `docker-conventions/SKILL.md` und
`unraid-conventions/SKILL.md`. Architektur ✅ Entrypoint bleibt für den
Containerstart zuständig; Shell ⚠️ B1/B4; CLI ⚠️ B4; Qualität/Tests ⚠️ B3;
Docker-Laufzeit ⚠️ B1/B2; Dokumentation ⚠️ B2 und der veraltete Kommentar
`docker/Dockerfile:78-80`, der die jetzt konfigurierbare App-ID noch
uneingeschränkt als 99:100 beschreibt. Python, Frontend/i18n und Persistenz
➖. DRY ✅: Im Übergabediff und der berührten Umgebung liegt die
UID/GID-Validierung nur im Entrypoint und die Fallauswertung nur im
Smoke-Helfer; die wiederholten `setpriv`-Aufrufe sind Start- und
Prüfverdrahtung, keine zweite Fachregel. Die englischen Entrypoint-Meldungen
sind interne Containerausgabe; dafür ist kein App-i18n-Katalog nötig.

`README.md` (Docker-Abschnitt), `docker/README.md` (Storage/Configuration)
und `unraid/README.md` (Data) wurden gegen Entrypoint und Dockerfile
abgeglichen. Die Docker-Hub-Vorschau bestand mit 8.691 UTF-8-Bytes.
Das lokale Unraid-Template unter
`/Volumes/DevLocal/DevUnraid/Production/Templates/templates/stockinfo.xml`
nennt weiterhin Image `mangolila/stockinfo:latest`, Port 8000 und `/data`;
es setzt weder `--user` noch Cap-Drops. Die Standard-IDs 99:100 sind damit
abgedeckt; ein Template-Push fand nicht statt. Die Dockerfile-Kommentarzeile
und die Zusage zum A9-Fehlerpfad gehören zur Nacharbeit. Keine menschliche
Abnahme erfolgte.

## Verifier-Prüfung · Runde 2 (Codex, 2026-10-01)

**Ergebnis: `changes_requested`.** `8b1cd51` gegen `fbba09b` unabhängig
geprüft. B1, B3, B4 und der Dockerfile-Kommentar sind erledigt. Von B2
bleibt ein konkreter Fall offen; Produktcode wurde im Review nicht geändert.

**B2 · Rest: Die Abhilfe kann den gemeldeten Zustand unverändert lassen.**
`docker/entrypoint.sh:61-72` bildet den Rat allein aus dem Eigentümer des
Pfads. Bei `--user 1000:1000` und `/data` mit Eigentümer 1000:1000,
Modus 0555, endet der Container korrekt vor dem App-Start (Exit 1), meldet
aber als Abhilfe `chown -R 1000:1000 <host path>` oder nochmals
`--user 1000:1000`. Beide Vorschläge beschreiben schon den Ist-Zustand;
das fehlende Schreibrecht bleibt. Unabhängige Gegenprobe:

```sh
docker run --rm --user 1000:1000 \
  --tmpfs /data:uid=1000,gid=1000,mode=555 stockinfo-t86:smoke true
```

Die Meldung nennt `/data` und die IDs, aber keine wirksame Änderung der
Schreibrechte. Der Scope-Vertrag und `docker/README.md` sagen für diesen
Abbruch eine Abhilfe zu. Ein ebenso fehlender Schreibmodus einer bereits
passend besessenen Datenbankdatei führt nach derselben `remedyFor`-Logik
zum gleichen Problem (aus dem Code abgeleitet, nicht separat ausgeführt).
Bitte die Meldung auch für unverändertes Eigentum mit fehlendem Schreibrecht
brauchbar machen und einen Smoke-Fall mit passendem Eigentümer und fehlendem
Schreibbit ergänzen. Die Fälle A6a/b, A7a/c, A9 und A10 können bleiben.

**Bestätigte Nacharbeit:** Leere und übergroße Werte beider ID-Variablen
werden mit passender Meldung abgelehnt; A4c–A4g bestehen. A7a verlangt
die CHOWN-Warnung, A7b belegt Warnung mit anschließendem Start bei
beschreibbarem `/data`; A1 und A8 verbieten die Warnung. Die
SETUID/SETGID-Meldung nennt jetzt `/data`, IDs und Abhilfe. Die Funktionen
haben Zweck-, Parameter- und Rückgabeangaben; eine unbekannte Smoke-Option
zeigt Fehler und Hilfe (Exit 2). Der Dockerfile-Kommentar nennt die
konfigurierbaren IDs.

**Unabhängige Nachweise:** `./_tickets/30-doing/T-86-smoke.sh --run` baute
das lokale Testimage für `linux/amd64`; alle A1–A11 samt A4a–g, A6a/b und
A7a–c bestanden. `shellcheck -s sh docker/entrypoint.sh`, ShellCheck für
den Smoke, `sh -n`, `bash -n` und `git diff --check fbba09b 8b1cd51`
bestanden. Die Docker-Hub-Vorschau bestand; die zuvor gemessene Größe von
8.691 UTF-8-Bytes gilt weiterhin, da `docker/README.md` unverändert ist.
Eigene Smoke-Container und Volumes sind entfernt; kein Push und keine
menschliche Abnahme.

**Standards und Doku-Abgleich:** `code-standards` (Architektur, Shell, CLI,
Qualität, Dokumentation), `docker-conventions` und `unraid-conventions`
wurden gegen die geänderten Dateien angewandt. Shell/CLI/Qualität ✅ für
B1/B3/B4; Docker-Laufzeit und Dokumentation ⚠️ wegen B2. DRY ✅: Die
Abhilfe wird in einer Funktion gebildet. Python, Frontend/i18n und
Persistenz ➖. `README.md`, `docker/README.md` und `unraid/README.md`
wurden erneut gegen das Verhalten abgeglichen; die Dateien selbst sind in
Runde 2 unverändert. Die konkrete Zusage einer wirksamen Abhilfe in
`docker/README.md` ist noch nicht erfüllt. Das Unraid-Template ist von
der Nacharbeit nicht betroffen. Der Smoke-Header und seine Hilfe nennen
„A1–A12“, obwohl das Skript A1–A11 mit Unterfällen ausführt; bitte diese
beiden Beschriftungen berichtigen.
