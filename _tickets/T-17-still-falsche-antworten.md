# T-17 · Still falsche und lückenhafte Antworten

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | offen | 90 min | drei Fehler im Antwortpfad, kein Umbau | — |

**Löst:** Drei Stellen, an denen die App etwas Falsches speichert oder ausliefert,
ohne dass es auffällt. Alle drei am 2026-08-19 gemessen, alle drei vorbestehend
und unabhängig vom Plugin-Vorhaben.

**Hängt an:** nichts. Kann sofort laufen und sollte es auch — Nummer 1 verfälscht
gespeicherte Daten.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `GET /quote/FR0000121014` (LVMH), danach `GET /instruments` | gespeicherte ISIN ist **FR**0000121014, nicht die kanadische Zweitnotierung | | |
| 2 | Server-Log beim selben Abruf | Abweichung zwischen eingegebener und gemeldeter ISIN wird als Warnung protokolliert | | |
| 3 | `GET /quote/CA78012H5675` mit `DEFAULT_EXCHANGE=XTSE` | liefert die Stammaktie, **nicht** `RY V3.65 PERP BB.TO` | | |
| 4 | Papier abrufen, TTL ablaufen lassen, erneut abrufen | `ter` in der Antwort entspricht dem Wert in `GET /instruments` | | |
| 5 | `./_tickets/T-16-smoke.sh --run` | Zeile `#5c` ist grün | | |
| 6 | `make test` | Backend grün, neue Tests je Fehler | | |

```bash
# #1 — die eingegebene ISIN muss gewinnen
curl -s "http://localhost:8000/quote/FR0000121014" | python3 -m json.tool | grep isin
curl -s "http://localhost:8000/instruments" | python3 -c "import sys,json; print([i['isin'] for i in json.load(sys.stdin)])"

# #3 — Gattung statt erstem Treffer
curl -s "http://localhost:8000/quote/CA78012H5675" | python3 -m json.tool | grep -E 'symbol|name'

# #4/#5
./_tickets/T-16-smoke.sh --run
```

---

## Details

### 1 — Eine eingegebene ISIN wird still überschrieben

`app/services/quote_service.py`, `_build`: `isin = raw.isin or resolved.isin` —
**`raw` gewinnt.** `_safe_isin` (`yfinance_provider.py:171`) filtert nur `'-'`.

Gemessen:

```
MC.PA   yfinance: CA50244Q1037 = LVMH MOET HENNESSY LOUIS VUI   ← kanadisches DR
        tatsächlich: FR0000121014 = LVMH MOET HENNESSY LOUIS VUI
7203.T  yfinance: CA89238H1091 = TOYOTA MOTOR CORP              ← kanadisches DR
        tatsächlich: JP3633400001 = TOYOTA MOTOR CORP
```

Der Name stimmt, die Gattung nicht. Beim Draufschauen fällt nichts auf.

**Weg:** `resolved.isin` gewinnt, wenn sie aus einer Nutzereingabe stammt.
Weicht `raw.isin` ab, wird das protokolliert statt still übernommen.

### 2 — `_extract_ticker` nimmt den ersten Treffer

`app/providers/openfigi_provider.py:69`. Gemessen mit korrekter ISIN und
richtiger Börse:

```
OpenFigiResolver(default_exchange=XTSE) → RY V3.65 PERP BB.TO
```

Eine ewige Vorzugsanleihe statt der Stammaktie. OpenFIGI liefert
`securityType` — derselbe Fix wie in `_passendster` (Commit `5ec9c37`), nur
eine Schicht tiefer: Gattung als Feinauswahl, nicht als Bedingung.

### 3 — Die Antwort hält den gespeicherten Stand nicht

Kurs-TTL abgelaufen, Metadaten-TTL noch frisch: `_build` fragt justETF nicht
(richtig), die frische Antwort hat deshalb keine ETF-Felder, und `_save_fresh`
reicht **genau diese** an den Client durch. Gemessen: `ter` in der Antwort
`null`, in der Datenbank `0.2`.

**Weg:** In `_save_fresh` den gespeicherten Stand über die frische Antwort
legen, so wie `_with_overrides` es für die manuellen Werte tut.

---

## Auflösung

_(offen)_
