# StockInfo

Eine kleine App, die **Aktien- und ETF-Kurse per REST-API** ausliefert und in einer
**SQLite-Datenbank zwischenspeichert**. Abgefragt wird per **ISIN** oder per
**Symbol+Börse**; zurück kommt **JSON** mit Kurs, Währung, Zeitpunkt, Bezeichnung und
– bei ETFs – Zusatzdaten wie TER, Anbieter und Fondsgröße.

Dazu gibt es ein optionales **Web-Dashboard** (Vue), das den Datenbank-Inhalt und die
Konfiguration anzeigt, Kurse aktualisiert und die Kurshistorie als Graph darstellt.

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
- **Historie** – zu jedem Wertpapier wird eine Kurs-Zeitreihe gespeichert und ist
  abfragbar.
- **Viele Infos** – neben Kurs und Zeitpunkt u.a. Bezeichnung, Währung, Volumen und
  bei ETFs TER, Anbieter, Replikationsart und Fondsgröße.

[↑ Übersicht](#übersicht)

---

## Wie funktioniert die Kursabfrage?

Die App kombiniert drei **kostenlose** Datenquellen:

| Quelle | Wofür |
|---|---|
| **yfinance** (Yahoo Finance) | Kurs, Währung, Volumen, Bezeichnung – Aktien & ETFs, EU & US |
| **justETF** | ETF-Zusatzdaten: TER, Anbieter, Replikation, Fondsgröße |
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
make dev            # im Vordergrund (mit Auto-Reload)
#   oder
make start          # im Hintergrund   →  make stop / make logs
```

Der Server läuft dann auf `http://localhost:8000`. Eine interaktive API-Doku
(Swagger) gibt es unter `http://localhost:8000/docs`.

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
| `GET /health` | Health-Check |
| `GET /quote/{isin}` | Kurs per ISIN (bevorzugt Xetra/EUR) |
| `GET /quote?symbol=VGWL.DE` | Kurs per vollständigem Yahoo-Symbol (Suffix = Börse) |
| `GET /quote/{isin}/history?from=&to=&limit=` | Kurshistorie eines Wertpapiers |
| `GET /instruments` | alle gecachten Wertpapiere mit letztem Kurs |
| `GET /env` | aktuelle Konfiguration (Secrets maskiert) |
| `POST /refresh` | alle Wertpapiere jetzt aktualisieren |
| `POST /refresh/{isin}` | einzelnes Wertpapier aktualisieren |
| `DELETE /instruments/{isin}` | Wertpapier + Historie löschen |

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
  "source": "yfinance+justetf",
  "cached": false,
  "stale": false,
  "fetched_at": "2026-07-12T18:16:28+00:00"
}
```

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
| `API_KEY` | optionaler Zugriffsschutz (leer = aus) | leer |

[↑ Übersicht](#übersicht)

---

## Dashboard

Ein eigenständiges Web-Frontend liegt unter [`dashboard/`](dashboard/) (Vue 3 + Vite +
TypeScript). Es zeigt die gecachten Wertpapiere und die Konfiguration, erlaubt das
Hinzufügen/Löschen und Aktualisieren von Wertpapieren und zeichnet die Kurshistorie
als Graph.

```bash
cd dashboard
cp .env.example .env       # VITE_API_BASE_URL, Standard http://localhost:8000
npm install
npm run dev                # http://localhost:5173
```

Voraussetzung: Der API-Server (siehe Schnellstart) läuft parallel.

[↑ Übersicht](#übersicht)

---

## Docker

Die API läuft auch im Container; der SQLite-Cache liegt in einem persistenten Volume:

```bash
make up          # Container bauen und starten (docker compose up -d --build)
make docker-logs # Logs verfolgen
make down        # stoppen und entfernen
```

Danach ist die API wie gewohnt unter `http://localhost:8000` erreichbar.

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
Dockerfile, docker-compose.yml
Makefile                # Start/Stopp der Dienste (make help)
```

Technische Details und Design-Entscheidungen: siehe
[`docs/superpowers/specs/`](docs/superpowers/specs/).

[↑ Übersicht](#übersicht)
