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
- [Tatsächlicher Entwicklungsstand](#tatsächlicher-entwicklungsstand)
- [Dokumentation gehört zur Änderung](#dokumentation-gehört-zur-änderung)
- [Datenbankzugriffe in Tests](#datenbankzugriffe-in-tests)

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

Vollständige Konventionen samt Namensschema je Sprache: Skill `code-standards`.

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
  sammeln Fehlermuster des jeweils benannten Agenten. Der Coder liest seine
  Sammlung vor der Übergabe; der Verifier liest die des Autors der geprüften
  Fassung vor dem Review. Bei gemischter Autorenschaft beide lesen.
- `_tickets/.agents/AGENT-WORKFLOW.md` enthält den gemeinsamen fachlichen Ablauf.
- `_tickets/.agents/AGENT-ACTIVATION.md` trennt davon die laufzeitspezifischen Startwege.

Diese Regeln gelten für beide Rollen. Dateinamen und historische Akteursnamen
sind keine Rollenverteilung. Ein Rollenwechsel wird ausdrücklich im Status
festgehalten und ändert weder geprüfte Fassungen noch den Rundenverbrauch.

[↑ Übersicht](#übersicht)

## Tatsächlicher Entwicklungsstand

StockInfo ist Entwicklungsstand und wird bislang nur von Mike verwendet.
Eine erste Unraid-Version begründet keine angenommene externe Nutzerbasis.
Migrationspfade, Kompatibilität und Ablösungshinweise brauchen konkreten
Bedarf aus tatsächlich genutzten Daten, Installationen oder ausdrücklich
benannten Verbrauchern. Keine Zusatzarbeit für hypothetische Verbreitung.
Aktuelle Dokumentation beschreibt den gültigen Stand direkt; verworfene
Entwicklungsregeln brauchen keine Übergangs- oder Ablösungshinweise.
Prüfaufwand und Befundgewicht folgen dem belegten Schaden. Diese Einordnung
gilt, bis Mike einen anderen Betriebsstand festlegt.

[↑ Übersicht](#übersicht)

## Dokumentation gehört zur Änderung

**Schreibe für normale Programmierer, ohne Vorwissen über dieses Projekt.**
Das gilt für alle Dokumente, auf Deutsch und Englisch. Der Leser soll schnell
erkennen, was etwas macht, wie er es benutzt und welche Grenzen gelten.

- Kurze, direkte Sätze und geläufige Wörter. Keine KI-Floskeln, Werbesprache
  oder erfundenen Fachbegriffe.
- Fachbegriffe nur, wenn sie nötig sind; beim ersten Auftreten kurz erklären.
  Ein kleines Beispiel hilft oft mehr als eine abstrakte Erklärung.
- Aussagekräftige Überschriften und kurze Absätze. Schritte als nummerierte
  Liste, Vergleiche bei Bedarf als Tabelle. Nicht jeden Satz fett setzen.
- Die wichtigste Information zuerst. Details stehen beim jeweiligen Thema;
  Wiederholungen und Erklärungen ohne Nutzen für den Leser entfallen.
- Anleitungen beschreiben die Benutzung und das aktuelle Verhalten.
  Interne Arbeitsabläufe und Review-Geschichte gehören in die Tickets.

Bei Änderungen an Verhalten, Verträgen, Konfiguration, Installation oder
beschlossenem Umfang gehört der **Doku-Abgleich zum selben Auftrag**.
Mike muss betroffene Anleitungen nicht eigens nennen.

- Der Bearbeiter ermittelt über das Datei- und Überschrifteninventar die
  betroffenen Anleitungen, Referenzen, Beispiele und Specs; dazu gehören auch
  README-Dateien außerhalb von `docs/`. Anschließend verfolgt er die geänderten
  Zusagen und ihre Verweise gezielt durch diese Dokumente.
- Aktuelle Anleitungen werden mitgezogen. Geplantes wird ausdrücklich als
  noch nicht verfügbar gekennzeichnet; bei Umsetzung entfällt diese Markierung.
  Historische Entwürfe und Prüfnachweise bleiben als Historie erkennbar.
- Im Ticket beziehungsweise Abschlussbericht steht knapp: **Doku-Abgleich:**
  betroffene Dateien/Abschnitte und Ergebnis. Ist keine Anpassung nötig, wird
  der Grund genannt. Eine zweite handgepflegte Dokumentationsliste entfällt.
- Der Verifier prüft die Zuordnung und die Aussagen gegen die geprüfte Fassung.
  Fehlende oder widersprüchliche aktuelle Dokumentation gehört zur Nacharbeit.
  Linkprüfungen und ausführbare Beispiele ergänzen diesen Inhaltsabgleich;
  ein grüner Testlauf ersetzt ihn nicht.

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
