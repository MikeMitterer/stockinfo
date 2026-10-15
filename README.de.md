<div align="center">

<img src="dashboard/public/stockinfo-icon.png" alt="StockInfo-Icon" width="96" height="96">

# StockInfo

**Aktien- und ETF-Kurse per REST-API, zwischengespeichert in SQLite**

[English](README.md) · Deutsch

</div>

Eine kleine App, die **Aktien- und ETF-Kurse über eine REST-API** liefert und
sie in einer **SQLite-Datenbank** zwischenspeichert. Abgefragt wird per
**ISIN** oder per **Symbol und Börse**; die Antwort ist **JSON** mit Preis,
Währung, Zeitpunkt, Name und – bei ETFs – Zusatzangaben wie TER, Anbieter und
Fondsgröße.

Docker-Image: [mangolila/stockinfo auf Docker Hub](https://hub.docker.com/repository/docker/mangolila/stockinfo/general).
Änderungen je Release-Tag: [Changelog](CHANGELOG.md). Ältere, kuratierte
Zusammenfassungen: [Release Notes](docs/release-notes.md).

Das **Web-Dashboard** bietet eine Übersicht der Assets, Kursdiagramme,
manuelle ETF-Kennzahlen und die Quellenkonfiguration, mit deutscher und
englischer Oberfläche.

![StockInfo-Dashboard](unraid/screenshots/dashboard.png)

### StockPortfolio: die Schwester-App

StockInfo läuft für sich allein. Skripte, Tabellenkalkulationen und andere
Apps können die Kurse über die REST-API nutzen; sonst muss nichts installiert
werden.

[StockPortfolio](https://github.com/MikeMitterer/stockportfolio) ist eine
optionale Ergänzung, um das eigene Depot zu verwalten. Es entstand als
Begleiter zu StockInfo: Es bewertet deine Positionen, zeigt, wie weit sie von
ihrer Zielaufteilung entfernt sind, und berechnet Umschichtungen
(Rebalancing). Kurse, Wechselkurse und Fondskennzahlen kommen von StockInfo.

|  | StockInfo | StockPortfolio |
|---|---|---|
| Zweck | Kurse, Kursverlauf, ETF-Kennzahlen | Depots, Bewertung, Rebalancing |
| Läuft ohne die andere App | Ja | Nein, braucht StockInfo für die Kurse |
| Docker-Image | [`mangolila/stockinfo`](https://hub.docker.com/r/mangolila/stockinfo) | [`mangolila/stockportfolio`](https://hub.docker.com/r/mangolila/stockportfolio) |

Für beide zuerst StockInfo einrichten, dann StockPortfolio. Wie du
StockPortfolio auf deine StockInfo-Adresse zeigen lässt, erklärt dessen
[Einrichtungsanleitung](https://github.com/MikeMitterer/stockportfolio#setup).

### Release-Highlight: 1.5.0

- **Volatilität für jede Instrumentart.** Aktien und Fonds zeigen jetzt die
  Ein-Jahres-Volatilität aus den Tagesschlusskursen, mit Quelle und Datum im
  Detailbereich. ETFs behalten den Wert von justETF, wenn es einen gibt.
- **Fondsgröße immer in Millionen.** Werte von justETF sind in EUR; von Hand
  eingetragene Werte behalten die eingegebene Währung.
- **Neue Speicherschicht auf SQLModel.** Bestehende Datenbanken werden
  unverändert gelesen; ein Vergleich mit der Kopie einer echten Datenbank fand
  keine Unterschiede.
- `GET /fx` meldet in `quote_time` den Zeitpunkt der Quelle, wenn sie einen
  nennt, etwa `as_of` in einer YAML-Datei. Yahoo nennt keinen; dort bleibt
  `quote_time` der Abrufzeitpunkt.
- Eine vertippte ISIN wie `DE000110253X` wird mit `400` und
  `code: invalid_isin_format` abgelehnt, statt als Symbol gesucht zu werden.

## Inhalt

- [Was kann die App?](#was-kann-die-app)
- [Wie Kurse abgerufen werden](#wie-kurse-abgerufen-werden)
- [Voraussetzungen](#voraussetzungen)
- [Schnellstart](#schnellstart)
- [Sicherheitsmodell](#sicherheitsmodell)
- [Die REST-API](#die-rest-api)
- [Konfiguration (.env)](#konfiguration-env)
- [Dashboard](#dashboard)
- [Docker](#docker)
- [Unraid](#unraid)
- [Tests](#tests)
- [Releases und Changelog](#releases-und-changelog)
- [Projektstruktur](#projektstruktur)
- [Support](#support)
- [Lizenz](#lizenz)

---

## Was kann die App?

- **Kurse abrufen** – europäische **und** US-Aktien und -ETFs, per ISIN oder
  Symbol.
- **Zwischenspeichern** – jede Antwort landet in SQLite; wiederholte Anfragen
  kommen aus dem Cache, statt erneut ins Internet zu gehen.
- **Automatisch aktuell bleiben** – ein Hintergrundjob aktualisiert alle
  bekannten Instrumente in einem einstellbaren Abstand.
- **Kursverlauf** – zwei Ansichten: die **Intraday-Kurve** aus gesammelten
  Ticks und echte **Tagesschlusskurse** (EOD von Yahoo, schrittweise
  zwischengespeichert – jede Anfrage holt nur das fehlende Stück).
- **Umfangreiche Daten** – neben Preis und Zeitpunkt: Name, Währung, Volumen,
  Volatilität und bei ETFs TER, Anbieter, Replikationsmethode, Fondsgröße,
  Fondsdomizil, Fondswährung sowie thesaurierend oder ausschüttend.
- **Lücken selbst füllen** – was die Quellen nicht liefern, trägst du im
  aufklappbaren Detailbereich einer Zeile von Hand ein. Die Quelle hat immer
  Vorrang: Ein eigener Wert füllt eine Lücke, er überschreibt nie. Er bleibt
  gespeichert, solange die Quelle den Wert liefert, und gilt wieder, sobald die
  Quelle verstummt. Das ist der vorgesehene Weg für TER und Fondsgröße von
  ETFs außerhalb Europas, die keine freie Quelle verlässlich angibt.

  ![Detailbereich](unraid/screenshots/detail-area.png)

- **Dashboard** – Übersicht mit sortierbaren Spalten, angedocktem
  Kursdiagramm, 8 Themes, deutscher und englischer Oberfläche, Börsenlegende,
  Profil-Links und JSON-Export.

[↑ Inhalt](#inhalt)

---

## Wie Kurse abgerufen werden

Die vorgegebenen Online-Ketten verwenden diese **kostenlosen** Datenquellen:

| Quelle | Wofür |
|---|---|
| **yfinance** (Yahoo Finance) | Preis, Währung, Volumen, Name, Tagesschlusskurse (Grundlage der berechneten Volatilität) – Aktien und ETFs, EU und US. Außerdem der Fondsanbieter für **ETFs außerhalb Europas**, die justETF nicht führt |
| **justETF** | ETF-Zusatzangaben für **europäische** (UCITS-)Fonds: TER, Anbieter, Replikation, Fondsgröße (in Millionen EUR), Ein-Jahres-Volatilität, Ertragsverwendung |
| **OpenFIGI** | löst eine ISIN zum Listing an deiner bevorzugten Börse auf (Vorgabe: Xetra → EUR) |
| **Yahoo-Suche** | Rückfallweg zum Auflösen, wenn OpenFIGI ein Instrument nicht findet |

Die Quellenketten stellst du in `sources.yaml` neben der Datenbank ein. Das
mitgelieferte Plugin `yaml-file` kann von Hand gepflegte Daten als Rückfall
oder als reines Dateiprofil liefern. Siehe
[Quellenkonfiguration](docs/plugins.md) und die
[Anleitung für Plugin-Autoren](docs/plugin-authors.md).

**Keine offiziellen APIs.** Die Standardquellen justETF und Yahoo Finance
bieten für diese Daten keine öffentliche API an. StockInfo liest ihre
öffentlichen Webseiten über die Open-Source-Bibliotheken `justetf-scraping` und
`yfinance`. Die Nutzungsbedingungen von justETF verbieten zum Beispiel
automatisierte Kursabfragen und übermäßige Last. StockInfo holt von justETF
keine Kurse, nur Fondsdaten: einmal je ETF alle `METADATA_TTL_DAYS` (Vorgabe
7) und zusätzlich, wenn du ein einzelnes Instrument von Hand aktualisierst.
Wer StockInfo betreibt, ist dafür verantwortlich, diese Quellen im Rahmen der
Bedingungen der Anbieter zu nutzen. Wer sie vermeiden will, nimmt sie aus
`sources.yaml` heraus oder verwendet das reine Dateiprofil.

**ETFs außerhalb Europas.** justETF ist eine Datenbank europäischer
UCITS-Fonds; ein US- oder kanadischer ETF findet dort nichts. Für diese
liefert Yahoo den Fondsanbieter – und bewusst nichts weiter: Yahoo meldet die
Kostenquote in zwei Feldern mit zwei verschiedenen Einheiten (`0.03` und
`0.0003` für denselben Fonds) und die Fondsgröße als absoluten Betrag, während
diese App Fondsgrößen in Millionen führt (in EUR von justETF, in der gewählten
Währung, wenn du selbst einen Wert einträgst). Eine falsche Zahl wäre
schlimmer als keine, denn ein Wert aus einer Quelle *verdeckt* einen eigenen
Wert, statt die Lücke offen zu lassen. TER, Fondsgröße und Domizil bleiben bei
diesen Fonds deshalb leer – trag sie selbst ein, dann bleiben sie stehen.

**Zur Währung:** Das Börsensuffix wählt die Börse; die Währung kommt aus dem
Kurs. Das aktuelle Yahoo-Plugin lehnt Pence-Codes wie `GBp` ab, statt sie in
`GBP` umzurechnen. Yahoos Tageskurse sind um Splits und Dividenden bereinigt.
Beides weicht vom REST-Artefakt ab; siehe die
[bekannten Vertragsabweichungen](docs/rest-core-contract.md#die-begriffe-die-sich-sonst-niemand-erschließt).

[↑ Inhalt](#inhalt)

---

## Voraussetzungen

- **Python 3.11+** (`make setup` legt die Projekt-`.venv` an; einen anderen
  Interpreter wählst du mit `PYTHON_BOOTSTRAP=python3.12 make setup`)
- **make** (steuert die Einrichtung sowie Start und Stopp der Dienste)
- **overmind** und **tmux** für `make dev-up` (Backend und Dashboard
  zusammen)
- optional **Docker** (um den Container zu betreiben)
- **Node.js 24+ mit npm** (`make setup` installiert die Dashboard-Pakete; das
  Backend und das fertige Docker-Image brauchen kein Node.js auf dem Host)

**Für die Entwicklung brauchst du nichts unter `.libs/`.** `make setup`, die
`dev-*`-Targets, `make test`, `make check` und `make up`/`down` funktionieren
in einem frischen Klon. Targets, die `make help` mit **[Maintainer]**
kennzeichnet (`build`, `push`, `status`, `tag-*`, `version`), brauchen die
private BashLib des Autors und brechen ohne sie mit einem Hinweis ab. Um das
Image selbst zu bauen, nimm statt `make build`
`docker build -f docker/Dockerfile -t mangolila/stockinfo:latest .`.

Für den Maintainer verlinkt `make setup` außerdem die gemeinsamen Helfer unter
`.libs/` (MakeLib, BashLib, ProjectTools) über `scripts/setup-libs.sh`. Es
findet sie über `DEV_MAKE`, `BASH_LIBS` (BashLib-`src`) und `PROJECT_TOOLS`
(ProjectTools-`src`) und installiert den Python-Teil von ProjectTools aus
`requirements-maintainer.txt`. Das Docker-Image braucht nichts davon.

[↑ Inhalt](#inhalt)

---

## Schnellstart

```bash
# 1. Konfiguration anlegen
cp .env.example .env

# 2. Abhängigkeiten installieren (Python-.venv, Dashboard-Pakete)
make setup

# 3. Backend :8000 und Dashboard :5173 mit Auto-Reload starten
make dev-up         # stoppen mit make dev-down · Logs mit make dev-logs
```

`make dev-up` startet beides im Hintergrund über
[overmind](https://github.com/DarthSim/overmind) (braucht overmind und tmux).

`make dev-down` räumt auch nach einem Absturz auf: Es beendet übrig gebliebene
overmind-, tmux- und App-Prozesse dieses Projekts, entfernt eine verwaiste
`.overmind.sock` und gibt die Ports 5173 und 8000 frei. Dazu nutzt es
`dev-ports.sh` aus ProjectTools mit den Ports aus `.dev-ports.conf.sh`, beendet
nur eigene Prozesse in diesem Projekt und lässt sich beliebig oft ausführen.

Der Server läuft dann unter `http://localhost:8000`. Die interaktive
API-Dokumentation (Swagger UI, dunkles Theme) liegt unter
`http://localhost:8000/docs` (im Browser `http://` verwenden, nicht
`https://`).

Erste Abfrage:

```bash
curl http://localhost:8000/quote/IE00B3RBWM25
```

`make help` listet alle verfügbaren Befehle, `make hints` zeigt nützliche
Adressen.

Datenmigrationen von Plugins laufen automatisch vor dem normalen Betrieb, wenn
eine aktive Quelle ihre `data_version` erhöht. StockInfo legt vorher eine
Sicherung an und schreibt jede Migration zusammen mit ihrer neuen Version
fest. Fehlgeschlagene oder fehlende Migrationen sperren fachliche Anfragen
und Aktualisierungen; das Server-Log nennt Plugin, Versionen und Ursache.
Siehe [Datenmigrationen von Plugins](docs/plugin-authors.md#plugin-data-migrations).

[↑ Inhalt](#inhalt)

---

## Sicherheitsmodell

**StockInfo hat keine Anmeldung, und das ist auch nicht vorgesehen.** Jeder
Endpunkt ist für jeden offen, der den Port erreicht – auch die, die Daten
ändern oder löschen:

- `POST /backups/{name}/restore` ersetzt die ganze Datenbank durch eine
  Sicherung.
- `DELETE /instruments/{isin}` und `DELETE /instruments/by-symbol/{symbol}`
  entfernen ein Instrument samt seinem gesamten Kursverlauf.
- `POST /instruments/intake`, `PUT /instruments/by-symbol/{symbol}/isin`,
  `PUT /instruments/by-symbol/{symbol}/overrides` und
  `PATCH /instruments/by-id/{listing_id}/details` fügen gespeicherte Daten
  hinzu oder ändern sie.
- `POST /refresh` (auch für ein einzelnes Instrument) holt Live-Daten von
  Yahoo und justETF und schreibt sie in die Datenbank; `GET /analyze` löst
  Live-Anfragen aus, ohne sie zu speichern.

Die Vorgabe für die Bind-Adresse ist `0.0.0.0`. Nativ gestartet, ist StockInfo
dann aus deinem Netz erreichbar; in Docker erreicht es jede Host-Adresse, auf
der der Port veröffentlicht ist.

**Stell StockInfo nicht ins Internet.** Verwende es nur im Heimnetz. Von außen
verbindest du dich per VPN mit deinem Heimnetz, zum Beispiel mit WireGuard
oder Tailscale. Öffne den Port von StockInfo nie im Router.

Nur auf dem eigenen Rechner nutzen: Nativ gestartet setzt du
`HOST=127.0.0.1`. In Docker veröffentlichst du den Port mit
`-p 127.0.0.1:8000:8000` und lässt `HOST` unverändert; `HOST=127.0.0.1` im
Container macht den Port unerreichbar.

`CORS_ORIGINS` ist **kein** Schutz. Es beschränkt, was ein Browser von einer
anderen Adresse aus tun darf – gegen `curl`, ein Skript oder einen Aufruf von
Server zu Server hilft es nicht. Es verhindert aber, dass andere Webseiten in
deinem Browser die Antworten von StockInfo lesen oder Daten löschen. Trag
deshalb nur die Adressen ein, die du brauchst, statt `*`.

Zwei Grenzen gibt es, und sie betreffen die Last, nicht den Zugriff: Die
globale Aktualisierung nimmt eine nicht blockierende Sperre, damit sich zwei
Läufe nicht überlappen, und justETF wird nur alle `METADATA_TTL_DAYS`
abgefragt (eine ausdrückliche Einzelaktualisierung erzwingt es trotzdem).

[↑ Inhalt](#inhalt)

---

## Die REST-API

![Swagger UI (dunkel)](unraid/screenshots/swagger.png)

| Methode und Pfad | Zweck |
|---|---|
| `GET /health` | Lebenszeichen – antwortet, solange der Prozess lebt |
| `GET /ready` | Bereitschaft – ist der normale Betrieb freigegeben? `503` mit `status` = `degraded` (Datenbank nicht erreichbar **oder** Start fehlgeschlagen, unterschieden über `database`), `migration_pending` oder `starting` |
| `GET /operational` | kann der Prozess seine aktuelle Aufgabe erledigen? Daran hängt der Docker-Healthcheck. `200`, solange eine Migration aussteht oder der Dienst startet, `503`/`degraded` nur, wenn etwas kaputt ist |
| `GET /migration` | was eine bestätigte Migration tun würde – ohne etwas zu ändern |
| `POST /migration/confirm` | führt sie einmal aus, auf ausdrückliche Bestätigung |
| `GET /migration/report` | was tatsächlich passiert ist, auch lange danach noch abrufbar |
| `GET /quote/{isin}` | Kurs per ISIN (bevorzugt Xetra/EUR) |
| `GET /quote?symbol=VGWL.DE` | Kurs per vollständigem Yahoo-Symbol (Suffix = Börse) |
| `GET /quote/{isin}/history` | Intraday-Verlauf (gesammelte Ticks) |
| `GET /quote/{isin}/daily?period=1w\|1m\|3m\|1y\|max` | echte Tagesschlusskurse (EOD, zwischengespeichert) |
| `GET /fx?base=EUR&quote=USD` | Wechselkurs: 1 `base` = Kurs `quote`; `quote_time` ist der Zeitpunkt, den die Quelle nennt, sonst der Abrufzeitpunkt |
| `GET /instruments` | alle zwischengespeicherten Instrumente mit ihrem letzten Kurs |
| `POST /instruments/intake` | löst eine Kennung auf und fügt das Instrument hinzu; auf Wunsch vor dem Speichern eine andere Börse bestätigen |
| `GET /fields` | Beschreibungen der Kern- und Plugin-Felder, Detailschema und Schemaversionen |
| `GET /instrument-types` | deklarierte Asset-Typen aus der laufenden Plugin-Konfiguration, mit Vollständigkeit und Quellenstatus |
| `GET /sources` | konfigurierte Quellenketten und lokale Quellendiagnose |
| `GET /env` | aktuelle Konfiguration (Geheimnisse maskiert) |
| `POST /refresh` · `POST /refresh/{isin}` | alle / ein einzelnes Instrument aktualisieren |
| `PUT /instruments/by-symbol/{symbol}/isin` | nachträglich eine ISIN ergänzen |
| `PATCH /instruments/by-id/{listing_id}/details` | manuelle Detailwerte setzen oder entfernen |
| `DELETE /instruments/{isin}` | ein Instrument samt Verlauf löschen |
| `GET /backups` · `POST /backups` · `POST /backups/{name}/restore` | Sicherungen auflisten / eine anlegen / eine Wiederherstellung vormerken (`202`; sie greift beim nächsten Neustart) |

Für Instrumente **ohne ISIN** holst du den Kurs mit `GET /quote?symbol=…`.
Verlauf, Tageskurse, Aktualisierung und Löschen gibt es auch als
`…/by-symbol/{symbol}`. Ein mehrdeutiges Symbol liefert `409` mit den
möglichen Listings.

Für dynamische Typfilter liest du `GET /instrument-types`, statt Typen aus den
gespeicherten Instrumenten zu sammeln. Neue Plugin-Typen erscheinen ohne feste
Aufzählung im Client. Bekannte Typen bleiben bei Quellenausfällen gelistet;
`complete: false` zeigt fehlende oder ungültige Deklarationen an. Siehe den
[Vertrag des Typkatalogs](docs/rest-core-contract.md#asset-typen-aus-der-plugin-konfiguration).

**Auszug einer Beispielantwort** (`GET /quote/IE00B3RBWM25`; optionale Felder
weggelassen):

```json
{
  "identity": {
    "kind": "listed",
    "ticker": "VGWL",
    "mic": "XETR",
    "isin": "IE00B3RBWM25"
  },
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
  "volatility": 9.95,
  "accumulating": false,
  "source": "yfinance+justetf",
  "cached": false,
  "stale": false,
  "fetched_at": "2026-07-12T18:16:28+00:00"
}
```

Lies `identity.kind`, bevor du auf Identitätsfelder zugreifst: Börsennotierte
Instrumente tragen `ticker` und `mic`, Währungspaare `base` und
`quote_currency`, Instrumente nur mit ISIN tragen `isin`. Kurs- und
Instrumentantworten enthalten außerdem eine `details`-Map mit Werten,
Einheiten, Währungen und Herkunft. Instrumente haben eine dauerhafte
`listing_id`. Siehe die [REST-Referenz](docs/rest-core-contract.md) und die
[Detailfelder](docs/plugin-authors.md#open-detail-fields).

`volatility` ist die Ein-Jahres-Volatilität in Prozent – bei ETFs von justETF,
sonst (annualisiert) aus den zwischengespeicherten Tagesschlusskursen
berechnet. `accumulating` gibt an, ob ein ETF thesauriert (`true`) oder
ausschüttet (`false`).

Felder, die sich nicht bestimmen lassen, sind `null` (etwa `ter` bei
Einzelaktien). Scheitert ein Live-Abruf, liegt aber ein alter Wert im Cache,
kommt dieser Wert mit `"stale": true` statt eines Fehlers. Unbekannte ISIN →
`404`.

[↑ Inhalt](#inhalt)

---

## Konfiguration (.env)

Alle Werte lassen sich über `.env` überschreiben (`cp .env.example .env`):

| Variable | Bedeutung | Vorgabe |
|---|---|---|
| `HOST` / `PORT` | Serveradresse | `0.0.0.0` / `8000` |
| `DATABASE_PATH` | Pfad der SQLite-Datei | `data/stockinfo.db` |
| `CACHE_TTL_HOURS` | Alter, ab dem ein Kurs bei einer Anfrage neu geholt wird | `6` |
| `REFRESH_INTERVAL_HOURS` | Abstand der Hintergrundaktualisierung | `6` |
| `METADATA_TTL_DAYS` | Aktualisierungsabstand für ETF-Metadaten | `7` |
| `DEFAULT_EXCHANGE` | bevorzugte Börse für ISIN-Abfragen (MIC) | `XETR` (Xetra) |
| `STRICT_EXCHANGE` | beim Auflösen einer ISIN die bevorzugte Börse verlangen | `false` |
| `FX_TTL_HOURS` | Cache-Dauer für Wechselkurse | `1` |
| `OPENFIGI_API_KEY` | optionaler Schlüssel für ein höheres OpenFIGI-Limit | leer |
| `EXTRAETF_ETF_URL` / `EXTRAETF_STOCK_URL` | Vorlagen für Profil-Links (Platzhalter `{isin}`) | extraetf.com/… |
| `YAHOO_URL` | Vorlage für den Yahoo-Link (Platzhalter `{symbol}`) | de.finance.yahoo.com/… |
| `CORS_ORIGINS` | Webseiten unter einer anderen Adresse, die die API aufrufen dürfen, als JSON-Liste | `["http://localhost:5173"]` |

[↑ Inhalt](#inhalt)

---

## Dashboard

Ein eigenständiges Web-Frontend liegt in [`dashboard/`](dashboard/) (Vue 3 +
Vite + TypeScript + SCSS), mit festem Kopfbereich (verlinkbare
Reiter-Navigation, **Sprachumschaltung DE/EN** – gespeichert, die
Startsprache folgt dem Browser) und einer Statusleiste
(**Health-Ampel** grün/orange/rot und Version):

- **Assets** – Übersicht mit dem letzten Kurs und **sortierbaren Spalten**
  (Klick auf einen Spaltenkopf: aufsteigend → absteigend → aus; gespeichert);
  hinzufügen (ISIN/Symbol), aktualisieren, löschen, **ISIN nachtragen**; je
  Zeile Links zu **extraETF**, **Yahoo Finance** und einem **JSON-Popup**
  (URL und Ergebnis kopierbar – funktioniert auch mit einfachem `http://`).
  Ein kurzer Hinweis unter der Tabelle (bzw. der Kartenliste auf schmalen
  Bildschirmen) nennt die Grenzen der angezeigten Kurse und Kennzahlen.
- **Kurshistorie** – die Auswahl einer Zeile dockt den Kursverlauf unten im
  Fenster an (immer sichtbar, auch bei langen Listen). Zeitraum
  `1D · 1W · 1M · 3M · 1Y · Max`: `1D` ist die Intraday-Kurve (gesammelte
  Ticks), der Rest sind echte Tagesschlusskurse (EOD). Echte Zeitachse,
  kompakte Achsenbeschriftung.
- **Börsen** – Legende der Yahoo-Suffixe (Börse, Region, Währung).
- **Environment** – aktuelle Konfiguration samt Hinweis zur automatischen
  Aktualisierung; **Themes** – 8 auswählbare, gespeicherte Themes.
- **About** – öffnest du unter **Einstellungen** oder über den Link
  **Über StockInfo** in der Statusleiste. Es erklärt die Grenzen der
  angezeigten Daten und verlinkt die EUPL in der gewählten Sprache sowie die
  Verbrauchererklärung des Anbieters. Ein eigener Link öffnet MangoLilas
  Hinweise zu Finanzinhalten für die Website und Veröffentlichungen. Logo,
  Postanschrift und Website-Link der MangoLila GmbH stehen neben dem Text.
  Auf schmalen Bildschirmen wählst du den Bereich der Einstellungen über die
  Auswahl über dem Inhalt.

```bash
cd dashboard
npm install
npm run dev                # http://localhost:5173
```

Der Vite-Dev-Proxy leitet API-Anfragen automatisch an das Backend weiter
(`http://localhost:8000`) – `VITE_API_BASE_URL` braucht es in der Entwicklung
nicht (bei Bedarf überschreibbar, siehe `dashboard/vite.config.ts`).

Das Backend muss parallel laufen. Beides zusammen: **`make dev-up`** (siehe
Schnellstart).

[↑ Inhalt](#inhalt)

---

## Docker

Installation und Betrieb des Containers: [Docker-Anleitung](docker/README.md)
(englisch).

StockInfo hat keine Anmeldung. Leite den Container-Port nicht ins Internet
weiter; das [Sicherheitsmodell](#sicherheitsmodell) nennt sichere Wege, ihn zu
erreichen.

Veröffentlichtes Image: [mangolila/stockinfo auf Docker Hub](https://hub.docker.com/repository/docker/mangolila/stockinfo/general).

Backend **und** Dashboard laufen in einem Image auf einem Port. Gebaut wird mit
`docker/build.sh` (Konvention des Ökosystems, Version über `gitDockerTag`):

```bash
make build     # Image bauen (docker/build.sh --build)
make up        # Container starten → http://localhost:8000/
make down      # stoppen und entfernen
make docker-logs   # Logs folgen
```

Auf ARM-Macs läuft der Dashboard-Build nativ; das fertige Image verwendet
trotzdem die mit `PLATFORM` gewählte Plattform (Vorgabe `linux/amd64` für
Unraid; `PLATFORM=arm` wählt `linux/arm64`). Der geprüfte Build veröffentlicht
jeweils eine Plattform.

FastAPI liefert das Dashboard selbst aus (relative API-Aufrufe) – ein eigener
Webserver ist nicht nötig. Der Cache liegt im Volume `stockinfo-data` (`/data`
im Container). Die App läuft als Nutzer ohne Root-Rechte (UID 99 / GID 100 –
Unraids `nobody:users`). `docker/entrypoint.sh` bereitet `/data` vor und hält
mit einer klaren Meldung an, wenn das Verzeichnis nicht beschreibbar ist;
siehe die [Docker-Anleitung](docker/README.md#storage-and-permissions).

Um das reine Dateiprofil **vor dem ersten Start** zu wählen, baust du das Image
und schreibst das Profil in dasselbe benannte Volume, das `make up` einbindet:

```bash
make build
./scripts/sources-profile.sh --yaml --target docker
make up
```

Mit `--online --target docker` stellst du die Online-Ketten mit YAML-Rückfall
wieder her. Das Skript kopiert die passende Beispiel-Assetdatei nur, wenn sie
fehlt, sichert eine vorhandene `sources.yaml` und lässt den App-Container
unberührt. Läuft der Container schon, starte ihn nach dem Umschalten neu; die
Quellenketten werden beim Start geladen. Der Weg über das benannte Volume
braucht Docker-Zugriff und ein lokal vorhandenes Image
`mangolila/stockinfo:latest`. Für ein anderes
`make up DATA_VOLUME=other-volume` gibst du dem Skript ebenfalls
`--volume other-volume` mit. Zwischen benannten Volumes und Host-Verzeichnissen
werden keine Daten verschoben.
Verwendet `make up` einen anderen `IMAGE_NAME`, setzt du beim Aufruf des
Skripts `STOCKINFO_IMAGE` auf dieses Image mit dem Tag `:latest`.

**In eine Registry pushen:**

```bash
make build                   # Docker-Hub-Image, lokal geprüft
make push                    # genau diesen Build nach Docker Hub pushen
TARGET=ghcr make build       # alternativ für die GitHub Container Registry bauen
TARGET=ghcr make push        # zum selben Ziel pushen wie beim Build
```

`make build` kopiert die [EUPL-Lizenz](LICENSE), ihren
[deutschen Text](LICENSE.de.txt), die
[Lizenz- und Anbietererklärung](LICENSING.md), die
[MIT-Lizenz von `plugin_api`](plugin_api/LICENSE) und die MIT-Lizenz des
Beispiel-Plugins ins Image. Es prüft die Dateien, ihre SHA-256-Hashes, die
Zielarchitektur sowie die OCI-Labels für Lizenz und Quelle, bevor es einen
Build als bereit zum Pushen vermerkt. Ein eigener Schritt zum Kopieren der
Lizenzen ist nicht nötig. Ein fehlgeschlagener Build löscht die vorherige
Push-Markierung; `make push` lehnt außerdem ein Image aus einem anderen
Quell-Commit oder für ein anderes Registry-Ziel ab. Der versionierte Image-Tag
enthält den Hash des Quell-Commits; veröffentliche diesen Commit vor dem Image,
damit Empfänger den zugehörigen Quelltext bekommen.

Nach einem erfolgreichen Image-Push nach Docker Hub lädt `make push`
[`docker/README.md`](docker/README.md) hoch, die Beschreibung für den
Container, mit absoluten GitHub-Links für Dokumente und Bilder. Andere
Registries überspringen diesen Schritt. Installiere dafür Python 3.11+ und
[Pandoc](https://pandoc.org/installing.html). Der Bash-Einstieg installiert
seine Abhängigkeiten in einer eigenen Umgebung im Nutzer-Cache und lässt die
Projekt-`.venv` unberührt. Die Links zeigen auf den veröffentlichten Branch
`master`.

Setz `DOCKER_PW_FILE` auf eine Docker-Hub-Tokendatei außerhalb des Repositorys
(Vorgabe: `${DOCKER_CONFIG:-$HOME/.docker}/dockerhub.sec`). Das Token braucht
die Rechte Read, Write und Delete. Das Skript prüft zuerst, ob README und
Tokendatei lesbar sind; die Zugangsdaten bekommt nur Docker Hub.

Vorschau ohne Docker-Hub-Zugangsdaten (die erste Einrichtung lädt eventuell
Pakete herunter):

```bash
./.libs/ProjectTools/src/bash/dockerhub-readme.sh --preview
# Ausgabe: docker/preview/README.md
```

Die Vorschau ist versioniert und gehört in denselben Commit wie die Änderung an
`docker/README.md`; `make docs-check` meldet sonst ein Problem.

Scheitert der Upload der Beschreibung, scheitert auch `make push`, das Image
ist dann aber schon veröffentlicht. Nur die Beschreibung erneut übertragen:

```bash
./.libs/ProjectTools/src/bash/dockerhub-readme.sh --publish
```

Vorgaben: Repository aus den Projekteinstellungen, Branch `master`.
Überschreiben mit `--repository`, `--ref` oder `--output`. `--username` für die
Anmeldung als Organisation, `--description` ändert die Kurzbeschreibung. Das
Skript prüft die gespeicherte Übersicht und hält die Grenze von 25.000 Bytes
ein, ohne zu kürzen. Ohne Argumente zeigt es die Hilfe.

[↑ Inhalt](#inhalt)

---

## Unraid

Installation, Einstellungen und Betrieb stehen in der
[Unraid-Anleitung](unraid/README.md) (englisch).

[↑ Inhalt](#inhalt)

---

## Tests

```bash
make test                       # Doku, Backend, Plugin-API, Beispiel-Plugin und Dashboard
make test-backend               # nur Backend (pytest)
make test-dashboard             # nur Dashboard (ESLint und Vitest)
make docs-check                 # nur Doku: Links, Befehle, Variablen, abhängige Dateien
make check                      # alles, was ohne Netz läuft, dazu Ruff und Typprüfungen
```

`make docs-check` prüft die Nutzerdoku gegen das Projekt; die Regeln stehen in
`.docs-check.conf.sh`. Es braucht ProjectTools unter `.libs/`; ohne sie gibt
das Target einen Hinweis aus, und die übrigen Tests laufen trotzdem.
`make setup` installiert außerdem einen Git-Pre-Commit-Hook, der die Prüfung
ausführt und einen Commit anhält, wenn sie Probleme meldet.

Der normale Backend-Lauf enthält Tests mit der Markierung `integration`, die
echte externe APIs oder den Paketindex aufrufen. `make check` lässt sie weg und
ergänzt `ruff` und die Typprüfung des Dashboards (`vue-tsc`). Nur die
Online-Tests ausschließen:

```bash
.venv/bin/pytest -m "not integration"
```

Backend-Tests verwenden temporäre Datenbanken. Die Testumgebung sperrt
Verbindungen zur Arbeitsdatenbank; zusätzliche Testdatenbanken gehören unter
`tmp_path`.

[↑ Inhalt](#inhalt)

---

## Releases und Changelog

`make changelog` erzeugt [CHANGELOG.md](CHANGELOG.md) lokal neu, aus den
Release-Tags und Conventional Commits. Es committet und pusht nicht. Die
erzeugte Datei wird beim nächsten Lauf ersetzt; ihr Inhalt kommt aus den
Nachrichten der Commits und Release-Tags. Mit
`make changelog PYTHON=/path/to/python3` wählst du einen anderen
Python-Interpreter (Python 3.9+).

`make tag-major`, `make tag-minor` und `make tag-patch` erhöhen die Version,
committen, taggen und pushen sie und erzeugen, committen und pushen danach den
Changelog. Mit `MSG="Release summary"` gibst du die Nachricht des Release-Tags
mit. Ein Release braucht einen sauberen Arbeitsbaum und die gemeinsamen
Bibliotheken BashLib und ProjectTools. Scheitert der Changelog-Schritt, nachdem
der Tag gepusht ist, behebst du die Ursache und wiederholst mit
`python3 .libs/ProjectTools/src/python/changelog.py --publish`, ohne die
Version erneut zu erhöhen.

[↑ Inhalt](#inhalt)

---

## Projektstruktur

```
app/                    # FastAPI-Backend
  main.py               #   App-Aufbau, Routen, Start des Schedulers
  config.py             #   Konfiguration (.env)
  persistence/          #   SQLite über SQLModel: Schema, Migrationen, Datenzugriff (nur hier)
  resolver.py           #   ISIN → Symbol/Börse (OpenFIGI + Yahoo)
  providers/            #   Datenquellen: yfinance, justETF, OpenFIGI
  plugins/              #   mitgelieferte Quellen nach der Plugin-API
  services/             #   Kursabruf + Cache-/TTL-Logik
  scheduler.py          #   regelmäßige Hintergrundaktualisierung
  routers/              #   HTTP-Endpunkte (Kurse, Dashboard)
  docs.py               #   Swagger UI im dunklen Theme (/docs)
dashboard/              # Vue-Dashboard (eigenständige App)
plugin_api/             # unabhängiger Plugin-Vertrag, Beispiele und Rollentests
contract/               # REST-Vertrag, HTTP-Fixtures und OpenAPI-Snapshot
examples/               # Quellenprofile und Beispiele für von Hand gepflegte Assets
tests/                  # Backend-Tests (pytest)
docker/                 # Dockerfile, build.sh (Build eines einzigen Images)
unraid/                 # Unraid-Anleitung und Screenshots (README + CA-Template)
Makefile                # Start/Stopp der Dienste (make help)
CHANGELOG.md            # erzeugte Historie der getaggten Releases
```

Aktuelle Referenzen: [REST-API](docs/rest-core-contract.md),
[Quellenkonfiguration](docs/plugins.md),
[Plugin-Entwicklung](docs/plugin-authors.md) und
[Vertragsprüfungen](contract/README.md). Historische Entwürfe und Pläne liegen
unter [`docs/superpowers/`](docs/superpowers/).

[↑ Inhalt](#inhalt)

---

## Support

StockInfo ist für den Eigengebrauch des Autors gebaut und wird kostenlos
geteilt. [Issues](https://github.com/MikeMitterer/stockinfo/issues) und Pull
Requests werden gelesen, ohne Zusage auf Antwort, Fehlerbehebung oder neue
Funktion.

[↑ Inhalt](#inhalt)

---

## Lizenz

Der Anwendungscode von StockInfo steht unter der
**[European Union Public Licence 1.2 only](LICENSE)** (`EUPL-1.2`), also nur
dieser Version. Private und gewerbliche Nutzung, Änderung, Weitergabe, Verkauf
und Hosting sind nach ihren Bedingungen ohne zusätzliche kostenpflichtige
Lizenz erlaubt. Erforderliche Hinweise bleiben erhalten, und die Pflichten zu
Quelltext und Copyleft gelten, auch für erfasste Netzwerkdienste. Siehe
[Lizenz- und Quelltextinformationen](LICENSING.md) und den
[deutschen Lizenztext](LICENSE.de.txt).

Copyright © 2026 **Michael Mitterer**, Autor und Rechteinhaber.
**MangoLila GmbH** ist Anbieter und Lizenzgeber. Ihre eigene
[Erklärung für Verbraucher](LICENSING.md#mangolilas-declaration-for-consumers)
gilt neben dem unveränderten EUPL-Text.

Das unabhängige Paket [`plugin_api/`](plugin_api/) und sein Beispiel-Plugin
stehen weiter unter [MIT](plugin_api/LICENSE). Komponenten Dritter behalten
ihre eigenen Lizenzen.

[↑ Inhalt](#inhalt)
