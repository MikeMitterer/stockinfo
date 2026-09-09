# T-17 · Still falsche und lückenhafte Antworten

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | codex-abgenommen | 90 min | drei Fehler im Antwortpfad, kein Umbau | — |

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
| 1 | `GET /quote/FR0000121014` (LVMH), danach `GET /instruments` | gespeicherte ISIN ist **FR**0000121014, nicht die kanadische Zweitnotierung | ✅ [^1] | |
| 2 | Server-Log beim selben Abruf | Abweichung zwischen eingegebener und gemeldeter ISIN wird als Warnung protokolliert | ✅ [^1] | |
| 3a | `GET /quote/CA78012H5675` mit `DEFAULT_EXCHANGE=XTSE` | kein erfundenes Yahoo-Symbol; der Fallback wird aufgerufen und bleibt leer → sauber 404 | ✅ [^2] | |
| 3b | `GET /instruments` danach | kein Symbol mit Leerzeichen im Bestand | ✅ [^2] | |
| 3c | `GET /quote/CA7800871021` (Stammaktie) | löst unverändert auf `RY.TO` auf | ✅ [^2] | |
| 4 | Papier abrufen, Kurs-TTL ablaufen lassen, erneut abrufen | `ter` in der Antwort entspricht dem Wert in `GET /instruments` | ✅ [^3] | |
| 5 | `./_tickets/40-done/T-16-smoke.sh --run` | Zeile `#5c` ist grün | ✅ [^4] | |
| 6 | `make test` | Backend grün, neue Tests je Fehler | ✅ [^5] | |

```bash
./_tickets/40-done/T-17-smoke.sh --run    # #1, #2, #3a-c, #4, #6 — eigener Server, temporäre DB
./_tickets/40-done/T-16-smoke.sh --run    # #5
```

[^1]: `./_tickets/40-done/T-17-smoke.sh --run`, Lauf 1 (Vorgabebörse `XPAR`):
    `#1a .isin = FR0000121014`, `#1b` dieselbe ISIN in `/instruments`,
    `#2` im Server-Log
    `[warning] isin_abweichung angefragt=FR0000121014 gemeldet=CA50244Q1037 symbol=MC.PA`.
    Code: `_isin_of` in `app/services/quote_service.py`. Vier Unit-Tests,
    davon zwei zuerst rot gesehen; die anderen beiden sind Gegenproben
    (übereinstimmende ISIN schweigt, Abruf per Symbol behält die
    Anbieter-ISIN).
[^2]: **Die ursprüngliche Zeile ist ersetzt** — ihre Annahme war widerlegt,
    Messung und Begründung stehen unten unter „2". `T-17-smoke.sh` Lauf 2
    (`XTSE`): `#3a` HTTP 404, `#3b` Symbole mit Leerzeichen: 0, `#3c`
    `.symbol = RY.TO`. Der Filter macht die Vorzugsaktie **nicht** abrufbar —
    Yahoos ISIN-Suche kennt sie ebenfalls nicht. Er sorgt allein dafür, dass
    die Kette weiterläuft. Belegt durch
    `test_bloomberg_bezeichner_laesst_den_fallback_ans_werk` (zuerst rot):
    Dort laufen **beide** Resolver echt, ersetzt sind nur die zwei
    Außengrenzen (`httpx.post` und `yf.Search`); die aufzeichnende Suche zeigt,
    dass der Yahoo-Resolver mit der ISIN aufgerufen wurde, und die leere
    Trefferliste bildet die Live-Messung ab.
[^3]: `T-17-smoke.sh` Lauf 3 (`XETR`, `CACHE_TTL_HOURS=0`):
    `ter: 1. Abruf=0.2, 2. Abruf=0.2, DB=0.2`. Gegenprobe gemacht — mit
    zurückgenommenem Fix (`git stash` auf `quote_cache.py`) meldet dieselbe
    Zeile rot. Dazu drei Unit-Tests, darunter die Gegenprobe, dass eine
    **vollständige** Antwort einen Wert weiterhin leeren darf.
[^4]: Grün: `ter: Antwort=0.2, DB=0.2`. Die Zeile **zeigt den Fehler auch** —
    gegengeprüft mit `git checkout 84c9c2d^ -- app/services/quote_cache.py`:
    dann meldet sie rot. Ich hatte hier zuerst das Gegenteil behauptet und
    dabei eine 6-Stunden-TTL unterstellt; `T-16-smoke.sh` startet seinen
    Server aber mit `CACHE_TTL_HOURS=0`, also geht auch der zweite Abruf live
    und trifft genau den Fall. `T-17-smoke.sh #4` prüft dasselbe noch einmal
    über die ISIN — doppelt, aber nicht überflüssig: dort steht die
    Vorgabebörse fest, hier hängt sie an der Umgebung.
[^5]: `.venv/bin/pytest tests/ -q` → `256 passed, 1 warning in 1.13s`,
    darunter zwölf neue Tests. Dashboard-Tests unberührt (kein
    Frontend-Anteil).

Von Hand gegen einen laufenden Stack (`make dev-up`) — die Vorgabebörse
entscheidet mit, deshalb nennt jede Zeile sie:

