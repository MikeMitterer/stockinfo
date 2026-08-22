# T-18 · Auflösung erreicht mehr Märkte

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | in-review | 3 h | Resolver-Kaskade und Zuständigkeit ohne ISIN | — |

**Löst:** Ein kanadisches Papier ist heute praktisch nicht aufnehmbar. Über die
ISIN scheitert die Auflösung vollständig, über das Symbol kommt es herein, bleibt
aber ohne Anbieter. Beides gemessen am 2026-08-19.

**Hängt an:** T-17 — dort wurde der Filter gebaut, der einen OpenFIGI-Treffer
verwirft, wenn sein Ticker kein Yahoo-Symbol sein kann. Ohne ihn liefert die
Kaskade schneller ein Symbol, das es nicht gibt.

> **Zwei Korrekturen am Ticket** *(Claude, 2026-08-22, gemessen)*
>
> 1. **Verify #1 stand auf einer widerlegten Annahme.** `CA78012H5675` ist die
>    RBC-**Vorzugsaktie**; OpenFIGI liefert dazu einen Bloomberg-Bezeichner,
>    kein Yahoo-Symbol, und Yahoos ISIN-Suche kennt sie gar nicht. Die Kaskade
>    kann daran nichts ändern — Einzelheiten in T-17 unter „2". Die Zeile prüft
>    jetzt `CA7800871021`, die **Stammaktie**: an `XETR` kein Treffer, an
>    `XTSE` → `RY`. Genau der Fall, für den die Kaskade gebaut wird.
> 2. **Der kanadische ETF bleibt außen vor.** `CA46434V6817` (iShares Core
>    S&P/TSX) findet OpenFIGI **unter keiner Börse** — weder `XETR` noch
>    `XTSE` —, und Yahoos ISIN-Suche liefert ebenfalls nichts. Die Kaskade
>    erreicht ihn nicht; über das Symbol `XIC.TO` kommt er herein, und genau
>    darum geht es in Zeile #5.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `GET /quote/CA7800871021` (RBC Stammaktie) mit **Vorgabe** `DEFAULT_EXCHANGE=XETR` | wird aufgelöst — Heimatbörse aus dem ISIN-Präfix greift, Symbol `RY.TO`, Währung CAD | ✅ [^a] | |
| 2 | dasselbe für `JP3633400001` (Toyota) | Tokio statt Fehlschlag | ✅ [^b] | |
| 3 | `GET /quote/IE00B4L5Y983` | unverändert Xetra/EUR — die bevorzugte Börse bleibt vorrangig | ✅ [^c] | |
| 4 | Server-Log bei #1 | protokolliert, dass auf die Heimatbörse ausgewichen wurde | ✅ [^d] | |
| 5 | `GET /quote?symbol=XIC.TO` → Detailbereich | Anbieter ist gefüllt, obwohl yfinance keine ISIN nennt | ✅ [^e] | |
| 6 | `make test` | Backend grün | ✅ [^f] | |
| 7 | `STRICT_EXCHANGE=true` | **keine** Kaskade — diese Börse oder 404 | ✅ [^g] | |

```bash
./_tickets/T-18-smoke.sh --run    # alle Zeilen, eigener Server, temporäre DB
```

Von Hand gegen einen laufenden Stack (`make dev-up`, `DEFAULT_EXCHANGE=XETR`):

```bash
curl -s "http://localhost:8000/quote/CA7800871021" | python3 -m json.tool   # #1
curl -s "http://localhost:8000/quote/JP3633400001" | python3 -m json.tool   # #2
curl -s "http://localhost:8000/quote/IE00B4L5Y983" | python3 -m json.tool   # #3
curl -s "http://localhost:8000/quote?symbol=XIC.TO" | python3 -m json.tool  # #5
```

[^a]: `./_tickets/T-18-smoke.sh --run` → `#1a .symbol = RY.TO`,
    `#1b .currency = CAD`. Code: `HOME_EXCHANGES` und die Kaskade in
    `OpenFigiResolver.resolve_isin`. Unit-Test
    `test_kaskade_weicht_auf_die_heimatboerse_aus` (zuerst rot) prüft
    zusätzlich die **Reihenfolge** der Anfragen: erst `XETR`, dann `XTSE`.
