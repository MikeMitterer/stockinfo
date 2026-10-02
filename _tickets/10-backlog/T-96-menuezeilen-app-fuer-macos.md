# T-96 · Menüzeilen-App für macOS

**Warum dieses Ticket:** StockInfo läuft auf dem Mac bisher nur über
`make dev-up` aus dem Projekt oder als Docker-Container. Für den Alltag fehlt
ein einfacher Weg, den Dienst im Hintergrund laufen zu lassen und schnell zu
erreichen. Vorbild ist Syncthing: eine kleine App in der Menüzeile startet den
Dienst und öffnet bei Bedarf dessen Weboberfläche.

**Beispiel:** Nach dem Anmelden erscheint ein StockInfo-Symbol in der
Menüzeile. Ein Klick zeigt den Status („läuft“) und öffnet das Dashboard; das
Menü bietet „Datenordner öffnen“, „Logs“, „Neu starten“ und „Beenden“. Ein
Terminal ist dafür nicht nötig.

**Stand:** Idee und Technikwahl, noch nicht eingeplant. Angelegt am
2026-10-02 auf Mikes Auftrag („Die Idee wären schlussendlich 2 Apps.
StockInfo in der Menüzeile und StockPortfolio mit App-Hülle“). Das
Gegenstück ist StockPortfolio T-80 (App-Hülle mit Fenster).

Für Mike steht kein Handgriff an.

## Umsetzung und technische Nachweise

| Repo | Time-box | Scope | GH-Issue |
|---|---|---|---|
| StockInfo | Prototyp 1–2 Tage | neue Mac-Hülle; App und API unverändert | — |

### Kontext / Ziel

**Technik: Deno Desktop** (`deno desktop`, ab Deno 2.9; 2.9 ist die aktuelle
LTS-Linie, gepflegt bis 2027-01-31). Gewählt nach Mikes Versionsregel in
`code-standards` und weil TypeScript bevorzugt ist. Verworfen: `rumps`
(letzte Version 2022), `pystray` (2023), Electron (zu schwer für ein
Menüsymbol). Ersatz, falls Deno Desktop nicht trägt: Swift mit
`MenuBarExtra`.

- `Deno.Tray` für das Menüzeilen-Symbol mit Template-Icon (hell/dunkel),
  `Deno.dock.setVisible(false)` für eine App ohne Dock-Symbol.
- Optional ein Panel am Symbol mit dem Dashboard (`http://127.0.0.1:<port>/`).
- `Deno.Command` startet StockInfo (uvicorn, `app.main`) als Kindprozess und
  beendet es mit der App.
- Daten unter `~/Library/Application Support/StockInfo/` über
  `DATABASE_PATH`, Logs unter `~/Library/Logs/StockInfo/`. Die Pfade je
  System über eine Funktion ermitteln, nicht fest im Code: Deno Desktop
  unterstützt auch Windows und Linux, das ist für später mitgedacht.

**Reihenfolge:** zuerst Prototyp gegen die vorhandene Projekt-venv (Menü,
Start/Stop, Status, Panel). Eigenständige `.app`, mitgeliefertes
StockInfo-Programm (etwa PyInstaller), Signatur, Notarisierung und Autostart
erst, wenn der Prototyp sich bewährt hat.

### Windows später (Ausblick, nicht Teil dieses Tickets)

`deno desktop` baut auch für Windows; `Deno.Tray` landet dort im
Infobereich der Taskleiste. Die Hürde ist StockInfo selbst: Es braucht ein
Python, und `app/plugin_env.py` installiert Plugins zur Laufzeit mit
`sys.executable -m pip`. Abwägung (Mike und claude-observer, 2026-10-02):

| Weg | Plugins | Zusatz auf dem Rechner | Einordnung |
|---|---|---|---|
| **App-Ordner mit `uv`** | ✓, venv mit `--seed` oder `uv pip install` | keiner | **bevorzugt** |
| Docker Desktop oder WSL mit Docker Engine | ✓ | Docker, gegebenenfalls WSL | Alternative; nutzt das geprüfte Unraid-Image |
| WSL mit venv | ✓ | WSL, venv | möglich, Einrichtung auf dem Zielrechner |
| PyInstaller | ✗ | keiner | **verworfen**: `sys.executable` ist die `.exe`, pip fehlt |

**Bevorzugter Weg:** `uv.exe` liegt im App-Ordner. Beim ersten Start legt
`uv sync` mit Lockfile eine venv unter `%LOCALAPPDATA%\StockInfo\` an und
lädt ein verschiebbares Python (python-build-standalone). Zu beachten: `uv
venv` legt standardmäßig kein pip an; ohne `--seed` oder eine Umstellung auf
`uv pip install` scheitert die Plugin-Installation. Der erste Start braucht
Netz; native Pakete brauchen Windows-Wheels. Daten nie im App-Ordner, der
unter `Program Files` schreibgeschützt sein kann. Derselbe Weg löst später
auch eine eigenständige Mac-`.app`.

### Offene Fragen vor der Aktivierung

- Fester Port der Menüzeilen-App und Verhalten bei belegtem Port.
- Signatur und Notarisierung: in der Deno-Desktop-Doku nachlesen, sobald eine
  weitergegebene `.app` nötig ist.
- Mehrsprachigkeit des Menüs nach i18n-Hausstandard.

### Akzeptanzkriterien

- [ ] Ein Menüzeilen-Symbol startet StockInfo und zeigt den Status.
- [ ] Das Menü öffnet das Dashboard, den Datenordner und die Logs.
- [ ] Beenden stoppt den eigenen StockInfo-Prozess, keinen fremden.
- [ ] Ein belegter Port führt zu einer verständlichen Meldung.
- [ ] Die Arbeitsdatenbank des Projekts (`data/`) wird nicht verwendet.
- [ ] `README.md` und `docker/README.md` sind abgeglichen: Die Mac-App ist
      ein dritter Betriebsweg neben Entwicklung und Container.

### Side-Effects

Neuer Betriebsweg mit eigenem Datenort. Docker und Unraid bleiben unverändert.
StockPortfolio T-80 nutzt diesen Dienst über dessen Health-Check.
