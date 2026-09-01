# T-49 · Fachdaten gehören nicht ins Ticketverzeichnis

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Tests + Beispieldaten + Doku) | offen | 3–4 h | Prüfdaten nach `tests/_resources/`, zwei versionierte Betriebsvorlagen nach `examples/` statt einer Datei im Ticketverzeichnis | — |

- **Angelegt:** 2026-08-31, auf Mikes Befund
- **Beauftragt von Mike:** *„Es kann nicht sein, dass wenn ich das yaml-File in
  `_tickets` ändere die Tests auf ROT gehen. Und sollte das Plugin endlich
  fertig sein, wird sich auch das zum Ticket gehörige yaml-File nach `solved`
  bewegen — sprich, alle Tests die auf das File in `_tickets` Bezug nehmen
  werden auf ROT gehen."*
- **Hängt ab von:** nichts. Berührt weder Vertrag noch Laufzeitlogik
- **Reihenfolge:** Vorschlag **direkt nach T-44**, vor T-46 — jede weitere
  Runde, die die Datei anfasst, läuft sonst in dieselbe Falle

**Löst:** Eine Datei dient gerade drei Herren: Sie ist Anhang eines Tickets,
Prüfmittel von zwei Testdateien und Vorlage für den Betrieb. Wer sie in einer
dieser Rollen anfasst, bricht die anderen beiden.

---

## Die Befunde, gemessen

### 1 · Eine Änderung an der Datei macht Tests rot

`tests/test_yaml_profile.py:311` hält den Kurs `94500.00` fest, um zu belegen,
dass er aus der Datei stammt und nicht aus dem Netz. Wer den Wert in der Datei
ändert — aus jedem Grund —, bekommt einen roten Lauf.

Das ist **kein Fehler des Tests**: Er prüft genau das Richtige. Falsch ist,
dass dieselbe Datei gleichzeitig als Spielwiese dient.

### 2 · Ein Umzug nach `solved/` reißt 13 Tests mit

Gegenprobe, nicht Vermutung — die Datei einmal verschoben und den Lauf
angesehen:

```
git mv _tickets/T-37-single-file-sample.yaml _tickets/solved/
→ 13 failed, 23 passed
```

Betroffen sind `tests/test_yaml_profile.py` und `tests/test_error_paths.py`.
Und der Umzug ist kein hypothetischer Fall: Er ist der **vorgesehene**
Abschluss jedes Tickets.

### 3 · Wer sonst noch daran hängt

Vollständiges Inventar, nicht geraten:

| Ort | Art des Zugriffs |
|---|---|
| `tests/test_yaml_profile.py` | liest die Datei, hält Werte fest |
| `tests/test_error_paths.py` | liest die Datei |
| `plugin_api/examples/yaml_file.py` | nennt sie im Docstring |
| `scripts/sources-profile.sh` (Branch `feat/sources-profile-script`) | legt daraus `data/assets.yaml` an |
| `_tickets/T-31…`, `_tickets/T-37…` | beschreiben sie als Beleg |

---

## Zwei Betriebsdateien statt einer — Mikes Frage, geprüft

> *„Eigentlich sollten es ja zwei yaml-Files sein — oder? Eines als Fallback
> für die Online-Version und eines für die yaml-File-Version."*

**Technisch nötig ist es nicht** — der T-42-Lauf hat beide Profile mit
derselben Datei bedient. **Inhaltlich ist es richtig**, und der Grund ist
schärfer als „Ordnung":

Die heutige Beispieldatei führt EUNL, Apple, RBC und BTC-EUR — alles Papiere,
die die Online-Kette selbst beantwortet. Als **Fallback** hinter yfinance
sind diese Einträge nicht bloß überflüssig, sie sind eine Falle: Fällt die
Online-Quelle aus, greift die Kaskade auf die Datei durch und liefert einen
**fest eingetragenen Preis vom 27. August** — plausibel aussehend, ohne
Kennzeichnung, statt eines ehrlichen Ausfalls.

Daraus folgt die Aufteilung nach Zweck, nicht nach Geschmack:

| Datei | Inhalt | Regel |
|---|---|---|
| **Fallback** hinter der Online-Kette | **nur**, was online nicht zu holen ist — die OTC-Anleihe, von Hand gepflegte Historie | Ein Papier, das eine Online-Quelle kennt, gehört **nicht** hinein. Ob sie es kennt, entscheidet die **Auflösung**, nicht die Gattung |
| **Eigenständig**, reines Dateiprofil | der vollständige Bestand samt Kursen, Historie und Devisen | Hier ist Vollständigkeit die Zusage |

## Was entsteht

1. **`tests/_resources/`** — die Prüfdatei, im Besitz der Tests. Werte dort
   sind festgehalten und ändern sich nur mit dem Test, der sie festhält.
2. **`examples/`** — die beiden **versionierten Vorlagen**, die niemand aus
   einem Test liest. Sie sind Vorlagen und keine Betriebsdaten: Die
   Betriebsdatei entsteht daraus im Volume.
3. **`/data/assets.yaml`** — die **ausgewählte Betriebsdatei**. `data/` ist
   absichtlich in `.gitignore`; dort liegt, was der Instanz gehört, und
   `yaml_file.py` erwartet genau diesen Pfad als Vorgabe.
4. **Kein ausführbarer Verweis mehr nach `_tickets/`** — die Tickets
   beschreiben die Datei weiter, aber nichts hängt an ihrem Ort.

---

## Verify

Legende: ✅ live bestätigt · ➖ nicht geprüft.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | `git mv _tickets/*.yaml _tickets/solved/` | **kein** Test wird rot — der Umzug eines Tickets ist folgenlos | ✅ | |
| **2** | `grep` über Tests und Skripte | kein ausführbarer Verweis auf `_tickets/` mehr | ✅ | |
| **3** | Prüfdatei ändern | genau die Tests werden rot, die den Wert festhalten — und nur die | ✅ | |
| **4** | Betriebsdatei ändern | **kein** Test wird rot | ✅ | |
| **5** | Fallback-Vorlage | enthält kein Papier, das die Online-Kette selbst beantwortet | ✅ [^gemessen] | |
| **6** | Online-Profil, Quelle gestört | die Datei springt **nicht** mit einem alten Kurs ein, wo online etwas liefern sollte | ✅ | |
| **7** | reines Dateiprofil mit der eigenständigen Vorlage | alle fünf Rollen werden bedient, wie bisher | ✅ | |
| **8** | `sources-profile.sh` | legt die Betriebsdatei aus der neuen Vorlage an, nicht aus `_tickets/` | ➖ [^script] | |

[^gemessen]: **Meine Einschätzung war falsch, und Codex hat sie gemessen.**
    Ich hatte den Fonds `DE0009848119` mit dem Argument „nicht
    börsengehandelt" in der Fallback-Vorlage gelassen; die Probe am
    2026-09-01 ergibt `resolve_isin()` → `HJUA/XFRA` **mit aktuellem Kurs**.
    Er ist damit genau der Fall, den die Regel verbietet, und ist entfernt.
    Übrig bleibt die Anleihe, für die es wirklich keine Quelle gibt.

[^script]: `scripts/sources-profile.sh` liegt auf dem noch nicht
    zusammengeführten Branch `feat/sources-profile-script` und zeigt dort auf
    den alten Ort. Der Verweis zieht nach, sobald der Branch landet — hier ist
    nichts zu ändern, was es auf diesem Branch nicht gibt.

## Nicht-Ziele

- Keine Änderung am Dateiformat und am Plugin-Vertrag.
- Keine neue Rolle, kein neuer Endpunkt.
- Kein Umbau der Tests über das Verschieben und Umbiegen hinaus.

## Runde 1 · Umgesetzt (2026-08-31)

**Der Umzug ist folgenlos — gemessen, nicht behauptet.** Vier Ticketdateien
samt zwei Smoke-Scripts nach `solved/` verschoben:

```
git mv _tickets/T-37-*.md _tickets/T-45-*.md _tickets/T-22-smoke.sh _tickets/T-35-smoke.sh _tickets/solved/
→ 964 passed, 29 skipped        (vorher: 13 failed)
→ T-22-Smoke aus solved/: 6/6
```

**Und die inhaltliche Zusage, als A/B.** Dieselbe gestörte Online-Quelle,
dieselbe Anfrage, nur die Datei dahinter unterscheidet sich — **je frischer
Datenbank**, weil der erste Anlauf sich eine geteilt hatte und damit nur den
Cache maß:

| Datei hinter der gestörten Quelle | Antwort auf `GET /quote/IE00B4L5Y983` |
|---|---|
| `assets-standalone.yaml` | **200 · 128,21 €** — ein Kurs vom 27. August, als aktueller ausgegeben |
| `assets-fallback.yaml` | **404 · `instrument_not_found`** — ehrlich |

Das ist der Grund für die Aufteilung, in einer Zeile: Dieselbe Störung wird
einmal verschwiegen und einmal gemeldet.

## Auflösung

### Codex-Review Runde 1 · Änderungen angefordert (2026-09-01)

Die Trennung der Test-Fixture ist technisch sauber und die Regression grün.
Die schmale Betriebsvorlage verletzt jedoch ihre eigene Kernregel:
`YFinanceResolver.resolve_isin("DE0009848119")` liefert das vollständige
Listing `HJUA/XFRA`; yfinance lieferte in der Gegenprobe außerdem einen
aktuellen Kurs. Der Fonds darf daher nicht in `assets-fallback.yaml` stehen.

Die Korrektur bleibt eng begrenzt: den Fonds aus der Fallback-Vorlage
entfernen, Kommentar und Matrix `#5` auf den gemessenen Stand bringen. Dazu
die Ortsregel in Ticket und Doku eindeutig machen: versionierte, sichtbare
Vorlagen liegen unter `examples/`; die vom Benutzer ausgewählte Arbeitskopie
liegt als `/data/assets.yaml` im absichtlich ignorierten Betriebsvolume.
Keine Laufzeitlogik, kein neues Testsystem und kein weiterer Umbau.

## Runde 2 · Der Fonds war eine Schätzung (2026-09-01)

**Codex hat gemessen, wo ich eingeschätzt habe, und die Einschätzung war
falsch.** Ich hatte `DE0009848119` mit dem Argument „nicht börsengehandelt" in
der Fallback-Vorlage gelassen und die Unsicherheit nur als ⚠️ vermerkt. Die
Probe: `resolve_isin()` liefert `HJUA/XFRA`, yfinance dazu einen aktuellen
Kurs. Der Eintrag war damit exakt die Falle, die diese Datei verbietet — er ist
raus.

**Die Lehre steht in der Vorlage selbst, nicht nur hier:** Ob eine
Online-Quelle ein Papier führt, beantwortet die **Auflösung**, nicht die
Gattung. „Nicht börsengehandelt" ist eine Eigenschaft des Papiers, keine
Aussage über die Quellenlage.

Nachgemessen mit der bereinigten Vorlage, dieselbe gestörte Online-Quelle, je
frischer Datenbank:

| Papier | `assets-standalone.yaml` | `assets-fallback.yaml` |
|---|---|---|
| ETF `IE00B4L5Y983` | 200 · 128,21 € | **404** |
| Fonds `DE0009848119` | 200 · 142,50 € | **404** |
| Anleihe `DE0001102531` | 200 · 99,42 € | 200 · 99,42 € |

Die Anleihe bleibt — für sie gibt es wirklich keine Quelle, und genau dafür ist
die Datei da. Alles andere schweigt jetzt dort, wo online etwas liefern sollte.

**Die Ortsbeschreibung war ebenfalls schief.** Ticket und STATUS sprachen von
„Betriebsdaten nach `data/`", während dort nichts Versioniertes liegen kann:
`data/` ist absichtlich ignoriert. Richtig ist die Zweiteilung — zwei
**versionierte Vorlagen** unter `examples/`, daraus entsteht die **eine
Betriebsdatei** `/data/assets.yaml` im Volume der Instanz.
