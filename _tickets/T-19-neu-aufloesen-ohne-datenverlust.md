# T-19 · Neu auflösen, ohne die Historie zu verlieren

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | offen | 2 h | Korrekturweg, Herkunft, Quellen-Übersicht | — |

**Löst:** Der einzige Weg, eine falsche Auflösung zu korrigieren, ist heute
`DELETE /instruments/{isin}` — und der kostet alles. Solange Quellenwechsel
Ausnahmefälle sind, fällt das kaum auf; sobald Plugins dazukommen, wird es zum
Normalvorgang.

**Hängt an:** nichts. Sollte **vor** dem Plugin-System stehen, nicht danach.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Papier mit Historie und eigenem TER → `POST /resolve/{isin}` | Symbol/Börse werden neu bestimmt, **Historie und TER bleiben** | | |
| 2 | dasselbe Papier, `GET /quote/{isin}/history` | Zeitreihe unverändert lang wie vorher | | |
| 3 | Detailbereich einer Zeile | zeigt „aufgelöst durch: openfigi" (o.ä.) | | |
| 4 | `GET /sources` | listet alle Quellen je Rolle, mit Reihenfolge und `configured` | | |
| 5 | `GET /sources` bei fehlendem OpenFIGI-Key | die Quelle erscheint mit `configured: false` und Begründung | | |
| 6 | `make test` | Backend grün; Dashboard grün | | |

```bash
# #1/#2 — vor und nach dem Neu-Auflösen zählen
curl -s "http://localhost:8000/quote/IE00B4L5Y983/history?limit=500" | python3 -c "import sys,json; print('Punkte:', len(json.load(sys.stdin)))"
curl -s -X POST "http://localhost:8000/resolve/IE00B4L5Y983" | python3 -m json.tool
curl -s "http://localhost:8000/quote/IE00B4L5Y983/history?limit=500" | python3 -c "import sys,json; print('Punkte:', len(json.load(sys.stdin)))"

# #4/#5
curl -s "http://localhost:8000/sources" | python3 -m json.tool
```

---

## Details

### Löschen ist zu grob

Am Instrument hängen **vier** Tabellen per `ON DELETE CASCADE` (`app/db.py`):

```
quotes                → die gesamte Kurshistorie
daily_closes          → Tages-Schlusskurse (Basis der Volatilität)
instrument_overrides  → die von Hand gepflegten Kennzahlen
daily_meta            → der Sync-Stand
```

`set_isin` korrigiert nur die ISIN; für Symbol, Börse oder Gattung gibt es keinen
Weg außer Löschen. In `repository.py:314` steht bereits ein Kommentar, dass genau
dieser Datenverlust schon einmal eingetreten ist.

**Weg:** `POST /resolve/{isin}` — löst neu auf und setzt **nur** Symbol, Börse und
Gattung. Alles andere bleibt stehen. Eine Repository-Methode, ein Endpunkt, ein
Knopf im Detailbereich.

### Niemand sieht, wer aufgelöst hat

`CompositeResolver` gibt das Ergebnis zurück, nicht seine Herkunft. Mit mehreren
Quellen ist „wer war das" die erste Frage bei jedem Zweifel.

**Weg:** Spalte `resolved_by` am Instrument, gefüllt beim Auflösen, angezeigt im
Detailbereich neben „Quelle".

### „Ich habe das Plugin installiert und es passiert nichts"

Das wird die häufigste Rückmeldung, sobald andere Quellen beisteuern — und sie hat
meist zwei harmlose Ursachen: Die Quelle ist gar nicht geladen, oder das Papier
wird nicht neu aufgelöst (siehe oben).

**Weg:** `GET /sources` zeigt je Rolle die Kette in ihrer Reihenfolge, mit Name,
Art, `configured` und einer Begründung, wenn nicht. Ohne diese Ansicht ist jede
Ferndiagnose Blindflug.

---

## Auflösung

_(offen)_
