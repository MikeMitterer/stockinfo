# T-54 · Ein neues deutsches Papier lässt sich nicht aufnehmen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | offen | 3–5 h | die Aufnahme deutscher Listings reparieren und den Fehlerweg richtig benennen | — |

- **Angelegt:** 2026-09-01, aus dem T-50-Browserlauf (dort B-3)
- **Hängt ab von:** nichts
- **Reihenfolge:** 3/5 der freigegebenen Kette T-55 → T-52 → T-54 → T-53 →
  T-51 — der gewichtigste Drain, aber erst nach Testisolation und dauerhaften
  Profilvorlagen

**Löst:** Wer `SAP.DE` in das Feld über der Assets-Liste tippt, bekommt eine
Fehlermeldung, die ihn zur Quelle schickt. Die Quelle ist in Ordnung.

---

## Der gemessene Befund

```
GET /quote?symbol=SAP.DE   →  502
{"code":"quote_unavailable",
 "params":{"identifier":"SAP.DE",
           "detail":"SAP.DE: Pflichtfelder fehlen — name, type"}}
```

Dasselbe für `BMW.DE`. **`MSFT` geht** und liefert `name`, `type`, `currency`
vollständig.

### Warum das kein Quellenausfall ist

**Die Quelle antwortet vollständig.** Direkt gefragt:

```
SAP.DE    keys=173  longName='SAP SE'   quoteType='EQUITY'
EUNL.DE   keys= 80  longName='iShares…' quoteType='ETF'
```

**Die Kette trägt.** `GET /analyze?symbol=BMW.DE` meldet für dieselbe
Konfiguration:

```
resolvers  yahoo-search  ok
quotes     yfinance      ok
daily      yfinance      ok       257 Zeilen
etf_meta   justetf       empty
```

Auflösung, Kurs und Tagesreihe sind da. Erst beim Zusammenbauen der Antwort
fehlen `name` und `type` — `app/services/quote_service.py:297` bzw. `:331`.

### Wen es trifft

- Reproduziert unter der T-37-Kette **und unter den Vorgaben ohne
  `sources.yaml`** — also in der Standardkonfiguration.
- **Nur die Neuaufnahme.** Bereits aufgenommene `.DE`-Papiere werden weiter
  bedient; ein Bestand mit `APC.DE`, `EUNL.DE`, `VGWL.DE` läuft unverändert.
- Der Unterschied zwischen `MSFT` und `BMW.DE` in der Analyse ist eine einzige
  Zeile: Bei `BMW.DE` wird `justetf` gefragt und `yfinance` übersprungen, bei
  `MSFT` umgekehrt. Ob das die Ursache ist oder eine Begleiterscheinung, ist
  **nicht** ermittelt — der Browserlauf hat an dieser Stelle bewusst
  aufgehört.

## Zwei Fragen, und die zweite ist die wichtigere

**1. Warum fehlen `name` und `type`?** Das ist der eigentliche Defekt.

**2. Warum heißt der Fehler `quote_unavailable` und trägt `502`?** Die Quelle
hat geantwortet; verworfen hat die Antwort der **Feldvertrag**. Der Betreiber
liest in der Oberfläche

> *„Keine Quelle konnte nachsehen: SAP.DE. Ob es das Papier gibt, ist damit
> offen."*

und sucht den Fehler bei seiner Quelle oder seinem Netz. Das ist derselbe
Verwechslungstyp, den **T-44 Befund 1** für `/fx` behoben hat — `502` für
etwas, das kein Gegenstellen-Ausfall ist — eine Ebene weiter. Auch wenn Frage 1
gelöst ist, bleibt Frage 2 offen: Eine unvollständige Antwort ist weder
„nicht gefunden" noch „Quelle weg", und dafür gibt es bis jetzt keine Kennung.

**Nebenbefund:** `params.detail` trägt deutschen Fließtext
(`"Pflichtfelder fehlen — name, type"`). Die Oberfläche zeigt ihn derzeit
nicht — sie baut ihren Satz aus der Kennung —, aber ein anderer Client täte es.
Verwandt mit [T-53](T-53-analyse-detail-traegt-deutschen-text.md).

## Verify

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | Ursache | belegt, **warum** `name`/`type` fehlen — nicht vermutet | ➖ | |
| **2** | Aufnahme | `SAP.DE` und `BMW.DE` lassen sich über das Feld aufnehmen, mit Name und Gattung | ➖ | |
| **3** | Kein Rückschritt | `MSFT`, `EUNL.DE`, `BTC-EUR` und ein `isin_only`-Papier gehen weiter | ➖ | |
| **4** | Fehlerweg | eine unvollständige Antwort ist von „nicht gefunden" und „Quelle weg" unterscheidbar — Kennung und Statuscode | ➖ | |
| **5** | Mutant | die Pflichtfeldprüfung ausgehängt rötet einen Test | ➖ | |
| **6** | Regression | `make test` und Ruff grün | ➖ | |

