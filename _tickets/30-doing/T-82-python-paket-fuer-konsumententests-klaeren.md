# T-82 · Python-Paket für StockPortfolio-Tests einbinden

StockPortfolios lokales Skript `scripts/stockinfo-test-server.py` wird mit
StockInfos Python-Umgebung gestartet. Für die einheitliche CLI-Hilfe und
Farbausgabe soll es `projecttools.ui.colors` aus dem paketierbaren
ProjectTools-Python-Teil nutzen können. Diese Bibliothek ist derzeit nicht
als Abhängigkeit der StockInfo-Umgebung deklariert. Ein bloßer
`sys.path`-Eingriff oder ein absoluter Rechnerpfad würde den Aufruf an
eine lokale Verzeichnisstruktur binden.

**Auswirkung für den Konsumenten:** Ohne geklärten Installationsweg kann
StockPortfolio das Skript nicht zuverlässig auf anderen Rechnern mit der
gemeinsamen CLI-Darstellung starten. Der bestehende Teststack und StockInfos
Produkt-API sollen davon unberührt bleiben.

**Stand:** Aktiviert von Mike am 2026-10-01, Coder `claude`, Verifier
`codex`. Die Paketstruktur liegt bereits in ProjectTools
(`mmit-projecttools`, `pyproject.toml` im Repo-Root).

**Vorgabe Mike, 2026-10-01:** „Zu T-82 kannst du dir das Makefile in
StockPortfolio ansehen - das erstellt mit setup das .venv. requirements.txt
kannst du im ProjectRoot ablegen - im Prizip gleich wie bei StockPortfolio.
Schau dass das Projekt eigenständig bleibt. Zieh nicht selbständig
iregendwelche Querverweise zu StockPortfolio“.

## Entscheidung

`make setup` richtet die Entwicklungsumgebung ein: `.libs`-Links per
`scripts/setup-libs.sh` (Hausvorlage), `.venv` mit Python 3.11+, Pakete
aus `requirements-dev.txt`, Dashboard-Pakete per `npm ci`. Das Paket
kommt als `-e ./.libs/ProjectTools` in **`requirements-dev.txt`** im
Projekt-Root.

Warum nicht `requirements.txt`: In StockInfo beschreibt diese Datei die
Laufzeit der App. Der Docker-Build installiert sie, und im Image gibt es
`.libs/` nicht; der Build bräche ab. `requirements-dev.txt` bindet
`requirements.txt` ohnehin ein und ist die Datei, die die Anleitung für die
Entwicklungsumgebung schon nennt.

Grenze: Der Weg setzt die ProjectTools-Quelle auf dem Rechner voraus
(`PROJECT_TOOLS` oder vorhandener Link). Ohne sie bricht `make setup` mit
der Meldung von `setup-libs.sh` ab. Produkt, API und Image bleiben unberührt.

## Scope-Vertrag

- **Ergebnis:** Nach `make setup` in einem frischen Checkout ist
  `projecttools.ui.colors` mit `.venv/bin/python` importierbar, ohne
  Rechnerpfad und ohne `sys.path`-Eingriff.
- **Fachliche Änderungen (2):** `setup`-Target samt `scripts/setup-libs.sh`;
  ProjectTools-Eintrag in `requirements-dev.txt`.
- **Dateien:** `Makefile`, `requirements-dev.txt`, `scripts/setup-libs.sh`
  (neu), `README.md` (Quick start); dieses Ticket.
- **Budget:** 4 Projektdateien, 1 Ticketdatei, 250 Diff-Zeilen.
- **Nicht-Ziele:** keine Änderung an App, Image, `requirements.txt`, Tests
  der App; keine Verweise auf andere Projekte in Code oder Anleitungen;
  kein Eingriff in fremde venvs.

## Klärung und technische Nachweise

| Repo | Time-box | Scope | GH-Issue |
|---|---|---|---|
| StockInfo | 1–2 h | Python-Umgebung für den lokalen StockPortfolio-Testaufruf | — |

Prüfen, ob StockInfos bestehende Projekt-venv die richtige Umgebung für
dieses Konsumentenwerkzeug ist und wie das ProjectTools-Paket dort
reproduzierbar verfügbar wird. Dabei den lokalen Entwicklungsweg, frische
Checkouts und den Aufruf aus StockPortfolio betrachten. Einen anderen
Installationsweg nur wählen, wenn er den gleichen maschinenunabhängigen
Aufruf ermöglicht. Die Entscheidung und ihre Grenze im Ticket begründen.

### Verify

