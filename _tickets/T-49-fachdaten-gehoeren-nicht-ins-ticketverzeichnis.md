# T-49 · Fachdaten gehören nicht ins Ticketverzeichnis

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Tests + Beispieldaten + Doku) | offen | 3–4 h | Prüfdaten nach `tests/_resources/`, Betriebsdaten nach `data/`, und zwei getrennte Betriebsdateien statt einer | — |

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
| **Fallback** hinter der Online-Kette | **nur**, was online nicht zu holen ist — die OTC-Anleihe, von Hand gepflegte Historie | Ein Papier, das eine Online-Quelle kennt, gehört **nicht** hinein |
| **Eigenständig**, reines Dateiprofil | der vollständige Bestand samt Kursen, Historie und Devisen | Hier ist Vollständigkeit die Zusage |

## Was entsteht

1. **`tests/_resources/`** — die Prüfdatei, im Besitz der Tests. Werte dort
   sind festgehalten und ändern sich nur mit dem Test, der sie festhält.
2. **`data/`** — die Betriebsdateien, die niemand aus einem Test liest.
   `yaml_file.py` erwartet dort ohnehin schon `/data/assets.yaml`.
3. **Beide Betriebsvorlagen** als Beispiel mit den Regeln von oben; die
   Autorendoku nennt den Unterschied.
4. **Kein ausführbarer Verweis mehr nach `_tickets/`** — die Tickets
   beschreiben die Datei weiter, aber nichts hängt an ihrem Ort.

---

## Verify

Legende: ✅ live bestätigt · ➖ nicht geprüft.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | `git mv _tickets/*.yaml _tickets/solved/` | **kein** Test wird rot — der Umzug eines Tickets ist folgenlos | ➖ | |
| **2** | `grep` über Tests und Skripte | kein ausführbarer Verweis auf `_tickets/` mehr | ➖ | |
| **3** | Prüfdatei ändern | genau die Tests werden rot, die den Wert festhalten — und nur die | ➖ | |
| **4** | Betriebsdatei ändern | **kein** Test wird rot | ➖ | |
| **5** | Fallback-Vorlage | enthält kein Papier, das die Online-Kette selbst beantwortet | ➖ | |
| **6** | Online-Profil, Quelle gestört | die Datei springt **nicht** mit einem alten Kurs ein, wo online etwas liefern sollte | ➖ | |
| **7** | reines Dateiprofil mit der eigenständigen Vorlage | alle fünf Rollen werden bedient, wie bisher | ➖ | |
| **8** | `sources-profile.sh` | legt die Betriebsdatei aus der neuen Vorlage an, nicht aus `_tickets/` | ➖ | |

## Nicht-Ziele

- Keine Änderung am Dateiformat und am Plugin-Vertrag.
- Keine neue Rolle, kein neuer Endpunkt.
- Kein Umbau der Tests über das Verschieben und Umbiegen hinaus.

## Auflösung

_(offen)_
