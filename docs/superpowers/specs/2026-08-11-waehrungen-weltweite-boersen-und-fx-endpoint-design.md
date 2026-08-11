# StockInfo — Währungen: weltweite Default-Börsen + FX-Endpoint

**Datum:** 2026-08-11
**Status:** Design freigegeben

## Ziel

StockInfo für Konsumenten außerhalb des Euroraums brauchbar machen, ohne das
Datenmodell zu verkomplizieren. Zwei unabhängige Stufen (aus der Konsumenten-Anfrage
`docs/stockinfo-currency-request.md`, Rebalancing-App *StockPortfolio*):

- **Stufe 1 — weltweite, konfigurierbare Default-Börse.** Jede StockInfo-Instanz wird
  auf ihre Region konfiguriert (Xetra/EUR, TSX/CAD, NYSE/USD, Tokio/JPY …). Die
  Notierungswährung ergibt sich automatisch aus dem Live-Quote der jeweiligen Börse.
- **Stufe 2 — FX-Endpoint.** `GET /fx?base=EUR&quote=USD` liefert Wechselkurse mit
  demselben Frische-Vertrag wie Kurse (Zeitstempel, Quelle, `stale`), damit die
  Konsumenten-App gemischte Depots umrechnen kann.

**Kernentscheidungen (mit dem Auftraggeber festgelegt):**
- **Eine ISIN = eine Zeile** (pro Instanz). Keine koexistierenden Mehrfach-Notierungen,
  kein Schema-Rekey der Instrument-Identität. Die Notierung ist eine Instanz-Eigenschaft,
  kein Request-Parameter.
- **Weltweit von Anfang an** — keine handverlesene Kleinstauswahl, US inklusive.
- **Stufe 3 (serverseitige Umrechnung) wird nicht gebaut** (versteckt Markt- und
  Devisenkurs-Alter in einem Feld; der Konsument rechnet mit Stufe 2 transparenter).

## Motivation

Heute bevorzugt der Resolver (`app/resolver.py`) eine einzelne europäische Börse
(`default_exchange = "XETR"`) aus einer kleinen `EXCHANGES`-Tabelle (10 europäische
MICs). Die Währung wird nie aus dem Börsensuffix abgeleitet, sondern stammt immer aus
dem Live-Quote (`app/providers/yfinance_provider.py`, `fast_info.currency`). Für einen
Nicht-Euro-Nutzer liefert StockInfo damit die falsche oder keine Notierung.

Weil die App **selbst-gehostet** ist (Unraid, ein Nutzer = eine Instanz), ist die
natürliche Lösung eine instanz-weite Konfiguration der Börse — nicht ein per-Request-
Multiplexing, das mehrere Notierungen pro ISIN und damit einen teuren Schema-Umbau
erzwingen würde. Devisenkurse fehlen heute ganz; yfinance liefert sie gratis über
Yahoo-FX-Ticker (`EURUSD=X` → `fast_info.last_price`, verifiziert ~0,2–0,6 s), sodass
Stufe 2 die bestehende `fast_info`- und TTL-Cache-Maschinerie wiederverwendet.

---

## Stufe 1 — weltweite, konfigurierbare Default-Börse

### Weltweite Börsentabelle

`EXCHANGES` in `app/resolver.py` wird von 10 europäischen MICs zu einer umfassenden
Welt-Tabelle `MIC → (Yahoo-Suffix, Anzeigename)` erweitert. Repräsentative Startabdeckung
(die großen Weltmärkte; per Zeile trivial erweiterbar):

- **Amerika:** US (NYSE/Nasdaq → **leeres Suffix**), Kanada `XTSE`→`.TO`, `XTSX`→`.V`,
  Brasilien `BVMF`→`.SA`, Mexiko `XMEX`→`.MX`.
- **Europa:** bestehende (XETR/.DE, XFRA/.F, XLON/.L, XMIL/.MI, XPAR/.PA, XAMS/.AS,
  XSWX/.SW, XMAD/.MC, XWBO/.VI, XBRU/.BR) + Stockholm `XSTO`→`.ST`, Oslo `XOSL`→`.OL`,
  Kopenhagen `XCSE`→`.CO`, Helsinki `XHEL`→`.HE`, Lissabon `XLIS`→`.LS`, Warschau
  `XWAR`→`.WA`.
- **Asien-Pazifik:** Tokio `XTKS`→`.T`, Hongkong `XHKG`→`.HK`, Shanghai `XSHG`→`.SS`,
  Shenzhen `XSHE`→`.SZ`, ASX `XASX`→`.AX`, Singapur `XSES`→`.SI`, Indien NSE `XNSE`→`.NS`
  / BSE `XBOM`→`.BO`, Korea `XKRX`→`.KS`, Taiwan `XTAI`→`.TW`.