Legende: ✅ bestätigt, ➖ noch keine Live-Verifikation.

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | In einer frischen StockInfo-Umgebung den dokumentierten Installationsweg ausführen | `projecttools.ui.colors` ist ohne absoluten Rechnerpfad und ohne `sys.path`-Änderung importierbar | ✅ |
| 2 | StockPortfolios Testskript mit der vorgesehenen Python-Umgebung und `--help` starten | Hilfe erscheint ohne laufenden Dienst und ohne Seiteneffekte | ✅ |
| 3 | Den Teststack nach der gewählten Einbindung starten, Status prüfen und stoppen | StockInfo und StockPortfolio bleiben über den dokumentierten Aufruf erreichbar; fremde Prozesse und Daten bleiben unangetastet | ✅ |
| 4 | StockInfos bestehende Tests und die betroffenen Entwickleranleitungen prüfen | Keine Regression; Installationsschritte und Zuständigkeit sind nachvollziehbar | ✅ |

**Belege (Claude, 2026-10-01):**

1. Lokaler Link `.libs/ProjectTools` entfernt (nicht versioniert), dann
   `make setup VENV=<scratchpad>/fresh-venv`. `setup-libs.sh` legt den Link
   neu an und meldet „✓ Setup fertig“; `import projecttools.ui.colors` mit
   `mmit-projecttools 0.1.0` gelingt. Der Pfad in `sys.path` stammt aus pips
   editierbarer Installation, nicht aus Projektcode. `make setup` im Root
   lief ebenfalls zweimal hintereinander durch (idempotent).
2. `<StockInfo>/.venv/bin/python scripts/stockinfo-test-server.py --help`
   im Konsumentenprojekt: Hilfe mit gemeinsamem Theme, Exit 0, kein Dienst
   gestartet; `cli_theme.has_theme()` ist `True`.
3. Dasselbe Skript mit `--run --port 18083` (StockInfo-Testserver, temporäre
   DB): `/ready` 200, `--status` nennt die eigene PID, `--stop` beendet nur
   diese; danach keine Antwort mehr auf 18083. Mikes laufendes Backend auf
   Port 8000 blieb unberührt. `--stack` lief nicht; er gehört zum
   Konsumentenprojekt und verwendet dessen eigene Umgebung.
4. `make test`: Backend 1245 bestanden / 35 übersprungen, Plugin-API 323,
   Beispiel-Plugin 50, Dashboard 52 Dateien / 389 Tests samt ESLint;
   `npm run build` erfolgreich, auch nach `npm ci` mit den von npm
   gemeldeten blockierten Installationsskripten. `shellcheck` ohne Befund;
   `setup-libs.sh` ohne Argument und mit `--info` Exit 0.

**Hausvorlage veraltet:** `makefile-conventions/setup-libs.sh` prüft noch
`ProjectTools/src/python/colors.py`. Seit dem Paketumbau liegt die Datei
unter `src/python/projecttools/ui/colors.py`. StockInfos Kopie ist
korrigiert; die Vorlage im Skill bleibt eine offene Übernahme für die
gemeinsamen Skills, auf Mikes Auftrag.

### Akzeptanzkriterien

- [x] Der für StockInfo gewählte Installationsweg ist begründet und reproduzierbar.
- [x] StockPortfolios Skript kann die gemeinsame CLI-Darstellung über den Paketimport nutzen, ohne Rechnerpfad im Code.
- [x] Hilfe und Teststack funktionieren auf dem dokumentierten Entwicklungsweg.
- [x] Betroffene Anleitungen in beiden Repositories sind auf Konsistenz geprüft; nötige Anpassungen sind dokumentiert.

### Doku-Abgleich

- `README.md` → Requirements und Quick start: `make setup` statt der
  Handbefehle; `.libs`, Umgebungsvariablen, `PYTHON_BOOTSTRAP` und der
  Hinweis, dass das Image nichts davon braucht.
- `make hints`: Zeile „Erster Start“ (`make setup` → Konfiguration
  anlegen → `make dev`).
- `docker/README.md` und `unraid/README.md`: unverändert; sie beschreiben
  den Container, der weder `.libs` noch `requirements-dev.txt` verwendet.
- Keine neuen Verweise auf andere Projekte in Code oder Anleitungen
  (Vorgabe Mike). Die Anleitung des Konsumentenprojekts nennt bereits
  StockInfos `.venv/bin/python`; dort ist nichts zu ändern.

### Side-Effects

Kein Eingriff in StockInfos Kurs- oder API-Vertrag. Keine globale
Python-Installation und keine automatische Änderung fremder Projekt-venvs.
ProjectTools bleibt ein eigenes Repository mit eigenem Commit.

### Auflösung

Umgesetzt auf `t-82-python-paket-konsumententests`; Übergabe an Verifier
`codex`.
