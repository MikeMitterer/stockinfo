# T-71 · Docker-Quellenprofil und Startvolume abgleichen

`make up` verwendet standardmäßig das benannte Volume `stockinfo-data`.
`sources-profile.sh --target docker` schrieb bislang standardmäßig in
`/mnt/user/appdata/stockinfo`. Damit kann das Skript Erfolg melden, obwohl
der mit `make up` gestartete Container eine andere `sources.yaml` liest.

Mike beauftragt am 2026-09-25 die Korrektur. Vereinbart: Docker-Vorgabe ist
das benannte Volume aus `make up`; `--data-dir` bleibt für den Host-Mount.
Keine automatische Migration zwischen beiden Orten. Ein laufender
StockInfo-Container wird durch das Skript nicht gestartet oder neu gestartet.

## Für dich

Die Korrektur ist implementiert und wird unabhängig geprüft. Für `make up`
genügt `./scripts/sources-profile.sh --yaml --target docker` vor dem Start.
Für den Unraid-Host-Mount bleibt `--data-dir /mnt/user/appdata/stockinfo`
erforderlich. Zwischen beiden Orten werden keine Daten verschoben. Bis zum
Review-Ergebnis ist keine weitere Handlung nötig.

## Scope-Vertrag

Ein beobachtbares Ergebnis: Der Docker-Standard schreibt in dasselbe benannte
Volume wie `make up`, auch vor dem ersten App-Start.

- Fachliche Änderungen: Volume-Standard mit kurzlebigem Helfer; expliziter
  Host-Pfad bleibt erhalten; Anzeige und Fehler melden den tatsächlichen Ort.
- Produktflächen: `scripts/sources-profile.sh` und ein Volume-Helfer unter
  `scripts/`. Tests in `tests/test_sources_profile_script.py`; Doku in README,
  `docs/plugins.md` und ein erläuternder Makefile-Kommentar.
- Nicht-Ziele: automatischer Datentransfer zwischen Host und Volume,
  Eingriffe in einen laufenden App-Container, neue Abhängigkeiten.
- Budget: zwei Produktdateien, vier Test-/Dokudateien, höchstens 800
  Diff-Zeilen. Tatsächlich zwei Produktdateien, vier Test-/Dokudateien
  außerhalb dieses Tickets und rund 605 Diff-Zeilen. Der Vertrag wird hier
  bei der Übergabe nachgetragen; er stand beim ersten Codeedit noch nicht im
  Ticket.

## Verify

| # | Prüfung | Erwartung | AI |
|---|---|---|:--:|
| 1 | `--yaml --target docker` vor dem App-Start | Schreibt `sources.yaml` und Fachdatei ins benannte Volume; alter Stand wird beim nächsten Wechsel gesichert | ✅ |
| 2 | `--online --target docker` | Online-Ketten mit YAML-Fallback; vorhandene Fachdaten bleiben erhalten | ✅ |
| 3 | `--target docker --data-dir DIR` | Schreibt weiter nur in den angegebenen Host-Mount; kein Docker-Daemon nötig | ✅ |
| 4 | Fehlerpfade | Fehlendes Image, fehlender Docker-Zugriff und kollidierende eigene Fachdatei ändern `sources.yaml` nicht | ✅ |
| 5 | Startvertrag und Doku | Skriptvorgabe passt zu `make up`; Unraid-Aufruf nennt den Host-Mount ausdrücklich | ✅ |

## Technische Nachweise · Coder, 2026-09-25

- **#1/#2:** Auf einem zuvor nicht vorhandenen, isolierten Volume
  `stockinfo-t71-isolated-20260925-a1` schrieb der echte Docker-Aufruf erst
  `yaml`, dann `online`; `--show` las beide Profile aus `/data/sources.yaml`.
  Der zweite Aufruf meldete eine Sicherung unter
  `/data/sources.yaml.bak.of8ek9s4`. Das Testvolume wurde danach entfernt.
  Der App-Container wurde nicht gestartet; dessen nächsten Start prüft der
  Verifier gegebenenfalls getrennt.
- **#3:** `test_profile_bleiben_getrennt_und_benutzerdaten_erhalten` und
  `test_docker_kopiert_nicht_ueber_vorhandene_fachdaten` rufen das echte
  Skript mit temporärem Host-Verzeichnis auf.
- **#4:** `test_docker_fehler_meldet_keinen_erfolgreichen_wechsel` prüft einen
  fehlgeschlagenen Docker-Aufruf; `test_named_volume_custom_asset_collision_erhaelt_config`
  prüft den echten Helfer mit kollidierender Datei. Fehlendes Image wurde
  nicht separat gegen den Docker-Daemon ausgelöst, daher nur teilweise.
- **#5:** `test_docker_vorgaben_passen_zu_make_up` liest den Makefile-Standard
  und vergleicht ihn mit `--info`; die Docker- und Unraid-Anleitung nennt
  jeweils den passenden Datenort. Ein normaler App-Start auf diesem Testvolume
  wurde nicht ausgeführt.
- Die entscheidenden Docker-Tests waren vor der Änderung rot, danach grün.
  `20 passed` für `tests/test_sources_profile_script.py`; vollständiger
  Offline-Backend-Lauf: `1195 passed, 29 skipped`. Der frühere ungekürzte Gesamtlauf
  hatte acht reine Netzwerk-Integrationstests mit DNS-Fehlern bei justETF,
  OpenFIGI und Yahoo; 1194 weitere Tests bestanden.
- `bash -n`, ShellCheck, Ruff Check/Format und `git diff --check` bestanden.

