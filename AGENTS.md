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
- [Ein Arbeitsort: der Projekt-Root](#ein-arbeitsort-der-projekt-root)
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

**Coder und Verifier werden ausschließlich in `_tickets/STATUS.md` zugeordnet.**
`implementer` bezeichnet den Coder, `reviewer` den Verifier, `owner` die
Instanz, die gerade am Zug ist. Diese drei Felder prüft die eigene Instanz vor
jedem Turn.

Nur der zuständige Coder implementiert, der Verifier prüft unabhängig. Wer nicht
am Zug ist, verändert keinen Produktcode: Für die andere Instanz bleibt die
Commit-Linie eingefroren, außer für ausdrücklich beauftragte Review- und
Statusdateien.

- `_tickets/.agents/CLAUDE-LESSONS.md` und `_tickets/.agents/CODEX-LESSONS.md`
  sind Linkeinstiege zu den lokalen Einzel-Lessons. Der Coder liest die
  Erfahrungen seiner Autorenschaft vor Umsetzung und Übergabe; der Verifier
  die des Autors der Prüffassung vor dem Review. Bei gemischter Arbeit beide.
- `_tickets/.agents/AGENT-WORKFLOW.md` enthält den gemeinsamen fachlichen Ablauf.
- `_tickets/.agents/AGENT-ACTIVATION.md` trennt davon die laufzeitspezifischen Startwege.

Diese Regeln gelten für beide Rollen. Dateinamen und historische Akteursnamen
sind keine Rollenverteilung. Ein Rollenwechsel wird ausdrücklich im Status
festgehalten und ändert weder geprüfte Fassungen noch den Rundenverbrauch.

Lokale Lessons liegen als Einzeldateien unter `_tickets/.agents/lessons/`.
Die alten Sammeldateien sind Linkeinstiege. Verzeichnisinventar, gemeinsamer
AgentLessons-Bestand und Herkunft folgen
[Lessons lesen und pflegen](_tickets/.agents/LESSONS-ACCESS.md). Der Collector
aktualisiert die gemeinsame Sammlung auf ausdrücklichen Aufruf; ein
periodischer Lauf und die automatische Regelableitung sind noch nicht umgesetzt.

[↑ Übersicht](#übersicht)

## Ein Arbeitsort: der Projekt-Root

**Alle Instanzen arbeiten ausschließlich im Projekt-Root
`/Volumes/DevLocal/DevWeb/Production/StockInfo`** (Mike, 2026-10-01).
Keine `git worktree add` und keine Kopien unter `/private/tmp` oder anderswo,
außer Mike ordnet es ausdrücklich an. Grund: Mike sieht Board und prüfbaren
Quellstand an einer Stelle und testet genau dort.

- **Ein Board.** `_tickets/` gibt es nur im Root. Board-Änderungen kommen auf
  den gerade ausgecheckten Branch. Ein Ticket im Backlog ist damit vom Root
  aus sichtbar, auch wenn seine Umsetzung noch nicht aktiviert ist.
- **Branch im Feld `branch`.** Der Ticketbranch wird im Root ausgecheckt
  (`git switch`). `_tickets/STATUS.md` nennt ihn im Feld `branch`. Vor jedem
  fachlichen Durchlauf vergleicht jede Instanz `git branch --show-current`
  mit diesem Feld. Bei Abweichung meldet sie den Konflikt und arbeitet nicht
  weiter.
- **Nur der Owner schaltet den Branch.** Er setzt `branch` im selben Commit,
  der den neuen Stand beginnt. Der Verifier prüft die Übergabe im Root und
  wechselt den Branch nicht; ältere Fassungen liest er mit `git show` und
  `git diff`.
- **Früh integrieren.** Nach der technischen Freigabe mergt der Coder den
  geprüften Ticketbranch lokal nach `master` und stellt den Root auf `master`
  zurück. Mikes menschliche Abnahme findet auf `master` statt. Nacharbeit
  beginnt auf einem neuen Branch von `master`. Bereits offene menschliche
  Abnahmen bleiben offen; der Merge ersetzt sie nicht.
- **Push ist eine eigene Entscheidung.** Weder technische Freigabe noch lokaler
  Merge beauftragen einen Push oder eine Veröffentlichung.

Lokale Ausnahme vom gemeinsamen Paket: `PROJECT-RULES.md` mergt erst nach
Prüfung **und** menschlicher Abnahme. In StockInfo folgt der lokale Merge
bereits auf die technische Freigabe. Die gemeinsame Übernahme ins Paket ist
AgentLessons T-52.

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
beobachteten Schaden ([SI-P-13](_tickets/.agents/lessons/SI-P-13-eine-muss-regel-wird-per-schadensabwaegung-zur-kann-regel.md)).
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
`./.libs/ProjectTools/src/bash/docs-check.sh --ack <datei>` quittieren und
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