- **Afrika/Nahost:** JSE `XJSE`→`.JO`, Tel Aviv `XTAE`→`.TA`.

Die Währung bleibt **emergent** aus dem Live-Quote — kein Währungs-Mapping nötig.

### US-Sonderpfad

US ist die einzige Region mit Extra-Logik, aus zwei Gründen (verifiziert per OpenFIGI):
1. **Kein Yahoo-Suffix** — US-Symbole sind suffixlos (`AAPL`, nicht `AAPL.US`). Der
   Tabelleneintrag trägt einen leeren Suffix-String; die Symbolbildung
   `f"{ticker}{suffix}"` ergibt damit korrekt das nackte Ticker.
2. **OpenFIGI-Composite** — die `micCode`-Auflösung ist für US inkonsistent (Apple löst
   an `XNYS`, nicht an `XNAS` auf). US wird daher über OpenFIGIs **Composite** aufgelöst:
   der OpenFIGI-Request nutzt für US `exchCode: "US"` statt eines einzelnen `micCode`.

Dazu wird `OpenFigiClient.map_isin` (`app/providers/openfigi_provider.py`) erweitert, das
Auflösungs-Merkmal (micCode **oder** exchCode) je Börseneintrag zu wählen. Der genaue
OpenFIGI-Feldname für die US-Composite-Auflösung wird zu Implementierungsbeginn an
mehreren US-Titeln (NYSE **und** Nasdaq, z.B. Apple/Microsoft) verifiziert.

### `strict_exchange`-Schalter

Neuer Config-Wert `strict_exchange: bool = False` (`app/config.py`). Die Verdrahtung sitzt
im Composition-Root (`app/container.py`):

- **`false` (Default, heutiges Verhalten):** Resolver bleibt
  `CompositeResolver(OpenFigiResolver(default_exchange), YFinanceResolver())` — findet
  OpenFIGI an der konfigurierten Börse nichts, greift der Yahoo-Search-Fallback (liefert
  irgendeine Notierung, ehrlich via `currency`/`exchange`/`source` beschriftet).
- **`true` (strikt):** Resolver ist nur `OpenFigiResolver(default_exchange)` **ohne**
  Fallback. Gibt es an der konfigurierten Börse keine Notierung → `resolve_isin` liefert
  `None` → `InstrumentNotFoundError` → die bestehende Router-Abbildung ergibt **404**.
  Erfüllt den Konsumenten-Wunsch „lieber klares 'gibt es nicht' als stille Ersatzwährung".

Default `false` ⇒ voll rückwärtskompatibel.

### Sichtbarkeit

`strict_exchange` (und das schon vorhandene `default_exchange`) werden über `/env`
(`app/routers/dashboard.py`, `EnvInfo` in `app/models.py`) und das `EnvironmentPanel`
(`dashboard/src/components/EnvironmentPanel.vue`, i18n de/en) angezeigt — analog zu
`metadata_ttl_days`.

### Fehlerbehandlung Stufe 1

- Unbekannter/nicht konfigurierbarer `default_exchange` → Fallback auf `XETR` wie heute,
  plus eine `logger.warning` (statt stiller Fehlkonfiguration).
- Strikt + keine Notierung an der Börse → 404 (siehe oben).
- Nicht-strikt + keine Notierung → Yahoo-Fallback, ehrlich beschriftet.

---

## Stufe 2 — FX-Endpoint

### Modell

Neues Pydantic-Modell `FxRate` (`app/models.py`) mit exakt dem Kurs-Metadaten-Vertrag:

```
FxRate:
  base:       str          # z.B. "EUR"
  quote:      str          # z.B. "USD"
  rate:       float        # 1 base = rate quote
  quote_time: str          # ISO-Zeitpunkt des Kurses
  source:     str          # "yfinance"
  cached:     bool
  stale:      bool
  fetched_at: str          # ISO-Zeitpunkt des Abrufs
```

### Provider

`YFinanceProvider.fetch_fx_rate(base: str, quote: str) -> RawFx | None`
(`app/providers/yfinance_provider.py`): bildet das Yahoo-FX-Symbol `f"{base}{quote}=X"`,
liest `fast_info.last_price`; `quote_time` = jetzt (UTC), da FX-Ticker keinen verlässlichen
Marktzeitpunkt liefern (dieselbe Pragmatik wie beim Kurs-Fallback). `None` bei Fehler.

### Cache

Neue Tabelle `fx_rates` (`app/db.py`):

```
CREATE TABLE fx_rates (
    base       TEXT NOT NULL,
    quote      TEXT NOT NULL,
    rate       REAL NOT NULL,
    quote_time TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (base, quote)
);
```

