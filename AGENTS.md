# StockInfo — Projektregeln

**Diese Datei ist die einzige Regelquelle des Projekts.** Sie gilt für jede
Instanz und jede Laufzeit. `AGENTS.md` ist der übliche projektweite Einstieg;
`CLAUDE.md` verweist nur hierher und enthält keine eigenen Regeln.

Eine zweite Regelkopie liefe beim ersten Nachtrag auseinander. Die Fassung vom
2026-08-26 hat genau das vorgeführt: Aus einer blinden Ersetzung von „Claude"
durch „Codex" wurden eine „Mailbox zwischen Codex und Codex" und ein
`owner`-Riegel, der das Gegenteil sagte.

## Übersicht

- [Bezeichner sind englisch. Ausnahmslos.](#bezeichner-sind-englisch-ausnahmslos)
- [Vor Arbeitsbeginn](#vor-arbeitsbeginn)
- [Arbeitsort und Integration](#arbeitsort-und-integration)
- [Tatsächlicher Entwicklungsstand](#tatsächlicher-entwicklungsstand)
- [Dokumentation gehört zur Änderung](#dokumentation-gehört-zur-änderung)
- [Datenbankzugriffe in Tests](#datenbankzugriffe-in-tests)
- [Browserprüfung](#browserprüfung)

## Bezeichner sind englisch. Ausnahmslos.

Funktionen, Klassen, Felder, Parameter und **auch lokale Variablen** — in
Produktivcode **wie in Tests** und in **jeder** Sprache: Python, TypeScript,
Vue, Bash, SQL, Makefile, YAML-Schlüssel. Es gibt keine Sprache und keine
Dateiart, in der die Regel nicht gilt.

Das Namensschema je Sprache ist davon unberührt: Bash-Variablen bleiben GROSS
(`local -r _RETRY_DELAY`), Python `snake_case`, TypeScript `camelCase` — nur
eben englisch.

Deutsch bleibt die Sprache der **Erklärung**: Kommentare, Docstrings, Testnamen
(`def test_werte_ueberleben_das_erneute_lesen`), beschreibende `pytest`-IDs und
Commit-Bodies.

Steht in einer Datei beides, ist das keine gewachsene Konvention, der man folgt,
sondern Altlast: **Was ohnehin angefasst wird, zieht mit.** Das ist keine
Scope-Frage, die es zu klären gilt — die Regel hat sie schon beantwortet.

**Die Gegenprobe ist ein Inventar, keine Textsuche.** `grep` findet nur, was man
vorher erraten hat. Für Python zählt `ast` alle `ast.Name`, `ast.arg`, Funktions-
und Klassennamen auf; für TypeScript leistet das ein Lauf über die
TS-Compiler-API, für Bash die Liste aller Zuweisungen und Funktionsköpfe.
(`vue-tsc` prüft Typen, kein Inventar — es findet einen deutschen Namen nie.) Genau daran ist die zu kurze Liste in
T-21 Runde 37 gescheitert.

Vollständige Konventionen samt Namensschema je Sprache: Skill `code-conventions`.

[↑ Übersicht](#übersicht)

## Vor Arbeitsbeginn

**Dieses Projekt führt seine Tickets mit agent-lessons.** Board, Rollen, Regeln
und Lessons liest und schreibst du über den MCP-Server `agent-lessons`, nicht
von Hand in `_tickets/`.

- **Zuerst `next`:** In jedem Durchlauf sagt `next`, was deine Rolle jetzt tut.
- **Stand:** `get_status`, die Spalten mit `get_tickets`, ein Ticket mit
  `get_ticket`.
- **Regeln und Lessons:** `get_config` nennt Regeln und Guards mit Summary
  (Volltext mit `get_rule`, `get_guard`), `get_lessons` die Lessons.
- **Rollen:** Eine Sitzung mit Rolle startet Mike mit `al start ROLLE`
  (implementer, reviewer, observer). Ohne Rolle arbeitest du nur auf
  ausdrücklichen Auftrag.
- **Fragen und Notizen an Mike:** `ask_user` bzw. `add_note`, nicht im eigenen
  Gedächtnis.

Nur der zuständige Coder (`implementer`) implementiert, der Verifier
(`reviewer`) prüft unabhängig. Wer nicht am Zug ist, verändert keinen
Produktcode. Ein Rollenwechsel ändert weder geprüfte Fassungen noch den
Rundenverbrauch.

Die früheren lokalen Lessons dieses Projekts (`SI-*`) stehen seit der
Umstellung im gemeinsamen Bestand; `get_lessons` liefert sie, beim Start eines
Tickets kommen die passenden mit.

[↑ Übersicht](#übersicht)

## Arbeitsort und Integration

**Jede Sitzung arbeitet in ihrem eigenen Workspace** unter `.worktrees/`, nicht
im Projekt-Root (Mike, 2026-11-02, mit der Umstellung auf agent-lessons; ersetzt
die Regel vom 2026-10-01, nach der alle Instanzen nur im Root arbeiteten).
`start_ticket` legt den Ticketbranch an und wechselt dorthin; den Branch wechselt
keine Instanz von Hand. Mike sieht den Stand im Projekt-Root mit `al develop`
oder `al T-NN`.

- **Ein Board.** `_tickets/` ist der Worktree des Branches `board`. Board und
  Tickets ändern nur die Werkzeuge, nie eine Instanz von Hand.
- **Integration über `develop`.** Die technische Freigabe des Verifiers merged
  den Ticketbranch auf `develop`. Mit dem Abnahme-Modus `auto` übernimmt das
  Board ein Ticket danach ohne menschliche Abnahme nach `master`, sobald der
  Prüfbefehl grün ist (Mike, 2026-11-02: „acceptance_default auto“). Je Ticket
  setzt Mike einen anderen Modus mit `al ticket mode ID human`; abnehmen
  mit `al ticket accept ID`, ablehnen mit `al ticket reject ID GRUND`.
- **Push ist eine eigene Entscheidung.** Weder Freigabe noch Abnahme
  beauftragen einen Push oder eine Veröffentlichung.

[↑ Übersicht](#übersicht)

## Tatsächlicher Entwicklungsstand

StockInfo ist Entwicklungsstand und wird bislang nur von Mike verwendet.
Eine erste Unraid-Version begründet keine angenommene externe Nutzerbasis.
Migrationspfade, Kompatibilität und Ablösungshinweise brauchen konkreten
Bedarf aus tatsächlich genutzten Daten, Installationen oder ausdrücklich
benannten Verbrauchern. Keine Zusatzarbeit für hypothetische Verbreitung.
Aktuelle Dokumentation beschreibt den gültigen Stand direkt; verworfene
Entwicklungsregeln brauchen keine Übergangs- oder Ablösungshinweise.
Prüfaufwand und Befundgewicht folgen dem belegten Schaden. Das gilt für die
Breite zusätzlicher Arbeit, nicht für bereits geltende, als MUST oder eigene
Abnahmebedingung formulierte Standardregeln (etwa i18n oder DRY in
`code-conventions`): ein Verstoß dagegen bleibt blockierend, unabhängig vom
beobachteten Schaden (Lesson SI-P-13).
Diese Einordnung gilt, bis Mike einen anderen Betriebsstand festlegt.

[↑ Übersicht](#übersicht)

## Dokumentation gehört zur Änderung

Bei Änderungen an Verhalten, Verträgen, Konfiguration, Installation oder
beschlossenem Umfang gehört der **Doku-Abgleich zum selben Auftrag**.
Mike muss betroffene Anleitungen nicht eigens nennen.

**Wie die Anleitungen aussehen, steht nicht hier.** Aufbau, Inhalt,
Sprachfassungen und Schreibregeln der Projektdoku regelt der Skill
`docs-conventions` mit der Projektvorlage
[`docs/README.template.md`](docs/README.template.md). Die Vorlage legt auch
fest, was in `README.md`/`README.de.md`, in die Entwicklerdoku
`docs/development.md`, in die Container-Anleitung `docker/README.md` und in
die Unraid-Anleitung `unraid/README.md` gehört. Die Docker-Hub-Beschreibung
regelt der Skill `docker-conventions`. Diese Datei wiederholt keine dieser
Regeln; wer eine ändern will, ändert Skill oder Vorlage.

Für alle übrigen Dokumente unter `docs/` gilt: für normale Programmierer
ohne Vorwissen über dieses Projekt schreiben. Dokumentation beschreibt nur,
was es gibt; geplante Funktionen gehören in Tickets, nicht in die Doku.

**`make docs-check` prüft die Doku gegen das Projekt** (läuft auch in
`make test`, `make check` und vor jedem Commit über `.githooks/pre-commit`,
das `make setup` aktiviert). Welche Dokumente, verbotenen Begriffe,
Pflichtdateien, Screenshots und Abhängigkeiten gelten, steht mit Grund in
[`.docs-check.conf.sh`](.docs-check.conf.sh); eine neue Regel dieser Art
kommt dort hinein. Diese Datei und `CLAUDE.md` prüft es nur auf tote Links
und Anker; Verweise auf andere Dokumente deshalb als Link schreiben.
Meldungen, die nach dem Prüfen nichts verlangen, mit
`docs-check --ack <datei>` quittieren und
`.docs-check.ack` mitcommitten; nie ungesehen. `--no-verify` nur im Notfall
und mit Begründung im Bericht. Einstellungen der Settings-Klasse in
`app/config.py` erkennt die Prüfung nicht; neue Einstellungen von Hand
dokumentieren.

**Doku-Abgleich im Ablauf:**

- Der Bearbeiter ermittelt die betroffenen Dokumente über ein Datei- und
  Überschrifteninventar und verfolgt die geänderten Zusagen gezielt durch
  sie hindurch.
- Im Ticket beziehungsweise Abschlussbericht steht knapp **Doku-Abgleich:**
  betroffene Dateien und Abschnitte samt Ergebnis, bei unveränderter Datei
  mit Grund.
- Der Verifier prüft Zuordnung und Aussagen gegen die geprüfte Fassung. Ein
  grüner Testlauf ersetzt diesen Inhaltsabgleich nicht; Änderungen an
  mehreren Dateien allein sind kein Nachweis.

[↑ Übersicht](#übersicht)

## Datenbankzugriffe in Tests

Backend-Tests erhalten durch `tests/conftest.py` je Test einen temporären
`DATABASE_PATH`; Settings-, Service- und Quellen-Caches werden zurückgesetzt.
SQLite-Verbindungen nach `data/` oder zur vor Testbeginn konfigurierten
Arbeitsdatenbank werden vor dem Öffnen abgewiesen. Zusätzliche Datenbanken
gehören unter `tmp_path`. Den Riegel nicht für einen Test abschalten; Gegenproben
verwenden temporäre Stand-ins. Die App-Verdrahtung darf Settings verwenden,
aber Tests dürfen sich nicht auf Daten aus dem Arbeitsbestand verlassen.

[↑ Übersicht](#übersicht)

## Browserprüfung

**Browserbelege für StockInfo kommen aus `dashboard/e2e/visual-check.mjs`.**
Kein eigenes Skript je Ticket, keine Kopie außerhalb des Repos (Mike,
2026-10-02). Das Skript startet eine eigene Instanz mit temporärer Datenbank
und Offline-Daten aus `examples/` und prüft die Hauptwege in Chrome. Die
Arbeitsdatenbank `data/` berührt es nie.

- **Aufruf:** steht im Kopfkommentar des Skripts, nur dort. Für ein Ticket
  genügt meist ein gezielter Lauf mit `ONLY=W…`; nach großen Umbauten alle
  Wege.
- **Neuer sichtbarer Ablauf:** Er bekommt einen neuen Weg im Skript, mit
  geprüften Inhalten statt nur einem Screenshot. Bestehende Wege werden
  angepasst, wenn sich ihr Verhalten ändert.
- **Kein Make-Target, kein README-Abschnitt:** Die Prüfung ist ein Werkzeug
  für die Agenten; einem Lauf kann kein Mensch folgen. Voraussetzung ist
  Node 24+, wie in [`docs/development.md`](docs/development.md) angegeben.
- **Fenster:** Sichtbare Läufe öffnen das Browserfenster auf dem
  Hauptmonitor, links bei x = 100 px, weil dort Mikes Dock liegt (Mike,
  2026-10-02). `HEADLESS=1` bleibt für Läufe ohne Fenster.

**Nach Umbauten an der Datenbank:** `scripts/compare_database_versions.py`
vergleicht die API eines alten und des aktuellen Stands auf je einer Kopie des
Arbeitsbestands und startet danach W17 „Arbeitsbestand“ sichtbar auf einer
weiteren Kopie (T-97). Das Original öffnet es nur lesend und bricht ab, wenn
es sich ändert oder die App noch läuft; alles andere liegt unter `.tmp/t97/`
und wird gelöscht. Aufruf und Grenzen stehen im Modul-Docstring. Jeder
Unterschied zwischen den Ständen ist ein Befund (Exit 1); eine
Ausnahmeliste gibt es nicht.

Für eine Browserprüfung mit beiden Apps gibt es in StockPortfolio
`scripts/stockinfo-test-server.py`. Es startet die echte StockInfo-API mit
temporärer Datenbank und lokalen Testkursen. Start und Stop sind in seinem
Modul-Docstring und in StockPortfolios `AGENTS.md` beschrieben. Dafür nie die
Arbeitsdatenbank verwenden.

[↑ Übersicht](#übersicht)
