# T-19 · Neu auflösen, ohne Messreihen zu vermischen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | offen | 4 h | Korrekturweg, Historien-Regel, Herkunft, Quellen-Übersicht | — |

**Löst:** Der einzige Weg, eine falsche Auflösung zu korrigieren, ist heute
`DELETE /instruments/{isin}` — und der kostet Kurshistorie, Tageskurse und alle
von Hand gepflegten Kennzahlen.

> **Ziel korrigiert (Codex-Review vom 2026-08-19).** Die erste Fassung dieses
> Tickets verlangte „nur Symbol, Börse und Gattung ändern, alles andere behalten".
> Das ist **falsch** und wäre gefährlicher als der heutige Zustand — siehe
> „Warum ‚kein Datenverlust' das falsche Ziel war".

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

**Hängt an:** nichts. Sollte **vor** dem Plugin-System stehen.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Papier neu auflösen, Listing bleibt **gleich** (Ticker, MIC, Währung) | Historie und gepflegte Kennzahlen bleiben vollständig | | |
| 2 | Papier neu auflösen, Listing **wechselt** (z.B. `.L`/GBp → `.DE`/EUR) | alte Kursreihe wird **nicht** mit der neuen vermischt | | |
| 3 | nach #2: `GET /quote/{isin}/daily` | keine Reihe, die Pence und Euro mischt | | |
| 4 | nach #2: Volatilität | wird neu aufgebaut, statt aus gemischten Werten zu stammen | | |
| 5 | nach #2: `daily_meta` | behauptet keine Zeiträume mehr als synchronisiert, die zum alten Listing gehören | | |
| 6 | nach #2: manuelle Kennzahlen (TER etc.) | bleiben — sie hängen am Papier, nicht am Listing | | |
| 7 | Detailbereich einer Zeile | zeigt „aufgelöst durch: openfigi" (o.ä.) | | |
| 8 | `GET /sources` | listet alle Quellen je Rolle, mit Reihenfolge und `configured` | | |
| 9 | `make test` | Backend, Plugin-API und Dashboard grün | | |

---

## Details

### Warum „kein Datenverlust" das falsche Ziel war

`quotes` und `daily_closes` hängen **nur** an `instrument_id`. Beide haben zwar
eine `currency`-Spalte, aber:

* `UNIQUE (instrument_id, date)` — für einen Tag kann es nur **einen**
  Schlusskurs geben, egal aus welcher Notierung
* die Volatilitätsberechnung ignoriert die Währung vollständig
  (`app/services/quote_cache.py:433`):

```python
closes = [row["close"] for row in rows if row.get("close") is not None]
return annualized_volatility(closes)
```

Wechselt ein Papier von London (GBp) nach Xetra (EUR), stünde in derselben Reihe
ein Sprung von rund **5400 auf 60**. Als Tagesrendite gelesen sind das −99 %; die
Volatilität wird unbrauchbar, und der Chart zeigt einen Absturz, den es nie gab.

**Alles zu behalten ist also schlimmer als zu löschen** — es sieht plausibel aus.

### Was stattdessen gilt

Zwei Fälle, sauber getrennt:

| Fall | Kursreihen | Manuelle Kennzahlen |
|---|---|---|
| Listing **unverändert** (Ticker, MIC, Währung gleich) | bleiben | bleiben |
| Listing **gewechselt** | werden invalidiert, `daily_meta` zurückgesetzt | bleiben |

Die manuellen Kennzahlen hängen am **Papier**, nicht an der Notierung: Ein TER
ändert sich nicht, weil dasselbe Papier an einer anderen Börse gehandelt wird.
Genau die gehen heute beim Löschen mit verloren — und genau die sind es, die
niemand nachträgt.

**Entschieden (Codex, 2026-08-20): löschen, nicht archivieren.** Die alte
Kursreihe wird verworfen, und zwar erst **nach ausdrücklicher Bestätigung** in
der Oberfläche — mit Angabe, wie viele Punkte betroffen sind. Eine
Listing-Generation an `quotes`/`daily_closes` wäre sauberer, verlangt aber eine
Generationslogik in jeder Abfrage; das ist viel Aufwand für einen seltenen
Vorgang. Archivierung bleibt ein späteres Feature und ist **keine**
Voraussetzung für das Plugin-System.

### Der Korrekturweg selbst

`POST /resolve/{isin}` löst neu auf, vergleicht das Ergebnis mit dem
gespeicherten Listing und wendet die Regel oben an. Der Endpunkt meldet zurück,
was passiert ist — unverändert oder gewechselt samt Folge —, damit die
Oberfläche vor dem Verwerfen fragen kann.

### Niemand sieht, wer aufgelöst hat

`CompositeResolver` gibt das Ergebnis zurück, nicht seine Herkunft.

**Weg:** Spalte `resolved_by` am Instrument, angezeigt im Detailbereich.

### „Ich habe das Plugin installiert und es passiert nichts"

`GET /sources` zeigt je Rolle die Kette in ihrer Reihenfolge, mit Name, Art und
Konfigurationsstand. Ohne diese Ansicht ist jede Ferndiagnose Blindflug.

**Anmerkung aus der Review:** `is_configured()` liefert nur `bool` und kann
keinen Grund nennen. Für die Anzeige braucht es entweder ein strukturiertes
Ergebnis oder eine zusätzliche Diagnosemethode — Entscheidung offen, siehe Spec.

---

## Auflösung

_(offen)_
