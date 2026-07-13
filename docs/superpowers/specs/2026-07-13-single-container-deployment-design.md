# StockInfo — Single-Container-Deployment (FastAPI serviert Dashboard) + build.sh

**Datum:** 2026-07-13
**Status:** Design freigegeben

## Ziel

Die gesamte App — FastAPI-Backend **und** Vue-Dashboard — in **einem** Docker-Image
ausliefern, damit sie auf **Unraid** als ein Container (ein Port, ein Volume) läuft.
Dazu ein `docker/build.sh` nach der Ökosystem-Konvention (`docker-build-script`-Skill),
das mit dem Dockerfile zusammenspielt.

## Motivation

Aktuell zwei Images (Backend `Dockerfile` + Dashboard `dashboard/Dockerfile`), verbunden
über `docker-compose.yml`. Das Dashboard bäckt seine API-URL **zur Build-Zeit** fest ein
(`VITE_API_BASE_URL=http://localhost:8000`). Auf Unraid ruft der Browser aber nicht
`localhost` — die feste URL bricht. Zwei Container + hartkodierte URL sind für ein NAS
unnötig umständlich.

**Kernidee:** FastAPI liefert das gebaute Dashboard als statische Dateien gleich mit aus.
Alles läuft dann auf **einem Origin, einem Port** → das Dashboard ruft die API **relativ**
auf (`/quote/…`), unabhängig davon welche IP/welchen Port Unraid vergibt.

## Architektur

Ein Multi-Stage-Dockerfile:

1. **Stage 1 (`node:22-slim`)** baut `dashboard/` → `dist/`. `VITE_API_BASE_URL` bleibt
   **leer** → relative API-Aufrufe im Bundle.
2. **Stage 2 (`python:3.12-slim`)** installiert `requirements.txt`, kopiert `app/` und das
   `dist/` aus Stage 1 nach `/app/web`. Einziger Prozess: `uvicorn`, Port 8000, Volume
   `/data`, Healthcheck auf `/health`.

FastAPI mountet die statischen Dateien **nach** allen API-Routern an `/`. Die API-Routen
(`/quote`, `/instruments`, `/env`, `/health`, `/refresh`) haben Vorrang; alles andere liefert
das SPA. Das Dashboard nutzt **Hash-Routing** → kein Server-seitiger SPA-Fallback nötig,
`index.html` an `/` genügt.

## Komponenten & Änderungen

### Neu
| Datei | Zweck |
|---|---|
| `docker/Dockerfile` | Vereinheitlichtes Multi-Stage-Image (Kontext = Projekt-Root) |
| `docker/build.sh` | Build/Push-Script aus `docker-build-script`-Skill-Template |

### Geändert
| Datei | Änderung |
|---|---|
| `app/main.py` | StaticFiles-Mount an `/` **nach** den Routern — nur wenn `STATIC_DIR` existiert |
| `app/config.py` | Neue Setting `static_dir: str = "/app/web"` |
| `dashboard/src/config.ts` | Default `API_BASE_URL` von `http://localhost:8000` → `''` (same-origin/relativ) |
| `dashboard/vite.config.ts` | Dev-Proxy für die fünf API-Präfixe → `http://localhost:8000` |
| `dashboard/.env` / `.env.example` | Feste URL entfernen (Dev nutzt Proxy); `.env.example` dokumentiert optionalen Override |
| `.dockerignore` (Root = Build-Kontext) | Ergänzen: `dashboard/node_modules`, `dashboard/dist`, `dashboard/.env` |
| `docker-compose.yml` | Auf das eine Image umstellen (ein Service) |
| `Makefile` | `build`/`push`-Targets → `docker/build.sh` |

### Entfernt
- `Dockerfile` (Root, alt) und `dashboard/Dockerfile` (alt) — durch `docker/Dockerfile` ersetzt.

## Lokale Entwicklung bleibt funktionsfähig (verifiziert)

