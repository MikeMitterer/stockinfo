# T-104 · README nach dem Skill: nutzerorientiert, Entwicklung nach docs/development.md

**Warum dieses Ticket:** Der Skill `readme-conventions` hält Make-Targets,
npm-Befehle, Verzeichnisbäume, Test- und Release-Abläufe und Interna wie
Cache oder CORS aus dem README heraus; das README verlinkt dafür die
Entwicklerdoku. StockInfos `README.md` und `README.de.md` enthalten all das
(je rund 670 Zeilen, 48 `make`-Stellen), weil `AGENTS.md` bisher sagte:
„Entwickleranleitungen gehören ins Root-README“. StockPortfolio trennt
beides bereits: README für Nutzer, `docs/development.md` für Entwickler.

**Beispiel:** Wer StockInfo nur betreiben will, liest heute im README
zwischen Installation und Lizenz auch `make tag-patch`, den Verzeichnisbaum
und die Push-Rechte des Docker-Hub-Tokens. Danach steht im README, was
StockInfo kann und wie man es startet; der Entwicklerweg ist einen Link
entfernt.

**Stand:** Auf Mikes Entscheidung vom 2026-10-15 angelegt und aktiviert
(Frage zum README-Umbau, Antwort „Wie StockPortfolio“). Coder `claude`,
Verifier `codex`, Branch `t-104-readme-nach-skill`.

## Befunde der Prüfung (2026-10-15, vor der Umsetzung)

`make docs-check`: keine Probleme, keine Hinweise. Die ausführliche Ausgabe
(`--verbose`) und der Skill ergeben:

| # | Befund | Fundstelle |
|---|---|---|
| 1 | Make-Targets, npm-Befehle, Verzeichnisbaum, Test- und Release-Ablauf, Cache- und CORS-Details im README | `README.md`, `README.de.md`: Requirements, Quick start, Dashboard, Docker, Tests, Releases, Project layout, Security model |
| 2 | Abschnitt „Dashboard“ beschreibt einen alten Aufbau: Es fehlen FX und Analysis in der Navigation; Themes, Environment und About sind Bereiche unter Settings (Appearance, Language, API & Links, Backups, Environment, About) | `README.md:388–431`, `README.de.md:409–457`; Quelle `dashboard/src/components/AppHeader.vue:58–62`, `i18n/en.ts` |
| 3 | „8 themes“; `@mmit/ux-foundation` liefert 14 (`THEME_IDS`), das Panel zeigt alle | `README.md:104`, `:407`, `README.de.md:111`, `:431` |
| 4 | Docker-Hub-Link auf die Verwaltungsseite (`hub.docker.com/repository/docker/…/general`), die eine Anmeldung verlangt (HTTP 302); öffentlich ist `hub.docker.com/r/mangolila/stockinfo` | `README.md:18`, `:439`, `README.de.md:19`, `:467` |
| 5 | Kein Mermaid-Diagramm für den Datenfluss zur Schwester-App und zu den Quellen | beide READMEs |
| 6 | Absatzregel: neue Information im selben Absatz | `README.md` Kopfabsatz (Image, Changelog, Release Notes); `docker/README.md:28–31` („To use both … Details are in its Docker guide“); `unraid/README.md:11–14` („see …“ im selben Satz) und `:38–41` (zwei Bedingungen in einem Absatz) |

Externe Links sonst erreichbar (14 geprüft); `YOUR_UNRAID_SERVER` ist ein
Platzhalter.

## Scope-Vertrag

**Beobachtbares Ergebnis:** `README.md` und `README.de.md` folgen dem Skill
ohne Ausnahme; der Entwicklerweg steht vollständig in `docs/development.md`;
`make docs-check` ohne Probleme; alle eingehenden Anker zeigen auf
bestehende Überschriften.

**Fachliche Änderungen (drei):**