---

## Die Ursache, gemessen (Claude, 2026-09-02)

`app/services/quote_service.py:485` — `get_quote_by_symbol`:

```python
ticker, mic = split_symbol(symbol)
if ticker and mic:
    resolved = ResolvedInstrument(symbol=symbol, ticker=ticker, mic=mic)
    return self._build(resolved, enrich_etf)
```

**Ein Symbol mit Börsensuffix fragt gar keine Quelle.** Die Identität entsteht
aus dem Symbol selbst — und mit ihr ein `ResolvedInstrument` **ohne Namen und
ohne Gattung**. `_build` holt beide aus `raw.name or resolved.name` bzw.
`raw.type or resolved.type`; die Kursquelle liefert sie nicht, die Auflösung
wurde nie gefragt. Also greift die Pflichtfeldprüfung aus T-38.

| Symbol | `split_symbol` | Weg | Ergebnis |
|---|---|---|---|
| `SAP.DE` | `('SAP', 'XETR')` | Abkürzung, keine Quelle | **502** |
| `BMW.DE` | `('BMW', 'XETR')` | Abkürzung, keine Quelle | **502** |
| `GOLD.SG` | `('GOLD', 'XSTU')` | Abkürzung, keine Quelle | **502** |
| `MSFT` | `(None, None)` | Resolver gefragt | 200 |
| `BTC-EUR` | `(None, None)` | Resolver gefragt | 200 |

Gegengeprobt an den Bausteinen: Der Resolver **liefert** für `SAP.DE`
`name='SAP SE…'`, `instrument_type='stock'`; die Kursquelle liefert für
**beide** Symbole `name=None`, `type=None`. Im Protokoll steht folgerichtig
nur `core_incomplete missing=['name','type']` und **keine** Resolver-Warnung —
die Quelle hat nicht versagt, sie wurde nicht gefragt.

**Damit ist auch Frage 2 des Tickets beantwortet:** `502 quote_unavailable`
war doppelt falsch. Es meldet einen Ausfall der Gegenstelle, obwohl gar keine
Gegenstelle beteiligt war.

**Betroffen ist nur die Neuaufnahme.** Ein Papier im Bestand läuft über
`_fetch_live` und ist unberührt — deshalb funktionieren `APC.DE`, `EUNL.DE`
und `GOLD.SG` weiter, obwohl sie heute nicht mehr aufnehmbar wären.

---

## Scope-Vertrag (Claude, 2026-09-02, vor dem ersten Produktedit)

### Die fachliche Änderung

Die Abkürzung bleibt in ihrem Zweck — **die vom Benutzer genannte Börse
gewinnt** —, aber sie beschafft Name und Gattung, statt sie leer zu lassen.
Der Weg dafür existiert bereits: `resolve_symbol`, denselben, den der
suffixlose Zweig zwei Zeilen später geht.

Die Identität bleibt die aus dem Symbol: Wer `GOLD.SG` tippt, meint Stuttgart,
auch wenn eine Quelle die Vorzugsbörse nennt. Genau dafür steht die Abkürzung
da, und das ändert sich nicht.

### Erwartete Flächen

| Datei | Was |
|---|---|
| `app/services/quote_service.py` | der Suffix-Zweig holt Name und Gattung |
| `tests/…` | neue Fälle, siehe Orakel |

**Ein Produktcode-Modul.** Kein Vertrag, kein Schema, kein Statuscode.

### Budget

| | Grenze |
|---|---:|
| Produktcode | ≤ 40 |
| Tests | ≤ 90 |

Gezählt als hinzugefügte Zeilen aus `git diff --numstat` gegen den
Abzweigpunkt, ohne Ticket- und `STATUS.md`-Dateien.

### Pflichtorakel

1. **Ein Papier mit Suffix lässt sich aufnehmen**, mit Name und Gattung —
   `SAP.DE` und `BMW.DE`.
2. **Die genannte Börse gewinnt weiterhin.** Ein Fall, in dem die Quelle eine
   andere Börse nennt als der Benutzer, muss die des Benutzers behalten. Ohne
   diesen Fall wäre die Abkürzung ersatzlos zu streichen, und der Test bewiese
   nur, dass irgendetwas antwortet.
3. **Kein Rückschritt** für `MSFT`, den ISIN-Weg, `BTC-EUR` und ein
   `isin_only`-Papier.
4. **Mutanten:** die Beschaffung wieder entfernt → Fall 1 rot; die
   Börsen-Übernahme entfernt → Fall 2 rot.

### Nicht-Ziele

- Eine neue Kennung für „Antwort unvollständig". Nach dieser Korrektur
  entsteht der Fall auf diesem Weg nicht mehr; für **wirklich** unvollständige
  Quellen bleibt die Frage offen und gehört in ein eigenes Ticket.
- Den deutschen Fließtext in `params.detail` — das ist [T-53].
- `split_symbol`, die Vorzugsbörse oder den Cache-Weg anfassen.
