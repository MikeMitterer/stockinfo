---
schema_version: 1
id: SI-P-14
project: stockinfo
kind: pattern
discovery_phase: mixed
affected_work:
- tests
- handoff
subject_author: claude
discovered_by: codex
recorded_by: claude-observer
structured_by: claude-observer
prevention_roles:
- implementer
- reviewer
evidence:
- ticket: T-90
  round: 2
  reviewed_commit: 88d54d8
  result_commit: 45fafe4
  finding: B4
- ticket: T-90
  round: 3
  reviewed_commit: 44f72ab
  result_commit: d62b141
  finding: B5
- ticket: T-92
  round: 1
  reviewed_commit: 833e3cf
  result_commit: 172e3b7
  finding: B1
- ticket: T-92
  round: 2
  reviewed_commit: 7d0be5e
  result_commit: 8d3b170
  finding: B1
- human: "Ja, leg die Lesson für das Wächtermuster an (Mike, 2026-10-02)"
---

# SI-P-14 · Der Grenzwächter bestätigt eine handgeschriebene Liste

**Implementer-Regel:** Ein Grenztest beweist eine Zusage nur, wenn er die
Fundstellen selbst inventarisiert und mit der erklärten Ausnahmeliste
vergleicht. Ausnahmen über den exakten erlaubten Ausdruck festlegen, nicht
über erkannte Merkmale. Vor der Übergabe den Wächter gegen die gemeldete
Variante **und** mindestens zwei selbst gewählte Nachbarvarianten laufen
lassen; jede muss rot werden.

**Verifier-Prüfung:** Die Ausnahme- oder „sauber“-Liste der Übergabe nicht
aus dem grünen Test übernehmen. Eine eigene minimale Variante bauen, die die
Zusage verletzt, aber anders aussieht als die bekannten Fälle (Alias,
anderer Aufrufname, dynamischer Zweig, Verkettung). Erwarteter Beleg: die
Variante und die rote Testausgabe.

## Originalbelege und Einordnung

**Erkennungsregel:** Das Ticket nennt eine von Hand geschriebene Liste —
„diese Module enthalten kein rohes SQL“, „nur diese Datei fasst die
Datenbank an“ — und ein Wächtertest „bestätigt“ sie. Der Test sucht aber nur
nach vorher vermuteten Merkmalen: bestimmten Funktionsnamen, Variablennamen
oder festen Strings. Was anders aussieht, bleibt unsichtbar, und die Liste
gilt trotzdem als belegt. Jede Nacharbeit schließt genau die gemeldete
Variante; die nächste naheliegende findet wieder der Verifier.

**Prüffrage:** Würde der Test rot, wenn jemand die Zusage auf eine Weise
verletzt, an die beim Schreiben niemand gedacht hat? Erzeugt der Test die
Liste selbst und vergleicht sie, oder prüft er nur die Fälle, die schon auf
der Liste stehen?

**Belege (Befunde von Codex als Verifier, Fassungen von Claude als Coder):**

| Ticket · Runde | Zusage | Was der Wächter erkannte | Was er übersah |
|---|---|---|---|
| T-90 · 2, `88d54d8` | Kein Datenbankzugriff außerhalb `app/persistence/` | SQL-Strings, `execute`, SQLite-Importe | Dateitausch beim Restore (`os.replace`, `shutil.copy2`, `-wal`/`-shm`) |
| T-90 · 3, `44f72ab` | dieselbe | Dateizugriffe, wenn der Name `database` enthält | `path = Path(database_path); os.replace(incoming, path)` |
| T-92 · 1, `833e3cf` | `session.py` ohne SQL-Text | `text()` und SQL in `execute` | `exec_driver_sql("BEGIN IMMEDIATE" …)` |
| T-92 · 2, `7d0be5e` | in `session.py` nur `BEGIN`/`BEGIN IMMEDIATE` | feste Strings im Argument | `"BEGIN IMMEDIATE" if immediate else statement`, `"BEGIN" + suffix` |

Jeder Fall kostete eine Review-Runde; der Produktcode war in T-92 dabei laut
Verifier schon in Ordnung. Den gemeinsamen Mechanismus über beide Tickets
hat claude-observer am 2026-10-02 benannt; Mike beauftragte die Lesson.

**Wie es ausgegangen ist:** T-90 Runde 4 (`65d7f05`) verfolgt Pfad-Aliase
innerhalb einer Funktion und wurde mit einer Mutation im echten
`apply_pending` rot belegt; Restgrenzen (Übergabe als Argument, Tupel,
Closures) stehen offen im Ticket. T-92 Runde 3 (`544e82a`) prüft den ganzen
Argumentausdruck gegen feste erlaubte Zeichenketten und belegt Variable,
Verkettung und f-String als rot.

**Abgrenzung:** [SI-P-02](SI-P-02-punktuelle-korrektur-wird-als-vollstaendige-regelumsetzung-gemeldet.md)
beschreibt die punktuelle Korrektur allgemein,
[SI-P-08](SI-P-08-der-test-erzeugt-den-entscheidenden-unterschied-nicht.md)
den Test ohne entscheidenden Unterschied. SI-P-14 betrifft den Fall, dass ein
Prüftest eine handgeschriebene Vollständigkeitsaussage scheinbar belegt.
Grenze nach [SI-P-09](SI-P-09-eine-testanforderung-waechst-zum-unbeauftragten-subsystem.md):
kein eigenes Analyse-Subsystem; eine exakte Ausnahme und wenige
Nachbarvarianten genügen. Bezug in `AGENTS.md`: „Die Gegenprobe ist ein
Inventar, keine Textsuche.“
