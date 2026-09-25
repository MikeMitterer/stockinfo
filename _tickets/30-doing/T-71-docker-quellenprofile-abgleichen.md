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

Der Coder setzt die Korrektur um. Danach prüft der unabhängige Verifier die
Übergabe. Bis dahin bleibt der bisherige Aufruf mit ausdrücklich genanntem
Host-Verzeichnis für Unraid verfügbar.

## Verify

| # | Prüfung | Erwartung | AI |
|---|---|---|:--:|
| 1 | `--yaml --target docker` vor dem App-Start | Schreibt `sources.yaml` und Fachdatei ins benannte Volume `stockinfo-data`; alter Stand gesichert | ➖ |
| 2 | `--online --target docker` | Online-Ketten mit YAML-Fallback; vorhandene Fachdaten bleiben erhalten | ➖ |
| 3 | `--target docker --data-dir DIR` | Schreibt weiter nur in den angegebenen Host-Mount; kein Docker-Daemon nötig | ➖ |
| 4 | Fehlerpfade | Fehlendes Image, fehlender Docker-Zugriff und kollidierende eigene Fachdatei ändern `sources.yaml` nicht | ➖ |
| 5 | Startvertrag und Doku | Skriptvorgabe passt zu `make up`; Unraid-Aufruf nennt den Host-Mount ausdrücklich | ➖ |

## Auflösung

Offen. Technischer Nachweis und unabhängiger Review folgen.
