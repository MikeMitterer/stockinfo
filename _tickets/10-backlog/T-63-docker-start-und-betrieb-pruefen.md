# T-63 · Docker-Start und Betrieb prüfen

StockInfo soll **auch als fertiger Container zuverlässig laufen**.

Ein erfolgreicher lokaler Entwicklungsstart belegt noch nicht, dass das
Docker-Image mit eigener Konfiguration startet und gespeicherte Daten behält.

Beispiel: Der Container wird mit demselben Datenverzeichnis neu erstellt.
Die zuvor aufgenommenen Instrumente und ihre Werte sollen weiterhin da sein.
Auch das gebaute Dashboard muss ohne Entwicklungsserver erreichbar sein.

Der fehlende Docker-Nachweis aus
[T-16](../40-done/T-16-review-fixes-und-etf-quellen-testen.md) wird hier nachgeholt.
Die technischen Tests wurden am 2026-09-25 mit eigenen Containern, Volumes
und Konfigurationen ausgeführt. Die laufende Arbeitsinstanz blieb unberührt.

## Für dich

Für die lokale Docker-Prüfung ist kein Handgriff nötig. Der Test ist
reproduzierbar; die Abschlussentscheidung im Ticketboard steht noch aus.

### Bisheriger Auftrag

Mike, 2026-09-07: „Kennzeichne es als erledigt - erstelle ein eigenes Ticket für die Docker-Tests“.
[T-16](../40-done/T-16-review-fixes-und-etf-quellen-testen.md) ist damit abgeschlossen;
dessen fehlender Docker-Nachweis wird nicht als bestanden übernommen.
Mike beauftragte am 2026-09-25 die Punkte 1–5 der Docker-Veröffentlichung und
damit auch diesen Nachweis.

## Umsetzung und technische Nachweise

| Repo | Time-box | Scope | GH-Issue |
|---|---|---|---|
| StockInfo | 1–2 h | Lokale Container-Verifikation, keine Produktänderung | — |

### Voraussetzungen und Ablauf

Docker muss erreichbar sein. Den vorhandenen lokalen Buildweg verwenden,
Image-Tag, Commit, Architektur und sämtliche ausgeführten Befehle im Nachweis
festhalten. Eigenen Containernamen, freien Port sowie ein temporäres
Datenverzeichnis verwenden. Das Dateiprofil aus `examples/` und das YAML-Plugin
in die Testumgebung kopieren. Keine laufende Instanz voraussetzen.

### Verify

Alle Zeilen liefen ausschließlich in der isolierten Docker-Testumgebung.

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | Image über den bestehenden lokalen Buildweg bauen | Build erfolgreich; Image-ID, Architektur und Commit festgehalten | ✅ |
| 2 | Container mit frischem Volume und eigener `--env-file` starten | Gültiges `STRICT_EXCHANGE=false` akzeptiert | ✅ |
| 3 | Start mit separater Env-Datei und nachgestelltem Leerraum am booleschen Wert wiederholen | Erwarteter `ValidationError`; Env-Werte dürfen keinen solchen Leerraum enthalten | ✅ |
| 4 | `/health`, `/ready`, `/fields` und Dashboard über den veröffentlichten Testport abrufen | Dienst bereit; Feldkatalog und gebaute UI ohne Vite erreichbar | ✅ |
| 5 | Instrument aus der kopierten YAML-Vorlage per REST aufnehmen und abrufen | Identität, Kurs und Detailwerte entsprechen der Vorlage | ✅ |
| 6 | Eigenen Container entfernen und mit demselben Testvolume neu erstellen | Instrument und gespeicherte Werte bleiben erhalten | ✅ |
| 7 | Eigene Ressourcen aufräumen und Produktionsdaten vergleichen | Testressourcen beendet; Produktions-DB unverändert | ✅ |

Der Test liegt in [T-63-smoke.sh](T-63-smoke.sh) und verwendet für jeden Lauf
eigene Docker-Volumes, Containernamen und einen freien Loopback-Port:

```bash
make build
bash _tickets/10-backlog/T-63-smoke.sh
```

Der Test schreibt das YAML-Profil vor dem App-Start in sein frisches Volume,
ruft die drei Endpunkte und das Dashboard ab, nimmt `IE00B4L5Y983` per
`POST /instruments/intake` auf und prüft Preis `128.21`, Anbieter `iShares`
und TER `0.2`. Nach Neuerstellung liest er den Datensatz aus derselben
Datenbank. Er prüft außerdem den laufenden Prozess mit UID 99/GID 100, den
Docker-Status `healthy` und den erwarteten Fehler bei einer ungültigen
Env-Datei. Bei jedem Ausgang räumt er ausschließlich seine Ressourcen auf.

**Lauf vom 2026-09-25:** `make build` in einem sauberen Release-Worktree auf
Commit `bb99413` erzeugte `mangolila/stockinfo:0.6.0-260925.1326.bb994.ahead1103`
mit Image-ID `sha256:5abdb69087f0e8e3fcf020f010f282ec68ee937296c3c8b0b96271761358183f`
für `linux/amd64`. Der vollständige Smoke-Lauf endete mit Exit-Code 0.
Die Arbeitsdatenbank `data/stockinfo.db` hatte vor und nach einem zusätzlichen
Lauf denselben SHA-256-Wert
`f5ca9afdf809f7a9e0fd28d806a84849a904aea44bf3d89a06e0739d6eaaa7b4`.
Produktive Pfade und der Containername `stockinfo` wurden nicht verwendet.

**Wiederholung nach Build-Automatisierung:** `make build` auf Commit `768f312`
erzeugte `mangolila/stockinfo:0.6.0-260925.1423.768f3.ahead1105` für
`linux/amd64` mit Image-ID
`sha256:cbe17ec616dbc2317e2375875f478adcf60b6859466abeb4b05101a2940659ab`.
Der Build prüfte die drei mitkopierten Lizenztexte gegen das Repository, die
Architektur und die OCI-Labels. Der Smoke-Lauf mit genau diesem `IMAGE_REF`
endete mit Exit-Code 0: Kurs 128.21, Anbieter iShares und TER 0.2 waren auch
nach der Container-Neuerstellung vorhanden; beide App-Prozesse liefen mit
UID 99/GID 100. Der ungültige Env-Wert führte zum erwarteten `ValidationError`.
Das Skript entfernt Container anhand der von Docker geschriebenen IDs, nicht
anhand bloß vorhergesagter Namen.

**Doku-Abgleich:** README „Docker“ erklärt den automatischen Lizenztransport,
die Build-Prüfung und den Push-Nachweis. Die historische Deployment-Spec unter
`docs/superpowers/` bleibt als Entwurf unverändert.

### Side-Effects

Nur lokale Testimages, eigener Container und temporäre Daten. Kein Registry-Push,
Deployment oder Release. Bestehenden Container `stockinfo`, Betriebskonfiguration
und Produktionsdaten nicht verändern. Kein neues Makefile-Target.
Ein optionales Smoke-Skript gehört neben dieses Ticket; vorher vorhandene
Prüfwerkzeuge auf Wiederverwendung prüfen.

### Auflösung

Die technische Docker-Prüfung ist durchgeführt. Der absichtlich ungültige
Env-Wert bleibt ein dokumentierter Fehlerfall; die aktuelle `.env.example`
stellt Kommentare über die Werte und enthält keinen nachgestellten Kommentar.
Eine menschliche Abschlussbestätigung für den Ticketordner liegt nicht vor.