1. Projektregel und Vorlage: `AGENTS.md` (Entwickleranleitung in
   `docs/development.md`), `docs/README.template.md` nach dem Skill ohne
   Ausnahme, `.docs-check.conf.sh` (Pflichtdatei, Abhängigkeiten).
2. Entwicklerdoku: `docs/development.md` mit allem, was das README abgibt
   (Voraussetzungen, Einrichten, Befehle, Tests, Docker-Build und -Push,
   Release, Projektaufbau), in Englisch wie die Quelle.
3. READMEs neu nach der Vorlage, beide Sprachen, mit Mermaid-Diagramm;
   Befunde 2–6 behoben; eingehende Anker in `LICENSING.md`,
   `docs/plugins.md`, `unraid/README.md` nachgezogen; `docker/README.md`,
   Vorschau und `unraid/README.md` angeglichen.

**Erwartete Dateien:** `AGENTS.md`, `docs/README.template.md`,
`.docs-check.conf.sh`, `docs/development.md` (neu), `README.md`,
`README.de.md`, `docker/README.md`, `docker/preview/README.md`,
`unraid/README.md`, `LICENSING.md`, `docs/plugins.md`, `.docs-check.ack`
— 12 Dateien, keine Produkt- oder Testdatei.

**Diff-Budget:** rund 2.000 Zeilen, überwiegend verschobener Text (die
READMEs schrumpfen von je rund 670 auf rund 200 Zeilen). Das liegt über der
800-Zeilen-Grenze; Mike hat den Umbau mit dem Hinweis „Eigenes Ticket,
größerer Diff“ ausdrücklich gewählt. Das gilt als Vorabfreigabe des
Umfangs; geht der Diff über 2.400 Zeilen oder kommt eine weitere Datei
dazu, folgt ein Scope-Checkpoint.

**Nicht-Ziele:** keine Änderung an Code, Tests oder Make-Targets; keine
neuen Screenshots; StockPortfolio wird nicht angefasst (Links von dort auf
StockInfo-Anker nur als Befund); kein Image-Build oder Push in diesem
Ticket.

## Umsetzung und technische Nachweise

### Verify

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | `make docs-check` | keine Probleme; Hinweise begründet | ➖ |
| 2 | `grep` nach `make `, `npm `, Verzeichnisbaum, `CORS`, Cache in beiden READMEs | keine Treffer außer einem Link auf `docs/development.md` | ➖ |
| 3 | Eingehende Anker (`git grep 'README.md#'`) | jedes Ziel existiert; `docs-check` ohne toten Anker | ➖ |
| 4 | Inventar: jede Aussage des alten README steht im neuen README, in `docs/development.md`, `docker/README.md` oder bewusst gestrichen | Tabelle Abschnitt → Ziel im Ticket | ➖ |
| 5 | `README.md` und `README.de.md` nebeneinander | gleiche Gliederung und Aussagen, Bedienelemente im Wortlaut von `i18n/en.ts` bzw. `de.ts` | ➖ |
| 6 | Mermaid-Diagramm | rendert auf GitHub (Syntax geprüft) | ➖ |
| 7 | Doku-Abgleich | Dateien und Abschnitte im Ticket | ➖ |

### Akzeptanzkriterien

- [ ] README.md und README.de.md ohne Make-, npm-, Baum-, Test-, Release-, Cache- und CORS-Inhalte.
- [ ] `docs/development.md` enthält den vollständigen Entwicklerweg.
- [ ] `AGENTS.md` und `docs/README.template.md` beschreiben die neue Aufteilung.
- [ ] Befunde 2–6 behoben.
- [ ] `make docs-check` ohne Probleme.

### Abgrenzung

- Image-Build und -Push folgen nach diesem Ticket mit eigenem Auftrag.

### Side-Effects

Kein Laufzeitverhalten ändert sich. Die Docker-Hub-Beschreibung ändert sich
erst mit dem nächsten `make push`.

### Auflösung

Offen.

## Review-Verlauf (neueste Runde zuerst)

Noch keine Übergabe.
