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
| 4 | Fehlerpfade | Fehlendes Image, fehlender Docker-Zugriff und kollidierende eigene Fachdatei ändern `sources.yaml` nicht | ◑ |
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

Coder-Umsetzung und technische Eigenprüfung stehen. Unabhängiger Review und
Abschlussurteil sind offen.
