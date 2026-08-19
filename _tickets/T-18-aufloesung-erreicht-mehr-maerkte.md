# T-18 · Auflösung erreicht mehr Märkte

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | offen | 3 h | Resolver-Kaskade und Zuständigkeit ohne ISIN | — |

**Löst:** Ein kanadisches Papier ist heute praktisch nicht aufnehmbar. Über die
ISIN scheitert die Auflösung vollständig, über das Symbol kommt es herein, bleibt
aber ohne Anbieter. Beides gemessen am 2026-08-19.

**Hängt an:** T-17 (die Gattungswahl in `_extract_ticker` ist Voraussetzung, sonst
liefert die Kaskade schneller das falsche Listing).

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `GET /quote/CA78012H5675` mit **Vorgabe** `DEFAULT_EXCHANGE=XETR` | wird aufgelöst — Heimatbörse aus dem ISIN-Präfix greift | | |
| 2 | dasselbe für `JP3633400001` (Toyota) | Tokio statt Fehlschlag | | |
| 3 | `GET /quote/IE00B4L5Y983` | unverändert Xetra/EUR — die bevorzugte Börse bleibt vorrangig | | |
| 4 | Server-Log bei #1 | protokolliert, dass auf die Heimatbörse ausgewichen wurde | | |
| 5 | `GET /quote?symbol=XIC.TO` → Detailbereich | Anbieter ist gefüllt, obwohl yfinance keine ISIN nennt | | |
| 6 | `make test` | Backend grün | | |

```bash
curl -s "http://localhost:8000/quote/CA78012H5675" | python3 -m json.tool   # #1
curl -s "http://localhost:8000/quote/JP3633400001" | python3 -m json.tool   # #2
curl -s "http://localhost:8000/quote/IE00B4L5Y983" | python3 -m json.tool   # #3
curl -s "http://localhost:8000/quote?symbol=XIC.TO" | python3 -m json.tool  # #5
```

---

## Details

### Die Auflösung hängt an einer einzigen Börse

`OpenFigiResolver` fragt ausschließlich `default_exchange`. Ein Papier ohne
Listing dort fällt durch — und Yahoos ISIN-Suche fängt es nur manchmal auf:

| ISIN | OpenFIGI (XETR) | Yahoo-Suche |
|---|---|---|
| `US0378331005` (Apple) | — | 1 Treffer |
| `IE00B4L5Y983` (EUNL) | Treffer | 1 Treffer |
| `CA78012H5675` (Royal Bank) | — | **0 Treffer** |

**Weg:** Kaskade statt einer Börse — bevorzugte Börse → **Heimatbörse aus dem
ISIN-Präfix** → beliebiges Listing. Das Präfix nennt das Emissionsland (`CA` →
`XTSE`, `JP` → `XTKS`, `FR` → `XPAR`); die Zuordnung Land → MIC kommt neu dazu,
die MIC-Tabelle gibt es schon. Keine neue Einstellung nötig — die Information
steckt in der ISIN.

Wird ausgewichen, gehört das ins Protokoll: Sonst wundert sich jemand, warum
sein Papier in CAD notiert.

### Zuständigkeit darf nicht allein an der ISIN hängen

Seit Commit `809c48a` entscheidet `is_responsible(isin)`, welche Metadaten-Quelle
greift. Für `XIC.TO` meldet yfinance keine ISIN (`'-'`), also greift der
konservative Pfad und der Anbieter bleibt leer — obwohl der Enricher die ISIN gar
nicht zum Holen braucht, nur zur Zuständigkeitsprüfung.

**Weg:** Zuständigkeit auch aus **Börse oder Währung** ableiten. `.TO` ist nicht
europäisch, das reicht für die Entscheidung. Damit fällt der konservative Pfad
für genau die Fälle weg, die ihn nicht brauchen.

### Nicht in diesem Ticket

Die Kaskade bleibt hier fest verdrahtet. Sie **konfigurierbar** zu machen ist
T-22, und sie über Plugins zu erweitern T-23.

---

## Auflösung

_(offen)_
