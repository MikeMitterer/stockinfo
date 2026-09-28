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
