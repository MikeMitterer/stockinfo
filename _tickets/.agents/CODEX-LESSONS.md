# Erfahrungen aus Codex-Arbeit

**Diese Sammlung hält belegte, wiederkehrende Probleme in Codex-Arbeit fest.**
Sie dient dem Coder zur Vorbeugung und dem Verifier als gezielte Prüfhilfe.
Die aktuelle Rollenverteilung steht ausschließlich in [STATUS.md](../STATUS.md).

## Übersicht

- [Gemeinsame Vorgabe zum Rundenlimit](#gemeinsame-vorgabe-zum-rundenlimit)
- [Verwendung](#verwendung)
- [R-02 · Entwicklungsstand wird wie ein breit ausgerolltes Produkt behandelt](#r-02--entwicklungsstand-wird-wie-ein-breit-ausgerolltes-produkt-behandelt)
- [CX-01 · Der grüne Gesamtlauf steht auf Reststand statt auf Frischstart](#cx-01--der-grüne-gesamtlauf-steht-auf-reststand-statt-auf-frischstart)
- [T-66 · Fachbefund übernommen, Gewichtung nicht eigenständig geprüft](#t-66--fachbefund-übernommen-gewichtung-nicht-eigenständig-geprüft)
- [Wann ein Befund zum Muster wird](#wann-ein-befund-zum-muster-wird)

## Gemeinsame Vorgabe zum Rundenlimit

Maßgeblich ist der gemeinsame
[Ablauf zum Rundenlimit](AGENT-WORKFLOW.md#rundenlimit-rest-offenlegen-und-abschließen).
Die folgende Erfahrung erklärt den Anlass; sie ist keine zweite Regelkopie.

Anlass sind die von Mike benannten, zunächst liegen gebliebenen
Docstring-Korrekturen aus T-21 und Codex' anschließende zu starre
Eskalationsregel in `4dbb9bd`. Das ist eine ausdrückliche gemeinsame
Arbeitsvorgabe, keine Behauptung zusätzlicher unabhängiger Vorfälle.

[↑ Übersicht](#übersicht)

## Verwendung

Wenn Codex den Prüfgegenstand erstellt hat, liest der Verifier diese Datei
vor dem Review. Codex liest sie vor einer Übergabe seiner eigenen Arbeit.
Bei gemischter Autorenschaft werden die Sammlungen beider beteiligten Agenten
berücksichtigt. Entscheidend ist der Autor der geprüften Fassung, auch nach
einem Rollenwechsel.

Einzelbefunde bleiben zunächst in ihren Tickets; die Claude-Sammlung wird nicht
als Codex-Befund kopiert.

[↑ Übersicht](#übersicht)

## R-02 · Entwicklungsstand wird wie ein breit ausgerolltes Produkt behandelt

Die verbindliche Vorgabe steht im
[Projekteinstieg](../../CLAUDE.md#tatsächlicher-entwicklungsstand).
Dieser Eintrag hält Anlass und Erkennung des Fehlmusters fest.

**Erkennungsregel:** Eine Änderung wird mit Rückwärtskompatibilität,
Migrationspfaden, Ablösungshinweisen oder zusätzlicher Reviewarbeit belastet,
weil hypothetisch viele Nutzer oder unbekannte Altinstallationen betroffen
sein könnten. Eine Veröffentlichung auf Unraid wird dabei ohne Beleg mit
breiter Nutzung gleichgesetzt. So entsteht Aufwand ohne konkreten Nutzen.

**Prüffrage:** Welcher reale Nutzer, Datenbestand oder Verbraucher braucht diese
Maßnahme heute, und welchen konkreten Nachteil verhindert sie? Ohne belegbare
Antwort entfällt die zusätzliche Maßnahme; die eigentliche Änderung wird fertig.

**Anlass:** T-21, Codex als Implementer, `1166745`: Ablösungsnotiz zur früheren
US-Sonderregel; anschließend Übergangssprache im Entwurf (`f0fb8c8`). Mike
weist beides zurück; entfernt in `4bacaf2`. Mike benennt das übergeordnete
Problem ausdrücklich als wiederkehrend: „Der aktuelle Stand ist ein
Entwicklungsstand“ und „Wir schießen mit Kanonen auf Spatzen“. Diese Vorgabe
wird auf seinen Auftrag festgehalten; es werden keine weiteren Vorfälle erfunden.

[↑ Übersicht](#übersicht)

## CX-01 · Der grüne Gesamtlauf steht auf Reststand statt auf Frischstart

**Erkennungsregel:** Die Übergabe nennt eine vollständige grüne Suite und ein
kopierbares Kommando mit eigenem Datenpfad. Der Pfad wird im Kommando nur
*genannt*, nicht *erzeugt* — er existiert aus einem früheren Lauf bereits
angelegt und initialisiert.

**Prüffrage:** Existiert der im Beleg genannte Zustand vor dem Lauf schon? Das
dokumentierte Kommando einmal auf einem nachweislich leeren Pfad wiederholen und
die Zahlen vergleichen. Bei Tickets, die Schema, Migration, Loader oder
Startzustand berühren, ist das der Frischstart aus dem
Vertical-Acceptance-Riegel und nicht optional.

**Beleg (ausdrücklich falsche Vollständigkeitsbehauptung):** T-26 Runde 1,
Prüfstand `fe323ff`. Verify `#11` und die OUTBOX melden „1065 Backend
erfolgreich" mit dem Kommando
`env DATABASE_PATH=/tmp/stockinfo-t26-suite/stockinfo.db make test`. Diese Datei
lag zum Zeitpunkt des Belegs bereits vollständig initialisiert vor
(`detail_values`, `detail_overrides`, Zeitstempel 14:51). Auf einem frischen
Pfad ergibt dasselbe Kommando `7 failed, 1058 passed`: `GET /fields` liest seit
diesem Diff `meta`, ohne dass `init_db` gelaufen sein muss
(`sqlite3.OperationalError: no such table: meta`, `app/routers/fields.py:47`).
Gegenprobe mit initialisierter Datenbank: dieselben 36 Tests grün. Befund von
Claude als Verifier, 2026-09-07.

[↑ Übersicht](#übersicht)

## T-66 · Fachbefund übernommen, Gewichtung nicht eigenständig geprüft

Einzelfall-Lehre auf ausdrücklichen Auftrag von Mike, 2026-09-08: Codex
bestätigte Claudes korrekte Aussage zur HTTP-Middleware und übernahm daraus
vorschnell die SSE-Empfehlung (`26590c8`). Die Prüfung der konkreten UI-/REST-
Wirkung fehlte. Die Korrektur erfolgte in `e4b793e`, bestätigt in `e5e0b20`.
Bei der Review-Übernahme sind **Befund und Architekturfolgerung getrennt** zu
prüfen; ein zutreffender Codeverweis beweist nicht die behauptete Schwere.
Die gemeinsame Analyse und Gegenprüfung stehen einmalig in
[R-01 der Review-Lehren](CLAUDE-LESSONS.md#r-01--integrationsaufwand-verdrängt-die-fachliche-architekturentscheidung).
Keine zweite unabhängige Episode wird behauptet.

[↑ Übersicht](#übersicht)

## Wann ein Befund zum Muster wird

- **Mindestens zwei konkrete Belege derselben Fehlerklasse.**<br>
  Alternativ genügt eine ausdrücklich falsche Vollständigkeitsbehauptung mit
  dokumentierter Behauptung und Gegenbeleg. Eine Vermutung genügt nicht.

- **Jeder Eintrag macht die nächste Prüfung konkret.**<br>
  Er enthält Erkennungsregel, Prüffrage und verlinkte Belege mit Ticket,
  geprüfter Fassung oder Runde und beobachtetem Ergebnis. Die Zuordnung zu
  Codex muss belegt sein; der Name des aktuellen Owners allein genügt nicht.

- **Neue Belege ergänzen das vorhandene Muster.**<br>
  Stabile Kennungen wie `CX-01` verwenden. Menschliche Rückmeldungen bleiben
  im Original erhalten; ein Muster ersetzt weder Ticket noch Abnahmenachweis.

Wiederkehrende Probleme können Implementierung, Tests, Dokumentation,
Übergaben oder die Arbeit als Verifier betreffen. Die Rolle beim jeweiligen
Befund ausdrücklich nennen. Fachliche Regeln gelten unabhängig vom Agenten.

[↑ Übersicht](#übersicht)