[^b]: Smoke `#2 .symbol = 7203.T`. Vorher: OpenFIGI kennt an `XETR` kein
    Listing, Yahoos ISIN-Suche fand nichts → 404.
[^c]: Smoke `#3a .symbol = EUNL.DE`, `#3b .currency = EUR`. Der wichtigere
    Teil: Unit-Test `test_die_bevorzugte_boerse_bleibt_vorrangig` belegt, dass
    die Heimatbörse **gar nicht erst gefragt** wird, wenn die bevorzugte ein
    Listing hat — sonst kippten europäische ETFs auf ihr Domizil.
[^d]: Smoke `#4`:
    `[info] resolve_home_exchange home=XTSE isin=CA7800871021 preferred=XETR symbol=RY.TO`.
    Dazu `test_kaskade_meldet_die_abweichung`.
[^e]: Smoke `#5 .provider = BlackRock Asset Management Canada Ltd` — vorher
    leer. Code: `is_responsible` bekommt Börse und Währung, `_build` nutzt sie.
    Vier Provider-Tests und zwei Service-Tests.
[^f]: `make test` → Backend `331 passed, 29 skipped`, Plugin-API `36 passed`,
    Dashboard `230 passed`. Ruff sauber.
[^g]: Von Hand gegengeprüft mit einem eigenen Server auf Port 8768:
    `CA7800871021` → **404**, `IE00B4L5Y983` → 200 (die bevorzugte Börse
    bleibt erreichbar), **null** `resolve_home_exchange`-Zeilen im Log. Dazu
    `test_strikte_boerse_kennt_keine_kaskade`. Die Zeile stand nicht im
    Ticket — ich habe sie ergänzt, weil `strict_exchange` sonst still von der
    Kaskade ausgehebelt worden wäre.

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

**Stand 2026-08-22 — umgesetzt, bei Codex.**

| Was | Wo |
|---|---|
| Kaskade bevorzugte → Heimatbörse | `HOME_EXCHANGES` und `OpenFigiResolver.resolve_isin` |
| `strict_exchange` schaltet sie ab | `home_fallback`-Schalter, gesetzt in `container.py` |
| Zuständigkeit ohne ISIN | `is_european_listing`, neue Signatur von `is_responsible` |
| Anreicherung ohne ISIN | `QuoteService._build` und `_enrich_etf` |

**Die Länderzuordnung ist eine Heuristik, und sie steht als solche da.** Das
ISIN-Präfix nennt die ausgebende Stelle, nicht den gewünschten Handelsplatz.
`IE` und `LU` fehlen deshalb bewusst in `HOME_EXCHANGES`: Ein irischer oder
luxemburgischer Fonds wird europaweit gehandelt und hat an seinem Domizil oft
gar kein Listing. Für sie übernimmt weiterhin der Yahoo-Fallback.

**Was die Kaskade nicht erreicht.** `CA46434V6817` (iShares Core S&P/TSX)
kennt OpenFIGI unter **keiner** Börse, und Yahoos ISIN-Suche findet ihn auch
nicht. Über das Symbol `XIC.TO` kommt er herein — und bekommt jetzt einen
Anbieter, was vorher nicht der Fall war. Die Lücke bei der ISIN-Auflösung
bleibt; sie liegt bei den Datenquellen, nicht an der Kaskade.

**Zwei Änderungen am Ticket**, beide oben begründet: Verify #1 prüft die
RBC-**Stammaktie** statt der Vorzugsaktie, und Zeile #7 ist neu — ohne sie
hätte die Kaskade `strict_exchange` still ausgehebelt.

**Nebenbefund:** Der konservative Zweig „weder ISIN noch Börse noch Währung"
ist im `QuoteService` seit T-24 unerreichbar — die Core-Prüfung lässt eine
Antwort ohne Währung gar nicht bis dorthin. Er steht deshalb nicht mehr im
Service; die Quellen behandeln den Fall weiterhin konservativ, weil sie auch
von anderswo aufgerufen werden.