```bash
# #1 — die eingegebene ISIN muss gewinnen (DEFAULT_EXCHANGE=XPAR)
curl -s "http://localhost:8000/quote/FR0000121014" | python3 -m json.tool | grep isin
curl -s "http://localhost:8000/instruments" | python3 -c "import sys,json; print([i['isin'] for i in json.load(sys.stdin)])"

# #3a/#3c — kein erfundenes Symbol, Stammaktie unverändert (DEFAULT_EXCHANGE=XTSE)
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/quote/CA78012H5675"
curl -s "http://localhost:8000/quote/CA7800871021" | python3 -m json.tool | grep symbol

# #3b — kein Bloomberg-Bezeichner im Bestand
curl -s "http://localhost:8000/instruments" | python3 -c "import sys,json; print([i['symbol'] for i in json.load(sys.stdin) if ' ' in i['symbol']])"
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

**Die Annahme trägt nicht — am 2026-08-21 nachgemessen.** Sie stand hier so:

> `app/providers/openfigi_provider.py:69`. Gemessen mit korrekter ISIN und
> richtiger Börse: `OpenFigiResolver(default_exchange=XTSE) → RY V3.65 PERP BB.TO`.
> Eine ewige Vorzugsanleihe statt der Stammaktie. OpenFIGI liefert
> `securityType` — derselbe Fix wie in `_passendster`, nur eine Schicht tiefer.

OpenFIGI liefert zu `CA78012H5675` an `XTSE` **genau einen** Treffer:

```json
{ "ticker": "RY V3.65 PERP BB", "name": "ROYAL BANK OF CANADA",
  "securityType": "PUBLIC", "marketSector": "Pfd",
  "securityType2": "Preferred Stock", "exchCode": "TORONTO" }
```

Es gibt keinen zweiten Treffer, unter dem die Stammaktie läge. `results[0]` ist
hier nicht die falsche Wahl, sondern die einzige: **die ISIN gehört der
Vorzugsaktie.** Die Stammaktie hat eine eigene — `CA7800871021`, und die löst
schon heute richtig auf:

```
CA78012H5675 → RY V3.65 PERP BB.TO   (Vorzugsaktie, 1 Treffer)
CA7800871021 → RY.TO                  (Stammaktie, 1 Treffer)
```

Eine Gattungs-Feinauswahl hätte also nichts zu wählen. Verify-Zeile #3 verlangt
ein Ergebnis, das nicht nur unerreichbar, sondern **sachlich falsch** wäre.

**Was stattdessen echt kaputt ist.** Der FIGI-Ticker ist ein
Bloomberg-Bezeichner, kein Yahoo-Symbol. Der Resolver klebt das Börsensuffix
an und gibt ihn weiter:

```
ResolvedInstrument(symbol='RY V3.65 PERP BB.TO', exchange='Toronto')
yfinance → HTTP 404: Quote not found for symbol: RY V3.65 PERP BB.TO
```

Weil OpenFIGI „getroffen" hat, greift der Yahoo-Fallback im
`CompositeResolver` nicht mehr — der prüft nur auf ``None``. Das Papier ist
damit unauflösbar, obwohl die zweite Quelle nie gefragt wurde. Falsche Daten
entstehen dabei nicht; es bleibt bei 404 (Smoke `#4b`).

**Umgesetzt** (Entscheidung Mike, 2026-08-21; von Codex gegengeprüft):
`_extract_ticker` verwirft einen Treffer, dessen `ticker` kein Yahoo-Symbol
sein *kann*, und liefert ``None`` — dann läuft die Kette weiter zum
Yahoo-Fallback. Geprüft wird die Zeichenmenge, nicht `marketSector`:
Vorzugsaktien und Anleihen sind handelbare Papiere, die aufnehmbar sein
sollen, sobald ein brauchbares Symbol vorliegt.

**Was der Filter nicht leistet.** Er ist eine Plausibilitätsprüfung. Yahoos
ISIN-Suche findet `CA78012H5675` ebenfalls nicht (Codex-Live-Messung: `[]`,
auch `RY-PH.TO` → 404). Das Papier bleibt also unauflösbar; der Unterschied
ist, dass die Kette jetzt bis zum Ende läuft und sauber 404 meldet, statt an
einem Symbol hängenzubleiben, das es nicht gibt.

**Was hier bewusst nicht passiert.** Die eigentliche Ursache ist, dass
StockInfo einen Open-Symbology-Bezeichner als Yahoo-Symbol liest und blind ein
Börsensuffix anhängt. OpenFIGI ordnet Kennungen zu — ISIN, FIGI, Gattung,
Handelsplatz — und ist kein Symbol-Resolver. Die saubere Trennung

```
Instrumentidentität: ISIN / FIGI / Typ
Listingidentität:    kanonischer Ticker + MIC
Provider-Alias:      Provider + dessen eigenes Symbol
```

gehört in die Identitäts- und Plugin-Tickets (T-21 ff.), nicht in T-17.

