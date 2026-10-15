# T-102 · Doku-Prüfung mit docs-check nach dem StockPortfolio-Schema

StockInfo soll seine Nutzerdoku bei jedem `make test` und vor jedem Commit
gegen das Projekt prüfen, so wie StockPortfolio es seit Oktober 2026 tut. Das
Werkzeug dafür ist `docs-check.sh` aus ProjectTools; es liegt über
`.libs/ProjectTools` schon im Projekt, wird aber nicht genutzt.

**Beispiel:** Ein Make-Target wird umbenannt, `README.md` nennt noch den alten
Namen. Heute fällt das erst auf, wenn jemand das README liest. Mit
`docs-check` scheitert `make test` mit Zeile, gefundenem Namen und Rat. Ebenso
fallen tote Links und Anker auf, Umgebungsvariablen, die der Code liest, aber
keine Doku nennt, eine Docker-Hub-Vorschau, die nicht zu `docker/README.md`
passt, und Screenshots, deren Oberfläche sich seit der Aufnahme geändert hat.

**Stand:** Angelegt am 2026-10-15 auf Mikes Auftrag aus der
StockPortfolio-Sitzung („Leg in StockInfo als ein Ticket nach doing dass dort
nach dem Schema von StockPortfolio docs-check nachgezogen wird inkl.
passendem config-File, Makefile-Target, README.template.md usw.“). In
`30-doing/` aktiviert, Coder `claude`, Verifier `codex`. Umsetzung auf
`t-102-docs-check` begonnen (2026-10-15); Scope-Vertrag unten.

## Ausgangslage

| Baustein | StockPortfolio (Vorbild) | StockInfo heute |
|---|---|---|
| Config | `.docs-check.conf.sh` in fünf Abschnitten | fehlt |
| Make-Target | `make docs-check`, Teil von `make test` | fehlt |
| Pre-Commit-Hook | `.githooks/pre-commit`, aktiviert durch `make setup` (`core.hooksPath`) | fehlt |
| README-Vorlage | `docs/README.template.md` für den Skill `readme-conventions` | fehlt |
| Zweisprachiges README | `README.md` englisch, `README.de.md` deutsch, gegenseitig verlinkt | nur `README.md` |
| Docker-Hub-Vorschau | `docker/preview/README.md` versioniert, `DEPENDS` mit Frist 0 | von git ignoriert |
| Screenshots | `SCREENSHOTS` gegen den UI-Code, Quittung mit `--ack` | `unraid/screenshots/*.png` ungeprüft |
| Projektregel | `AGENTS.md` beschreibt Prüfung, Abhängigkeiten und Quittung | fehlt |

Vorlagen zum Nachlesen, alle in StockPortfolio:

- [`.docs-check.conf.sh`](/Volumes/DevLocal/DevWeb/Production/StockPortfolio/.docs-check.conf.sh)
- [`docs/README.template.md`](/Volumes/DevLocal/DevWeb/Production/StockPortfolio/docs/README.template.md)
- [`.githooks/pre-commit`](/Volumes/DevLocal/DevWeb/Production/StockPortfolio/.githooks/pre-commit)
- `Makefile`: Targets `docs-check`, `test` und `setup`
- `AGENTS.md`, Abschnitt „Dokumentation gehört zur Änderung“
- `docs/development.md`, Abschnitt zu `make docs-check`

Werkzeug und Config-Format: [ProjectTools-README, `docs-check.sh`](/Volumes/DevLocal/DevBash/Production/ProjectTools/README.md).
`docs-check.sh --example` erzeugt eine Starter-Config mit Vorschlägen aus
diesem Projekt.

## Scope-Vertrag

**Beobachtbares Ergebnis:** `make docs-check` prüft StockInfos Nutzerdoku,
läuft in `make test`, `make check` und vor jedem Commit und meldet auf dem
übergebenen Stand keine Probleme.

**Fachliche Änderungen (drei):**

1. Prüfung einrichten: `.docs-check.conf.sh`, Make-Target, Pre-Commit-Hook,
   `make setup`, versionierte Docker-Hub-Vorschau.
2. README-Aufbau festlegen: `docs/README.template.md`, `README.de.md`,
   Sprachlinks in `README.md`.
