# StockInfo

Eine kleine App, die **Aktien- und ETF-Kurse per REST-API** ausliefert und in einer
**SQLite-Datenbank zwischenspeichert**. Abgefragt wird per **ISIN** oder per
**Symbol+Börse**; zurück kommt **JSON** mit Kurs, Währung, Zeitpunkt, Bezeichnung und
– bei ETFs – Zusatzdaten wie TER, Anbieter und Fondsgröße.

Dazu gibt es ein **Web-Dashboard** (Vue): Assets-Übersicht, Konfiguration, Börsen-Legende,
8 umschaltbare Themes, ein Kurs-Chart (Tagesverlauf **und** echte Tages-Schlusskurse)
sowie pro Asset Aktionen (aktualisieren, löschen, ISIN nachtragen) und Links (extraETF,
Yahoo Finance, JSON-Export).

## Übersicht

- [Was kann die App?](#was-kann-die-app)
- [Wie funktioniert die Kursabfrage?](#wie-funktioniert-die-kursabfrage)
- [Voraussetzungen](#voraussetzungen)
- [Schnellstart](#schnellstart)
- [Die REST-API](#die-rest-api)
- [Konfiguration (.env)](#konfiguration-env)
- [Dashboard](#dashboard)
- [Docker](#docker)
- [Tests](#tests)
- [Projektstruktur](#projektstruktur)

---

## Was kann die App?

- **Kurse abfragen** – europäische **und** US-Aktien/ETFs, per ISIN oder Symbol.
- **Zwischenspeichern** – jede Abfrage landet in SQLite; wiederholte Anfragen kommen
  sofort aus dem Cache statt erneut aus dem Internet.
- **Automatisch aktuell halten** – ein Hintergrundjob aktualisiert alle bekannten
  Wertpapiere in einem einstellbaren Intervall.
- **Historie** – zwei Sichten: der **Tagesverlauf** aus den erfassten Ticks und die
  echten **Tages-Schlusskurse** (EOD von Yahoo, inkrementell gecacht – pro Anfrage wird
  nur die Differenz nachgeladen).
- **Viele Infos** – neben Kurs und Zeitpunkt u.a. Bezeichnung, Währung, Volumen,
  Volatilität und bei ETFs TER, Anbieter, Replikationsart, Fondsgröße sowie
  Thesaurierend/Ausschüttend.
- **Dashboard** – Übersicht, Kurs-Chart, 8 Themes, Börsen-Legende, Profil-Links, JSON-Export.

[↑ Übersicht](#übersicht)

---

## Wie funktioniert die Kursabfrage?

Die App kombiniert drei **kostenlose** Datenquellen:

| Quelle | Wofür |
|---|---|
| **yfinance** (Yahoo Finance) | Kurs, Währung, Volumen, Bezeichnung, Tages-Schlusskurse (Basis der berechneten Volatilität) – Aktien & ETFs, EU & US |
| **justETF** | ETF-Zusatzdaten: TER, Anbieter, Replikation, Fondsgröße, 1-Jahres-Volatilität, Ausschüttungspolitik |
| **OpenFIGI** | löst eine ISIN gezielt zur gewünschten Börse auf (Standard: Xetra → EUR) |

**Wichtig zur Währung:** Das Börsen-Suffix bestimmt die Börse, nicht die Währung –
die Währung kommt immer direkt vom Kurs. Beispiel: dieselbe ISIN notiert an der Xetra
in EUR, in London teils in Pence (GBp). Die App gibt die Währung originalgetreu zurück.

[↑ Übersicht](#übersicht)

---

## Voraussetzungen

- **Python 3.11+** (die App legt automatisch eine `.venv` an)
- **make** (steuert Start/Stopp der Dienste)
- optional **Docker** (zum Betrieb im Container)
- optional **Node.js 20+** (nur für das Dashboard)

Das Projekt nutzt gemeinsame Ökosystem-Helfer unter `.libs/` (MakeLib, BashLib). Für
die Makefile muss die Umgebungsvariable `DEV_MAKE` auf die MakeLib zeigen.

[↑ Übersicht](#übersicht)

---

## Schnellstart

```bash
# 1. Konfiguration anlegen
cp .env.example .env

# 2. Abhängigkeiten installieren (einmalig)
python3.11 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt

# 3. Server starten
make dev            # nur Backend im Vordergrund (Auto-Reload)
#   oder
make start          # nur Backend im Hintergrund   →  make stop / make logs
```

Ganzer Stack (Backend **und** Dashboard) auf einmal – via
[overmind](https://github.com/DarthSim/overmind):

```bash
make dev-up         # Backend :8000 + Dashboard :5173
make dev-down       # beides stoppen   ·   make dev-logs für Logs
```

Der Server läuft dann auf `http://localhost:8000`. Eine interaktive API-Doku
(Swagger) gibt es unter `http://localhost:8000/docs` (im Browser `http://`, nicht `https://`).

Erste Abfrage:

```bash
curl http://localhost:8000/quote/IE00B3RBWM25
```

`make help` zeigt alle verfügbaren Befehle, `make hints` nützliche URLs.

[↑ Übersicht](#übersicht)

---

## Die REST-API

| Methode & Pfad | Zweck |
|---|---|
| `GET /health` | Health-Check (Status + Version) |
| `GET /quote/{isin}` | Kurs per ISIN (bevorzugt Xetra/EUR) |
| `GET /quote?symbol=VGWL.DE` | Kurs per vollständigem Yahoo-Symbol (Suffix = Börse) |
| `GET /quote/{isin}/history` | Intraday-Historie (erfasste Ticks) |
| `GET /quote/{isin}/daily?period=1w\|1m\|3m\|1y\|max` | echte Tages-Schlusskurse (EOD, gecacht) |
| `GET /instruments` | alle gecachten Wertpapiere mit letztem Kurs |
| `GET /env` | aktuelle Konfiguration (Secrets maskiert) |
| `POST /refresh` · `POST /refresh/{isin}` | alle / einzelnes Wertpapier aktualisieren |
| `PUT /instruments/by-symbol/{symbol}/isin` | ISIN nachträglich eintragen |
| `DELETE /instruments/{isin}` | Wertpapier + Historie löschen |

Für Wertpapiere **ohne ISIN** gibt es jeweils eine `…/by-symbol/{symbol}`-Variante
(Kurs, History, Daily, Refresh, Delete).

**Beispiel-Antwort** (`GET /quote/IE00B3RBWM25`):

```json
{
  "isin": "IE00B3RBWM25",
  "symbol": "VGWL.DE",
  "exchange": "Xetra",
  "name": "Vanguard FTSE All-World UCITS ETF",
  "type": "etf",
  "currency": "EUR",
  "price": 160.98,
  "quote_time": "2026-07-10T15:35:46+00:00",
  "volume": 14403,
  "ter": 0.19,
  "provider": "Vanguard",
  "replication": "Physical(Optimized sampling)",
  "fund_size": 22638.0,
  "volatility": 9.95,
  "accumulating": false,
  "source": "yfinance+justetf",
  "cached": false,
  "stale": false,
  "fetched_at": "2026-07-12T18:16:28+00:00"
}
```

`volatility` ist die 1-Jahres-Volatilität in Prozent – bei ETFs aus justETF, sonst
aus den gecachten Tages-Schlusskursen berechnet (annualisiert). `accumulating` gibt
an, ob ein ETF thesauriert (`true`) oder ausschüttet (`false`).

Nicht ermittelbare Felder sind `null` (z.B. `ter` bei Einzelaktien). Schlägt eine
Live-Abfrage fehl, aber ein alter Wert ist im Cache, wird dieser mit `"stale": true`
geliefert statt eines Fehlers. Unbekannte ISIN → `404`.

[↑ Übersicht](#übersicht)

---

## Konfiguration (.env)

Alle Werte lassen sich über `.env` überschreiben (`cp .env.example .env`):

| Variable | Bedeutung | Standard |
|---|---|---|
| `HOST` / `PORT` | Adresse des Servers | `0.0.0.0` / `8000` |
| `DATABASE_PATH` | Pfad zur SQLite-Datei | `data/stockinfo.db` |
| `CACHE_TTL_HOURS` | Alter, ab dem ein Kurs bei Anfrage neu geholt wird | `6` |
| `REFRESH_INTERVAL_HOURS` | Intervall des Hintergrund-Refresh | `6` |
| `METADATA_TTL_DAYS` | Aktualisierungs-Rhythmus für ETF-Metadaten | `7` |
| `DEFAULT_EXCHANGE` | bevorzugte Börse für ISIN-Abfragen (MIC) | `XETR` (Xetra) |
| `OPENFIGI_API_KEY` | optionaler Key für höheres OpenFIGI-Limit | leer |
| `EXTRAETF_ETF_URL` / `EXTRAETF_STOCK_URL` | Profil-Link-Vorlagen (Platzhalter `{isin}`) | extraetf.com/… |
| `YAHOO_URL` | Yahoo-Link-Vorlage (Platzhalter `{symbol}`) | de.finance.yahoo.com/… |
| `CORS_ORIGINS` | erlaubte Dashboard-Herkunft(en) | `http://localhost:5173` |

[↑ Übersicht](#übersicht)

---

## Dashboard

Ein eigenständiges Web-Frontend liegt unter [`dashboard/`](dashboard/) (Vue 3 + Vite +
TypeScript + SCSS) mit fixem Header (deep-linkbare Tab-Navigation) und Statuszeile
(**Health-Ampel** grün/orange/rot + Version):

- **Assets** – Übersicht mit letztem Kurs; hinzufügen (ISIN/Symbol), aktualisieren,
  löschen, **ISIN nachtragen**; pro Zeile Links zu **extraETF**, **Yahoo Finance** und
  ein **JSON-Popup** (URL + Ergebnis kopierbar).
- **Chart** – Zeitraum-Umschalter `1T · 1W · 1M · 3M · 1J · Max`: `1T` = Tagesverlauf
  (erfasste Ticks), Rest = echte Tages-Schlusskurse (EOD). Echte Zeitachse, kompakte Ticks.
- **Börsen** – Legende der Yahoo-Suffixe (Börse, Region, Währung).
- **Environment** – aktuelle Konfiguration; **Themes** – 8 wählbare, persistente Themes.

```bash
cd dashboard
npm install
npm run dev                # http://localhost:5173
```

Der Vite-Dev-Proxy leitet API-Requests automatisch an das Backend
(`http://localhost:8000`) weiter — `VITE_API_BASE_URL` ist im Dev-Betrieb nicht
nötig (optional überschreibbar, siehe `dashboard/vite.config.ts`).

Backend muss parallel laufen. Beides zusammen: **`make dev-up`** (siehe Schnellstart).

[↑ Übersicht](#übersicht)

---

## Docker (ein Container)

Backend **und** Dashboard laufen in einem Image auf einem Port. Gebaut wird mit
`docker/build.sh` (Ökosystem-Konvention, versioniert via `gitDockerTag`):

```bash
make build     # Image bauen (docker/build.sh --build)
make up        # Container starten → http://localhost:8000/
make down      # stoppen & entfernen
make docker-logs   # Logs folgen
```

Das Dashboard wird von FastAPI mit ausgeliefert (relative API-Aufrufe), es
ist kein separater Webserver nötig. Der Cache liegt im Volume `stockinfo-data`
(im Container unter `/data`).

**Push in eine Registry:**

```bash
make push                     # docker/build.sh --push   (TARGET=dockerhub, Default)
TARGET=ghcr make push         # alternativ GitHub Container Registry
```

**Unraid:** Es liegt ein fertiges Container-Template unter
[`unraid/stockinfo.xml`](unraid/stockinfo.xml) bereit — Image
`mangolila/stockinfo` (Docker Hub), WebUI-Port `8000`, Pfad
`/mnt/user/appdata/stockinfo → /data`, plus die wichtigsten Einstellungen als
Variablen (Refresh-Intervall, TTLs, Börse, OpenFIGI-Key). Die XML in
`/boot/config/plugins/dockerMan/templates-user/` ablegen (oder ihren Inhalt beim
„Add Container" einfügen).

[↑ Übersicht](#übersicht)

---

## Tests

```bash
make test                       # Backend (pytest)
cd dashboard && npm run test    # Dashboard (Vitest)
```

Die Tests laufen ohne Netzwerk – externe Datenquellen sind gemockt.

[↑ Übersicht](#übersicht)

---

## Projektstruktur

```
app/                    # FastAPI-Backend
  main.py               #   App-Setup, Routen, Scheduler-Start
  config.py             #   Konfiguration (.env)
  db.py, repository.py  #   SQLite: Schema und Datenzugriff
  resolver.py           #   ISIN → Symbol/Börse (OpenFIGI + Yahoo)
  providers/            #   Datenquellen: yfinance, justETF, OpenFIGI
  services/             #   Kursbeschaffung + Cache/TTL-Logik
  scheduler.py          #   periodischer Hintergrund-Refresh
  routers/              #   HTTP-Endpoints (quotes, dashboard)
dashboard/              # Vue-Dashboard (eigenständige App)
tests/                  # Backend-Tests (pytest)
docker/                 # Dockerfile, build.sh (Ein-Image-Build)
Makefile                # Start/Stopp der Dienste (make help)
```

Technische Details und Design-Entscheidungen: siehe
[`docs/superpowers/specs/`](docs/superpowers/specs/).

[↑ Übersicht](#übersicht)
