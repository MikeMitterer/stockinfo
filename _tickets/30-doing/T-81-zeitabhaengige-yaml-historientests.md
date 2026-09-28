# T-81 · Zeitabhängige YAML-Historientests stabilisieren

Zwei Backend-Tests prüfen die manuelle Tagesreihe aus
`tests/_resources/assets.yaml` über `period=1m`. Die Beispieldatei enthält
Schlusskurse vom 25. bis 27. August 2026. Am 28. September beginnt das
31-Tage-Fenster am 28. August; der Endpunkt liefert deshalb korrekt `[]`,
während die Tests weiterhin drei Punkte erwarten.

**Fund beim Abschluss von T-80, 2026-09-28:** `make test` meldete
`1243 passed, 35 skipped, 2 failed`. Betroffen sind
`test_die_tagesreihe_faellt_auf_die_datei_durch` und
`test_die_manuelle_history_kommt_als_tagesreihe` in
`tests/test_yaml_profile.py`. T-80 ändert weder diese Tests noch Backend-Code;
der Fehler liegt bereits im gemeinsamen Stand von `master` und T-80.

## Ziel und Prüfung

- Die Tests prüfen weiterhin den Weg über die konfigurierte YAML-Quelle und
  die drei gepflegten Schlusskurse, unabhängig vom aktuellen Kalendertag.
- Den angefragten Zeitraum oder die Testdaten passend zum Testzweck wählen.
  Das Verhalten des öffentlichen `1m`-Filters bleibt erhalten.
- Beide betroffenen Tests und anschließend `make test` auf einem frischen
  Testlauf ausführen; keine Arbeitsdatenbank verwenden.

**Einordnung:** Eigenes Testproblem, kein offener T-80-Produktbefund. Mike
beauftragte die Korrektur am 2026-09-28; der aktive Auftrag steht in
`STATUS.md`.

## Umsetzung · Codex, 2026-09-28

Die beiden Anfragen in `tests/test_yaml_profile.py` verwenden jetzt
`period=max` statt `period=1m` (Commit `78059a8`). Beide Fälle prüfen die
Quelle und die drei gespeicherten Werte, nicht die Begrenzung auf einen Monat.
`max` liefert im Service `desired_start=None`; die Testdaten bleiben deshalb
auch später im abgefragten Verlauf. Der öffentliche `1m`-Filter und alle
Produktdateien sind unverändert.

| # | Prüffall | Ergebnis |
|---|---|:--:|
| 1 | Stumme vordere Quelle reicht die gesamte Tagesreihe an `yaml-file` weiter | ✅ Drei Schlusskurse über den echten API-Weg |
| 2 | `yaml-file` allein liefert die manuell gepflegte Tagesreihe | ✅ Drei Schlusskurse über den echten API-Weg |
| 3 | Vollständige Projekt-Testsuite | ✅ `make test`: Backend 1245 bestanden, 35 übersprungen; Plugin-API, Beispiel-Plugin, Dashboard-Lint und 385 Dashboard-Tests bestanden |

**Rot/Grün:** Vor der Änderung fielen beide betroffenen Tests mit `[]` statt
`[99.18, 99.31, 99.42]` durch. Nach der Änderung bestanden beide gezielt
(2/2). `make test` lief danach mit temporären Datenbanken vollständig durch.
Das AST-Bezeichnerinventar der angefassten Testdatei enthält gegenüber dem
Vorgänger keine neuen oder entfernten Namen (116 Namen, Differenz leer).
`git diff --check` ist sauber.

**Doku-Abgleich:** `README.md` beschreibt `1m` und `max` bereits als gültige
API-Zeiträume sowie den Testaufruf. `docker/README.md` beschreibt Container
und Datenquellen, aber keine internen Testzeiträume. Beide Anleitungen bleiben
unverändert, weil sich nur die Testanfrage ändert. Keine Änderung an
Verhalten, Konfiguration, Installation, Datenbank oder Lizenz.

**Code-Standards:** `code-standards/SKILL.md`, Python- und Qualitätsregeln
gelesen. Architektur ✅ vorhandener API-Testpfad; Qualität ✅ erwartetes Rot,
gezieltes Grün und Gesamtlauf; DRY ✅ keine neue Hilfslogik; Dokumentation ✅
Abgleich oben. Frontend/i18n, Shell, CLI, Persistenz und Makefile ➖ nicht
berührt. Lokale Lessons SI-CX-01, SI-R-02 und SI-T-66 gelesen; der Test nutzt
je Fall eine frische temporäre Datenbank und keine Arbeitsdaten.

## Auflösung

**Unabhängiger Review · Claude, 2026-09-28.** Geprüfte Übergabe `78059a8`
gegen ihren Vorgänger auf `t-81-zeitabhaengige-yaml-historientests`.
Ergebnis: **approved.**

- Root Cause im Service selbst nachgelesen, nicht nur behauptet:
  `daily_history.py:_period_start` liefert bei `period == "max"` `None`
  (kein Startdatum), sonst `date.today() - timedelta(days=…)`. Das erklärt
  exakt den Fund: Am 28.09. beginnt das `1m`-Fenster am 28.08. und schließt
  die fixen Fixture-Daten (25.–27.08.) aus.
- Rot/Grün selbst reproduziert statt übernommen (SI-CX-01-Muster): Beide
  `period`-Werte lokal auf `1m` zurückgesetzt — beide Tests schlagen fehl,
  Log zeigt `daily_synced rows=0 start=2026-08-28`, deckungsgleich mit dem
  Ticketbefund. Fix zurückgespielt — beide wieder grün, Arbeitsbaum sauber.
- Testabsicht bleibt erhalten: Beide Docstrings/Assertions prüfen die
  Quellenkette (`answers-never` → `yaml-file`) beziehungsweise die reine
  Dateiquelle, nicht die `1m`-Fensterlogik. `max` ist ein bestehender,
  öffentlich dokumentierter Zeitraumwert (`app/routers/quotes.py:115`), kein
  Sonderpfad für den Test.
- `make test` selbst gelaufen: Backend 1245 bestanden/35 übersprungen,
  Plugin-API 323 bestanden/1 übersprungen, Beispielpaket 50 bestanden,
  Dashboard 385 bestanden — deckungsgleich mit der Übergabe.
  `git diff --check` sauber, `ruff check` sauber. `ruff format --check` findet
  ein vorbestehendes, unverändertes Formatabweichung an anderer Stelle der
  Datei; identisch bereits auf dem Vorgänger-Commit, keine Neuregression
  dieses Diffs.
- Scope wie angekündigt: nur `tests/test_yaml_profile.py`, zwei
  String-Literale geändert, keine neuen Bezeichner, kein Produktcode, keine
  API-/DB-/Konfigurationsänderung. Doku-Abgleich nachvollzogen: `README.md`
  dokumentiert `max` bereits als gültigen `period`-Wert.

`T-81-zeitabhaengige-yaml-historientests.md` ist das einzige Element seiner
`priority_chain`; nach dem Portfolio-Riegel geht der Zustand auf
`portfolio_review` an Mike. Das Ticket bleibt bis zu Mikes Bestätigung in
`30-doing/`.