**Backend-Dev (`make dev` / `make dev-up`):** unverändert. Der StaticFiles-Mount ist an die
Existenz von `STATIC_DIR` (`/app/web`, absoluter Container-Pfad) gekoppelt — lokal nicht
vorhanden → Mount übersprungen → `uvicorn` läuft wie bisher.

**WebUI-Dev (vite auf 5173):** Statt der Cross-Origin-`.env`-URL (heute CORS 5173→8000)
übernimmt ein **vite-Dev-Proxy** die fünf API-Präfixe. Relative URLs funktionieren dann in
Dev **und** Prod identisch:
- Dev: `/quote` → vite-Proxy → `localhost:8000` (kein CORS, keine `.env`-Abhängigkeit).
- Prod: `/quote` → selber Origin → FastAPI.

Der Proxy deckt genau ab: `/quote`, `/instruments`, `/env`, `/health`, `/refresh` (aus allen
Routen verifiziert). Keine Kollision mit dem SPA (Hash-Routing, Assets unter `/`, `/@vite`,
`/src`). Voraussetzung im Dev: laufendes Backend auf 8000 (via `make dev-up` gegeben).

## build.sh (Skill-Konvention)

Aus `docker-build-script`-Template nach `docker/build.sh`, Platzhalter gesetzt:

| Platzhalter | Wert |
|---|---|
| `@@NAME@@` | `stockinfo` |
| `@@NAMESPACE@@` | `mangolila` |
| `@@GITHUB_OWNER@@` | `MikeMitterer` |
| `@@PORT@@` | `8000` |

- Lokales Image: `mangolila/stockinfo` · GHCR: `ghcr.io/MikeMitterer/mangolila-stockinfo`.
- Optionen: `--build [x86|arm|all]`, `--push` (Registry-Ziel per `TARGET=ghcr|dockerhub|ecr`,
  Default `ghcr`), `--images`, `--samples`, `--update`.
- Versioniert via `gitDockerTag` → **braucht einen Git-Tag**. Repo hat aktuell **keinen** →
  im Plan wird `v0.1.0` angelegt.
- `samples`-Array mit echtem `docker run` für Unraid (Port 8000, Volume `/data`, `.env`).
- Build-Kontext = `..` (Projekt-Root), Dockerfile = `docker/Dockerfile` — entspricht den
  Template-Defaults von `buildSingleArchImage`/`buildMultiArchImage`.
- `prepareConfig()` bleibt No-op (Multi-Stage-Dockerfile macht alles selbst).

## Deployment auf Unraid

Ein Container:
- Port-Mapping `Host:8000 → 8000`
- Pfad-Mapping `/mnt/user/appdata/stockinfo → /data`
- Env-Variablen aus `.env`

Dashboard und API laufen über denselben Port.

## Fehlerbehandlung

- **StaticFiles fehlt** (Dev): Mount wird konditional übersprungen, kein Fehler.
- **Kein Git-Tag**: `build.sh` bricht mit klarer Meldung + Tipp (`semVerBump patch`) ab.
- **API vs. Static**: Router vor dem Mount registriert → API-Routen gewinnen; unbekannte
  Pfade → `index.html` (SPA).
- **Healthcheck**: `curl /health` (unverändert), da `/health` weiterhin JSON liefert.

## Tests

- Backend-Suite (73) muss grün bleiben; neuer Test: StaticFiles-Mount wird bei fehlendem
  `STATIC_DIR` übersprungen (App startet ohne Fehler) und bei vorhandenem Verzeichnis wird
  `/` bedient.
- Frontend-Suite (10) muss grün bleiben (Proxy-Config berührt Vitest nicht).
- Verifikation: `bash -n docker/build.sh` (Syntax), `grep '@@' docker/build.sh` (leer),
  lokaler Image-Build + `docker run` → `/` liefert Dashboard, `/health` liefert JSON.

## Nicht enthalten (YAGNI)

Kein nginx, kein Reverse-Proxy im Image, keine Auth (separates Thema), kein
Registry-Push-Setup/CI (Verteilung erfolgt manuell durch den Nutzer).