**Doku-Abgleich:** README-Abschnitte Docker und Unraid beschreiben die beiden
Pfade, den Startzeitpunkt und die fehlende Migration. `docs/plugins.md`
verweist aus der Profilauswahl auf diese Anleitung; der Makefile-Kommentar
nennt den gemeinsamen Standard. Die historischen Entwürfe unter
`docs/superpowers/` bleiben unverändert.

**Lessons:** SI-CX-01: neues, vorher nicht vorhandenes Docker-Volume statt
Reststand; SI-R-02: keine hypothetische Migration; SI-T-66: Befund und
Schwere getrennt, kein Eingriff in den laufenden Container.

## Auflösung

**Unabhängiger Review · Claude, 2026-09-25.** Geprüfte Übergabe
`aaf48fdea642bc6f1c6b134f981d1426f6f813fb`, geheilte Endfassung
`1e18ac8` (siehe Selbstheilung unten). Ergebnis: **approved**.

**Eigenständig nachvollzogen, nicht nur die Coder-Angaben übernommen**
(SI-CX-01):

- Ein frisches, zuvor nie existierendes Docker-Volume
  (`stockinfo-t71-verify-20260925154229`) angelegt, `--yaml --target docker`
  und danach `--online --target docker` real ausgeführt. `--show --target
  docker` las exakt den zuletzt geschriebenen Stand, Sicherung lag unter
  `sources.yaml.bak.*`. Volume danach entfernt.
- **#4 von ◑ auf ✅ geschlossen:** `STOCKINFO_IMAGE` auf einen garantiert
  nicht vorhandenen Tag gesetzt und mit `--pull=never` gegen den echten
  Docker-Daemon laufen lassen. Erwartetes Verhalten bestätigt: Exit 1,
  `"... nicht geändert"` auf stderr, Volume-Inhalt unverändert. Mikes lokale
  Images dafür nicht angerührt.
- `tests/test_sources_profile_script.py` auf frischem `DATABASE_PATH`:
  20 grün. Voller Offline-Backend-Lauf (`-m "not integration"`) auf frischem
  `DATABASE_PATH`: **1195 passed, 29 skipped, 8 deselected** — deckt sich
  exakt mit der Coder-Angabe.
- `bash -n`, ShellCheck, Ruff Check/Format, `git diff --check` erneut
  gelaufen: grün. Die einzige ShellCheck-Meldung (SC1091 zu den
  BashLib-Includes) besteht nachweislich unverändert bereits vor diesem
  Commit — kein neuer Befund.
- DRY-Scope wiederholt: `mangolila/stockinfo` und `stockinfo-data` stehen
  bewusst zweifach (Makefile, Skript-Vorgabe); der neue
  `test_docker_vorgaben_passen_zu_make_up` ist das Drift-Orakel dafür. Keine
  doppelte Kopier-/Backup-Logik gefunden.
- Scope-Vertrag-Abrechnung nachgerechnet: 2 Produktdateien, 5 Begleitdateien
  (README, `docs/plugins.md`, Makefile, Test, Ticket — Ticket zählt
  üblicherweise nicht mit, macht die gemeldeten „vier" korrekt), 606
  Diff-Zeilen laut `git show --stat` — stimmt mit der OUTBOX überein.

**Selbstheilung (mechanisch, Verifier-Riegel):** Die neue
`-v | --volume NAME`-Zeile im Skriptkopf war um ein Zeichen zu kurz
gepolstert und brach die feste Spaltenausrichtung der CLI-Konvention.
Reine Whitespace-Korrektur in Commit `1e18ac8`
(`style(review): Spaltenausrichtung der neuen --volume-Hilfe korrigieren`).
Danach erneut `bash -n`, ShellCheck (identische, vorbestehende SC1091-Notiz)
und die 20 Skripttests gelaufen — alle grün. `handoff_commit` ist deshalb
`1e18ac8`, nicht mehr `aaf48fd`.

**Nicht blockierender Restbefund für ein späteres Kleinticket:** Bei
`--yaml`/`--online --target docker` auf einem bereits belegten benannten
Volume landet die Sicherungsmeldung des Python-Helfers unformatiert und
ungefärbt auf stdout (`backup:/data/sources.yaml.bak.xxxxx`, mit
container-internem Pfad) — inkonsistent zur sonst überall eingehaltenen
ANSI-Konvention (✓/ℹ/Farbe) und zur äquivalenten lokalen Meldung aus
`backupConfig()`. Live reproduziert bei Schritt 2 der eigenen Docker-Probe
oben. Kein Funktionsfehler — die Sicherung selbst ist korrekt und vollständig
—, nur Ausgabe-Politur. Keine rein mechanische Ersetzung (Entscheidung nötig:
Helfer-Ausgabe abfangen und im Bash-Stil neu formatieren oder der Helfer
schweigt und Bash meldet selbst), deshalb hier nur benannt statt
selbstgeheilt. Verhindert die Freigabe nicht (belegter Schaden: kosmetisch,
Ein-Personen-Betrieb).

**Standards-Gegenprüfung:** Coder-Tabelle unabhängig nachvollzogen, keine
Abweichung außer der oben genannten Selbstheilung. Identifikatoren in
`scripts/sources-profile-volume.py` und den geänderten Bash-Funktionen
durchgehend englisch; deutsche Testnamen sind die vorgesehene Ausnahme.

Scope-Vertrag eingehalten, keine Nicht-Ziele verletzt (keine automatische
Migration, kein Eingriff in einen laufenden Container, keine neue
Abhängigkeit — der Python-Helfer nutzt nur die Standardbibliothek).

**Abschlussbestätigung · Mike, 2026-09-25:** „Schiebe es ins done" — Ticket
nach `40-done/` verschoben. Der nicht blockierende Restbefund zur
Sicherungsmeldung ist bewusst offen; er braucht ein eigenes Kleinticket,
sobald das ansteht.
