---
schema_version: 1
id: SI-P-05
project: stockinfo
kind: pattern
discovery_phase: mixed
affected_work:
- implementation
- tests
- handoff
subject_author: claude
discovered_by: unknown
recorded_by: unknown
structured_by: codex
prevention_roles:
- implementer
- reviewer
provenance:
  project: stockinfo
  file: _tickets/.agents/CLAUDE-LESSONS.md
  heading: P-05 · Ein abgebrochener Prüflauf meldet sich als bestanden
  revision: 5fc549b84ae7d449780b856d3046230da6c5bf2d
  file_sha256: f506fd721ef98bf9c51bff326b06c22a39c24eee57f14daa4e0e93f06bd78dff
  section_sha256: 7b664489f37019ff228f833681630966f9cba13c0faeadfed86dec6397feafb4
  captured_at: '2026-09-11'
---

# SI-P-05 · Ein abgebrochener Prüflauf meldet sich als bestanden

**Implementer-Regel:** Geplante und tatsächlich ausgeführte Fälle abgleichen; Abbrüche als Fehler melden.

**Verifier-Prüfung:** Frühen Abbruch auslösen und Exit-Code sowie Abschlussmeldung prüfen.

## Originalbelege und Einordnung

**Erkennungsregel:** Ein Prüf-Script zählt die Ergebnisse, die es bekommen hat,
und schließt daraus auf Vollständigkeit. Bricht der geprüfte Vorgang mitten im
Lauf ab, sieht das Ergebnis aus wie ein vollständiger Lauf ohne Fehler — nur
mit weniger Zeilen. Verstärkt wird es, wenn die Fehlerausgabe nur dann gezeigt
wird, wenn **gar nichts** ankam.

**Prüffrage:** Woran erkennt das Script, dass der Lauf **zu Ende** gelaufen ist
— und nicht nur, dass das Angekommene grün war? Es braucht eine Schlussmarke
oder eine erwartete Anzahl; die Zahl im Erfolgssatz ist kein Beleg, sie zählt
nur mit. Gegenprobe: einen Abbruch mitten im Lauf erzwingen und nachsehen, ob
das Script rot wird.

**Beleg:** T-21 Teil 2b, 2026-08-23: Der Umzug von `figi_id_type` zum
OpenFIGI-Provider entfernte eine Spalte, die `T-21-smoke.sh` in seinem eigenen
Orakel noch las. Das Script stürzte nach vier von neun Prüfungen mit einer
`AttributeError` ab, die Fehlerausgabe blieb verborgen — und es meldete
„4 Checks bestanden, keine Fehler". Die vier Zeilen davor waren echt; die fünf
fehlenden fielen nur auf, weil die Ticketfußnote neun nannte.

**Neuer Beleg:** T-22 Runde 1, Commit `20af8fa`: Das neue Smoke-Script
kommentierte ausdrücklich, seine Schlussmarke verhindere einen grünen
Teil-Lauf. Scheitert `startServer()` jedoch vor `report()`, kehrt nur die
Check-Funktion mit 1 zurück; `runChecks()` läuft ohne `set -e` weiter,
`COUNT_FAIL` bleibt unverändert und der Erfolg verlangt keine erwartete Anzahl
von fünf Checks. Ein später vollständig laufender Rest kann deshalb mit vier
Checks und „keine Fehler" grün enden.

**Neuer Beleg:** T-27a Runde 1, Commit `6121a94`: Der öffentliche
Szenario-Runner liefert bei `only_real=True` und null mit `real_ok`
freigegebenen Fällen eine leere Finding-Liste — dieselbe Erfolgsform wie nach
einem vollständigen grünen Lauf. Der Test schreibt dieses Verhalten sogar als
Erwartung fest. T-27b könnte damit „Real" melden, ohne einen Anbieter gefragt
zu haben.

**Neuer Beleg:** T-37, Commit `d313318`: `checkTestData` entscheidet allein
an leerem Standardoutput über Erfolg. Wirft der eingebettete Parser etwa bei
`float("not-a-number")`, endet Python mit Status 1 und leerem Output; die
Shell ignoriert den Status und meldet Check `#0` grün. Die erwartete Gesamtzahl
17 schützt hier nicht, weil der fehlerhaft als Erfolg gezählte Check vorhanden
ist.

**Neuer Beleg:** T-36/T-37 Runde 3, Commit `cc0f028`: Die Korrektur prüft den
Exitstatus beim positiven Check, erklärt im neuen Negativcheck `#0b` aber
ausdrücklich jeden von Null verschiedenen Parserstatus zum Erfolg. Genau der
bekannte Abbruch an `float("keine-zahl")` ergibt damit 20/20 und die erfundene
Aussage, alle drei Mutanten seien erkannt worden. Die Abbrucherkennung wurde
vom Prüfling in die Gegenprobe verschoben, nicht in einen roten Lauf verwandelt.

**Neuer Beleg:** T-42 Runde 7, Commit `c046297`: `T-22-smoke.sh` meldete sechs
von sechs Checks und trug im Kopf weiterhin Verify `#2b`. Tatsächlich liefen
`#1`, `#2`, `#3`, `#4`, das neue `#4b` und `#5`; `#2b` lief gar nicht. Die
erwartete **Anzahl** stimmte damit exakt, obwohl eine zugesagte Identität durch
eine andere ersetzt worden war. Eine Schlussmarke braucht neben der Zahl auch
die erwarteten Check-IDs.

**Nachbarschaft zu P-01:** Dort wird die Testtiefe in der Übergabe
überzeichnet. Hier überzeichnet sich das **Werkzeug** — die Übergabe gäbe
seine Zahl gutgläubig weiter.
