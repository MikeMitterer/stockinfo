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

Diese Punkte sind aus dem Code abgeleitet, nicht im StockInfo-Container
nachgestellt.

**Auswirkung:** Unter Unraid mit Appdata auf dem Array oder Cache fällt nichts
auf. Auf Netzlaufwerken, mit `--user` oder eingeschränkten Fähigkeiten endet
der Start unklar oder die App scheitert später beim Schreiben.

**Vergleich:** StockPortfolio `docker/entrypoint.sh` und
`docker/smoke-test.sh` (Branch `t-72-unraid-uid-gid`, Commit `eaf6db6` und
folgende) zeigen eine mögliche Lösung samt Rauchtest für alle Fälle. Über die
Lösung für StockInfo entscheidet, wer den Dienst kennt.

Für Mike steht nichts an, bis das Ticket eingeplant wird.