**Folge für T-18:** Dessen Verify #1 erwartet, dass `CA78012H5675` über die
Heimatbörse auflösbar wird. Das trifft nicht zu — die Kaskade landet bei
derselben Vorzugsaktie ohne Yahoo-Symbol. Die Zeile gehört auf ein Papier
umgestellt, das den Kanada-Fall wirklich zeigt.

### 3 — Die Antwort hält den gespeicherten Stand nicht

Kurs-TTL abgelaufen, Metadaten-TTL noch frisch: `_build` fragt justETF nicht
(richtig), die frische Antwort hat deshalb keine ETF-Felder, und `_save_fresh`
reicht **genau diese** an den Client durch. Gemessen: `ter` in der Antwort
`null`, in der Datenbank `0.2`.

**Weg:** In `_save_fresh` den gespeicherten Stand über die frische Antwort
legen, so wie `_with_overrides` es für die manuellen Werte tut.

**Umgesetzt** als `_keep_stored_metadata`. Überlagert wird unter **derselben
Bedingung und mit derselben Feldmenge**, unter der das Repository die Spalten
schützt — `PROTECTED_META_FIELDS` ist jetzt einmal definiert und wird von
beiden Seiten benutzt. Zwei getrennte Listen wären auseinandergelaufen, und die
Antwort widerspräche der Zeile daneben.

Gefüllt werden nur Lücken: Eine **vollständige** Antwort bleibt unangetastet,
sonst ließe sich eine Kennzahl nie wieder loswerden. Geprüft wird auf ``None``
und nicht auf Falschheit, damit „ausschüttend" (`accumulating=False`) seinen
Sinn behält. Ausnahme ist `source` — es beschriftet die überlagerten Felder und
stünde sonst auf „yfinance" über Werten von justETF.

Derselbe Fehler steckte im Refresh-Pfad (`_save_fresh_with_volatility`) und ist
dort mitbehoben.

---

## Auflösung

**Stand 2026-08-21 — umgesetzt, von Codex in Runde 2 abgenommen.**

Ohne sachliche Findings, auf Commit `1a2f2bd`. Codex hat unabhängig
nachgerechnet: die drei Zieltests (67 bestanden), Ruff über die berührten
Dateien, `bash -n` für beide Prüf-Scripts, `make test` (256 + 36 + 230) und
`./_tickets/40-done/T-17-smoke.sh --run` (8/8). Die `Human`-Spalte bleibt für eine
spätere, von Mike ausdrücklich gewünschte menschliche Abnahme leer.

Branch `t-17-still-falsche-antworten`.

| Fehler | Datei | Kern der Änderung |
|---|---|---|
| 1 ISIN wird überschrieben | `app/services/quote_service.py` | `_isin_of` — die aufgelöste ISIN gewinnt, Abweichung wird protokolliert |
| 2 unbrauchbarer FIGI-Ticker | `app/providers/openfigi_provider.py` | `_is_yahoo_compatible_symbol` — Treffer, der kein Symbol sein kann, wird verworfen |
| 3 Antwort hält den Stand nicht | `app/services/quote_cache.py`, `app/repository.py` | `_keep_stored_metadata` + `PROTECTED_META_FIELDS` als gemeinsame Feldmenge |

Zwölf neue Tests in `tests/test_quote_service.py`, `tests/test_quote_cache.py`,
`tests/test_providers.py` und `tests/test_resolver.py`; jeder zuerst rot
gesehen, wo er ein Verhalten ändert. Suite: `256 passed`.

Prüf-Script `T-17-smoke.sh` (drei Läufe, je eigene Vorgabebörse) — acht Checks
grün. Es wandert mit dem Ticket nach `solved/`.

**Nach Codex-Review Runde 1** (`changes_requested`, drei Punkte, alle
übernommen):

- Das Script beendete am Ende jedes Laufs **alles**, was auf Port 8766 lauschte
  — auch einen fremden Prozess, etwa Mikes Entwicklungsserver. Bei belegtem
  Port hätte der Health-Check zudem die fremde Instanz für die eigene halten
  können. Jetzt bricht es bei belegtem Port ab (`requirePortIsFree`), beendet
  nur die selbst gestartete PID, und der Port lässt sich per `PORT=`
  überschreiben. Nachgemessen mit einem Fremdprozess auf 8766: Abbruch, der
  Prozess überlebt.
- Der Kettentest ersetzte den Yahoo-Resolver durch einen Stub und bewies damit
  nur, dass *irgendein* zweiter Resolver läuft. Jetzt laufen beide Resolver
  echt; ersetzt sind allein `httpx.post` und `yf.Search`.
- Bezeichner durchgehend englisch, auch die strukturierten Log-Felder:
  `isin_mismatch` mit `requested`/`reported`, `openfigi_ticker_unusable`.

**Zwei Punkte für später, hier nur festgehalten:**

1. **T-18 Verify #1** erwartet, dass `CA78012H5675` über die Heimatbörse
   auflösbar wird. Das trifft nicht zu (siehe „2").
2. **Der Identitäts-Umbau** — Instrument / Listing / Provider-Alias trennen —
   gehört in T-21 ff. und wurde bewusst nicht in T-17 gezogen.
