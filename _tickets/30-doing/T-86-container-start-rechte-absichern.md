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

Für Mike steht nichts an, bis das Ticket eingeplant wird.