`CachedFxService` (`app/services/fx_service.py`) legt einen TTL-Cache mit **`fx_ttl_hours`
(Default 1)** vor die Live-Beschaffung — dieselbe Lazy-TTL- und „serve-stale-on-error"-
Logik wie `CachedQuoteService`: frischer Cache → nutzen; sonst frisch holen und speichern;
schlägt das Holen fehl, aber ein alter Wert liegt vor → diesen als `stale` liefern.
Repository-Methoden `get_fx_rate(base, quote)` / `save_fx_rate(...)` in
`app/repository.py`.

### Endpoint

Neuer, kleiner Router `app/routers/fx.py`, eingebunden in `app/main.py`:

```
GET /fx?base=EUR&quote=USD   → FxRate
```

- Validierung: `base`/`quote` je genau 3 Buchstaben, uppercase-normalisiert; sonst 422.
- `base == quote` → Kurzschluss auf `rate = 1.0` (kein Fetch), `source = "identity"`.
- Kein Kurs beschaffbar und kein Cache → 502 (analog zu den Quote-Routen).

### Config & Sichtbarkeit

- `fx_ttl_hours: int = 1` (`app/config.py`), über `/env` + `EnvironmentPanel` sichtbar.
- Kein Dashboard-Umrechner-UI — der Konsument ist die API, nicht der StockInfo-Nutzer.

### Fehlerbehandlung Stufe 2

- Unbekanntes Währungspaar (Yahoo liefert nichts) und kein Cache → 502 mit klarer Meldung.
- Alter Kurs bei Fetch-Fehler → `stale = true` mit Zeitstempel (nie stiller alter Wert).

---

## Rückwärtskompatibilität

- Stufe 1: rein additive Konfiguration; Defaults (`default_exchange = "XETR"`,
  `strict_exchange = false`) reproduzieren das heutige Verhalten. Keine Änderung an
  Response-Schemata.
- Stufe 2: neuer Endpoint + neue Tabelle (additive Migration). Bestehende Endpunkte
  unberührt.
- Die vom Konsumenten gelesenen Felder (`currency`, `price`, `quote_time`, `stale`,
  `fetched_at`) bleiben unverändert.

## Nicht im Scope (YAGNI)

- **Stufe 3** — serverseitige Umrechnung (`?in=EUR`): verworfen.
- Koexistierende Mehrfach-Notierungen pro ISIN / per-Request `?exchange=`/`?currency=`:
  widerspricht „eine ISIN, eine Zeile".
- Modellierung von Währungs**risiko** (Durchschau auf Fondswährungen) — ausdrücklich nicht.
- Historische Devisenkurse — die App rechnet nur mit dem Jetzt.
- Dashboard-Währungsumrechner-UI.

## Testing

**Stufe 1**
- Resolver-Komposition: `strict_exchange=true` → kein Yahoo-Fallback (leeres OpenFIGI-
  Ergebnis ⇒ `None` ⇒ 404 im Endpoint); `false` → Fallback greift.
- Weltweite Tabelle: repräsentative Einträge bilden korrekte Symbole (TSX `RY`→`RY.TO`;
  US-Ticker → **leeres** Suffix ⇒ `AAPL`).
- US-Sonderpfad: OpenFIGI-Composite-Auflösung liefert für NYSE- und Nasdaq-Titel ein
  Ticker (mit Fake/aufgezeichneter Antwort im Unit-Test; Live-Verifikation zu Beginn).
- Unbekannter `default_exchange` → Fallback + Warnung.

**Stufe 2**
- `CachedFxService`: Cache-Miss holt live und speichert; Cache-Hit ohne Fetch; Fetch-
  Fehler mit vorhandenem Wert → `stale`; ohne Wert → Fehler.
- Endpoint: 200 mit `FxRate`; 422 bei fehlenden/ungültigen Codes; `base==quote` → `1.0`
  ohne Fetch; 502 wenn nichts beschaffbar.
- Provider `fetch_fx_rate` mit gefaktem Ticker (kein Netz im Test).

## Betroffene Dateien (Überblick)

**Backend:** `app/config.py` (strict_exchange, fx_ttl_hours), `app/resolver.py` (Welt-
Tabelle, US-Sonderpfad-Auswahl), `app/providers/openfigi_provider.py` (mic-/exchCode-
Auswahl), `app/providers/yfinance_provider.py` (fetch_fx_rate + RawFx), `app/models.py`
(FxRate, EnvInfo-Erweiterung), `app/services/fx_service.py` (neu), `app/repository.py`
(fx_rates-Methoden), `app/db.py` (fx_rates-Tabelle + Migration), `app/routers/fx.py`
(neu), `app/routers/dashboard.py` (/env-Erweiterung), `app/main.py` (fx-Router),
`app/container.py` (strict-Komposition, get_fx_service).

**Frontend:** `dashboard/src/components/EnvironmentPanel.vue`, `dashboard/src/types.ts`
(EnvInfo-Felder), `dashboard/src/i18n/de.ts` + `en.ts` (strict_exchange, fx_ttl_hours).
