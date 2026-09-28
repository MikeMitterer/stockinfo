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

**Einordnung:** Eigenes Testproblem, kein offener T-80-Produktbefund. Dieses
Backlog-Ticket startet keine Umsetzung ohne Einplanung in `STATUS.md`.