3. Regeln und Befunde: `AGENTS.md`-Abschnitt, Befunde der ersten Prüfung
   in den betroffenen Dokumenten beheben, begründete Quittungen.

**Erwartete Dateien:**

| Art | Dateien | Budget |
|---|---|---|
| Produkt (Build/Werkzeug) | `Makefile`, `.gitignore`, `.githooks/pre-commit`, `.docs-check.conf.sh`, `.docs-check.ack` | 5 |
| Doku | `README.md`, `README.de.md`, `docs/README.template.md`, `docker/preview/README.md`, `AGENTS.md`, Befundkorrekturen in bis zu 5 weiteren Dokumenten | 10 |
| Tests | keine neuen Testdateien; Nachweis über die Gegenproben der Verify-Matrix | 0 |

**Diff-Budget:** etwa 1.600 Zeilen. Davon sind rund 640 die Übersetzung
`README.de.md` und rund 230 die erzeugte Vorschau; Config, Vorlage, Hook,
Makefile und Regeln zusammen etwa 500, Befundkorrekturen bis 200. Das
liegt über der 800-Zeilen-Grenze. Deshalb geht der Stand **vor**
`README.de.md` als `scope_checkpoint` an den Verifier; die Übersetzung
folgt erst nach dessen Entscheidung.

**Nicht-Ziele:** ProjectTools ändern; Screenshot-Werkzeug aus StockPortfolio
T-95; zentrale Unraid-Vorlage im Templates-Repo; neue Screenshots
aufnehmen (geprüft wird, ob die vorhandenen noch stimmen); Push oder
Docker-Hub-Update.

## Umsetzung und technische Nachweise

| Repo | Time-box | Scope | GH-Issue |
|---|---|---|---|
| StockInfo | 1 Tag | Config, Makefile, Hook, README-Vorlage, `README.de.md`, Vorschau, AGENTS.md, Befunde der ersten Prüfung | — |

1. **Config.** `.docs-check.conf.sh` aus `docs-check.sh --example` anlegen und
   für StockInfo füllen, in derselben Gliederung wie StockPortfolio:
   - **Dokumente:** `DOCS` mit den nutzersichtbaren Anleitungen (`README.md`,
     `README.de.md`, `docker/README.md`, `unraid/README.md`, `docs/`,
     `LICENSING.md`, `contract/README.md` und weitere nach Inventar),
     `LINKS_ONLY` für `AGENTS.md` und `CLAUDE.md`, `EXCLUDE` für Entwürfe wie
     `docs/superpowers`.
   - **Inhalt:** `FORBIDDEN` für Begriffe, die laut StockInfos `AGENTS.md`
     nicht in Nutzerdoku gehören, `MAX_ALERTS`.
   - **Variablen:** `KNOWN_VARIABLES`, `CODE_VARIABLES` für `app/`,
     `plugin_api/src`, `dashboard/src` und Skripte, `INTERNAL_VARIABLES` mit
     Grund.
   - **Pflichtdateien:** `REQUIRED` nach Datei- und Überschrifteninventar.
   - **Abhängigkeiten:** `SCREENSHOTS` für `unraid/screenshots/*.png` gegen den
     UI-Code, den sie zeigen (Dashboard, für `swagger.png` die API); `DEPENDS`
     für die Docker-Hub-Vorschau (Frist 0), `README.de.md` und die
     Lizenzabschnitte aus `LICENSING.md`; `DEPENDS_HINT` für
     `README.md` → `docker/README.md`.
   - Die Erklärung zur Quittung mit `--ack` steht wie in StockPortfolio vor
     `SCREENSHOTS`.
2. **Makefile.** Target `docs-check`; `test` und `check` hängen davon ab. Fehlt
   ProjectTools, meldet das Target das und bricht nicht den ganzen Lauf ab
   (Verhalten wie in StockPortfolio). `make setup` setzt
   `core.hooksPath .githooks`. `make help` zeigt das Target.
3. **Pre-Commit-Hook.** `.githooks/pre-commit` ruft `make docs-check` auf,
   bricht den Commit bei Problemen ab, lässt Hinweise durch.
4. **README-Vorlage.** `docs/README.template.md` für StockInfo: Abschnitte,
   Reihenfolge, Bilder und Quellen nach dem heutigen README und StockInfos
   Aufbau (Dienst mit API, Dashboard, Plugins, Vertrag). Englisches
   `README.md` und deutsches `README.de.md`, im Kopf gegenseitig verlinkt.
   Wohin Entwicklerdetails gehören, legt die Vorlage fest.
5. **`README.de.md`** nach der Vorlage anlegen; `README.md` an die Vorlage
   angleichen, soweit die Prüfung oder die Vorlage es verlangt.
6. **Docker-Hub-Vorschau versionieren.** `docker/preview/` aus `.gitignore`
   nehmen, Vorschau mit dem ProjectTools-Helfer erzeugen und einchecken.
7. **Projektregeln.** StockInfos `AGENTS.md` beschreibt die Prüfung, die
   Abhängigkeiten, dass die Vorschau in denselben Commit wie
   `docker/README.md` gehört, und die Quittung; Doku-Abgleich in den
   Entwickleranleitungen.
8. **Erste Befunde.** Alle Probleme der ersten Prüfung beheben. Hinweise, die
   nach Prüfung nichts verlangen, mit `docs-check.sh --ack` quittieren und
   `.docs-check.ack` mitcommitten; nichts ungesehen quittieren.

### Verify

Legende: ➖ noch keine Live-Verifikation.

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | `make docs-check` im Projekt-Root | Ergebniszeile ohne Probleme; jeder verbliebene Hinweis ist im Ticket begründet | ➖ |
| 2 | Gegenprobe: im README ein nicht vorhandenes Make-Target nennen, `make docs-check` | Problem mit Zeile und Target; danach zurücksetzen | ➖ |
| 3 | Gegenprobe: `docker/README.md` ändern, ohne die Vorschau neu zu erzeugen | Problem „gehört in denselben Commit“; danach zurücksetzen | ➖ |
| 4 | `make setup`, dann ein Commit mit Problem | Hook bricht den Commit ab und zeigt die Befunde | ➖ |
| 5 | `make test` und `make check` | Beide grün, `docs-check` läuft mit | ➖ |
| 6 | Lauf ohne `.libs/ProjectTools` (Symlink kurz entfernt oder `PROJECT_TOOLS` auf leeren Pfad) | Verständliche Meldung, übrige Tests laufen | ➖ |
| 7 | `README.md` und `README.de.md` nebeneinander | Gleiche Gliederung und Aussagen, Sprachlinks im Kopf | ➖ |
| 8 | Doku-Abgleich | Betroffene Dateien und Abschnitte im Ticket genannt | ➖ |

### Akzeptanzkriterien

- [ ] `.docs-check.conf.sh` in der Gliederung von StockPortfolio, jeder Eintrag mit Grund.
- [ ] `make docs-check` vorhanden, Teil von `make test` und `make check`.
- [ ] Pre-Commit-Hook aktiv nach `make setup`.
- [ ] `docs/README.template.md` vorhanden; `README.md` und `README.de.md` folgen ihr.
- [ ] `docker/preview/README.md` versioniert und aktuell.
- [ ] Screenshots unter `unraid/screenshots/` gegen den UI-Code geprüft.
- [ ] `AGENTS.md` beschreibt Prüfung, Abhängigkeiten und Quittung.
- [ ] Erste Prüfung ohne Probleme; Quittungen begründet.

### Abgrenzung

- **ProjectTools** wird nicht geändert. Fehlt dem Werkzeug etwas oder stimmt
  etwas nicht, entsteht dafür ein eigenes Ticket in StockPortfolio oder
  ProjectTools; StockInfo arbeitet mit dem veröffentlichten Stand.
- Das Screenshot-Werkzeug aus StockPortfolio T-95 ist nicht Teil dieses
  Tickets.
- Die zentrale Unraid-Vorlage im Templates-Repo bleibt außerhalb der Prüfung.

### Side-Effects

Kein Laufzeitverhalten ändert sich. Der Pre-Commit-Hook blockiert künftig
Commits mit Doku-Problemen; im Notfall `git commit --no-verify` mit
Begründung. Kein Push, kein Docker-Hub- oder Unraid-Update ohne eigenen
Auftrag.

### Auflösung

Offen. Noch keine Umsetzung oder Verifikation.

## Review-Verlauf (neueste Runde zuerst)

Noch keine Übergabe.
