# Single-Container-Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** StockInfo (FastAPI-Backend + Vue-Dashboard) als ein Docker-Image ausliefern, das auf Unraid als ein Container läuft — plus ein `docker/build.sh` nach Ökosystem-Konvention.

**Architecture:** Multi-Stage-Dockerfile: node baut das Dashboard, das Python-Image serviert das gebaute Bundle via FastAPI-StaticFiles am selben Origin. Das Dashboard ruft die API relativ auf; im lokalen Dev leitet ein vite-Proxy die API-Präfixe ans Backend weiter.

**Tech Stack:** FastAPI, uvicorn, StaticFiles · Vue 3 + Vite · Docker Multi-Stage · BashLib `build.lib.sh`/`docker.lib.sh`/`version.lib.sh`.

## Global Constraints

- Ein Container, ein Prozess (`uvicorn`), ein Port (`8000`), ein Volume (`/data`). Kein nginx.
- Dashboard ruft API **relativ** auf (`API_BASE_URL = ''`) — same-origin in Prod, vite-Proxy in Dev.
- Lokaler Dev-Flow muss funktionsfähig bleiben: `make dev`/`make dev-up` (Backend) und vite auf 5173 (WebUI).
- StaticFiles-Mount ist **konditional** (`STATIC_DIR` muss existieren) — sonst startet der Dev-Server ohne Dashboard-Verzeichnis nicht.
- API-Routen haben Vorrang vor dem Static-Mount (Mount wird als Letztes registriert).
- Build-Kontext = Projekt-Root; Dockerfile = `docker/Dockerfile`; `build.sh` liegt in `docker/`.
- `build.sh` aus dem `docker-build-script`-Template, Platzhalter: `NAME=stockinfo`, `NAMESPACE=mangolila`, `GITHUB_OWNER=MikeMitterer`, `PORT=8000`. Keine `@@…@@` dürfen übrig bleiben.
- `build.sh` versioniert via `gitDockerTag` → Repo braucht einen Git-Tag (`v0.1.0`).
- Backend-Tests (73) und Frontend-Tests (10) bleiben grün.
- Branch: `feat/single-container-deployment` (bereits angelegt, Spec dort committet).

---

### Task 1: Backend serviert das statische Dashboard

**Files:**
- Modify: `app/config.py:44` (neue Setting `static_dir`)
- Modify: `app/main.py` (Import + Mount-Funktion + Aufruf am Modulende)
- Test: `tests/test_static_mount.py` (neu)

**Interfaces:**
- Consumes: `Settings.static_dir` (str), `get_settings()`.
- Produces: `mount_dashboard(app: FastAPI, static_dir: str) -> bool` in `app/main.py` — mountet StaticFiles an `/` wenn `static_dir` ein existierendes Verzeichnis ist, gibt `True`/`False` zurück.

- [ ] **Step 1: Failing test schreiben**

`tests/test_static_mount.py`:
```python
"""Tests für den konditionalen StaticFiles-Mount des Dashboards."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import mount_dashboard


def test_mount_wird_uebersprungen_wenn_verzeichnis_fehlt(tmp_path) -> None:
    app = FastAPI()
    mounted = mount_dashboard(app, str(tmp_path / "gibt-es-nicht"))
    assert mounted is False


def test_mount_serviert_index_wenn_vorhanden(tmp_path) -> None:
    (tmp_path / "index.html").write_text("<h1>StockInfo Dashboard</h1>")
    app = FastAPI()
    mounted = mount_dashboard(app, str(tmp_path))
    assert mounted is True

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "StockInfo Dashboard" in response.text
```

- [ ] **Step 2: Test ausführen — muss fehlschlagen**

Run: `.venv/bin/python -m pytest tests/test_static_mount.py -v`
Expected: FAIL — `ImportError: cannot import name 'mount_dashboard' from 'app.main'`

- [ ] **Step 3: Setting `static_dir` ergänzen**

In `app/config.py` nach dem `api_key`-Feld (Zeile 44) einfügen:
```python
    # Statisches Dashboard — Verzeichnis mit dem gebauten Vue-Bundle.
    # Existiert es nicht (z.B. lokaler Dev), wird nichts ausgeliefert.
    static_dir: str = "/app/web"
```

- [ ] **Step 4: Mount-Funktion + Aufruf in `app/main.py`**

Imports oben ergänzen (nach `from collections.abc import AsyncIterator`):
```python
import os
```
Und bei den FastAPI-Imports:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
```

Am **Ende** von `app/main.py` (nach der `health()`-Funktion) anfügen:
```python
def mount_dashboard(app: FastAPI, static_dir: str) -> bool:
    """Mountet das gebaute Dashboard als statische Dateien an ``/``.

    Wird als Letztes registriert, damit die API-Routen Vorrang behalten. Fehlt
    das Verzeichnis (z.B. im lokalen Dev ohne Build), wird nichts gemountet.

    Args:
        app: Die FastAPI-Instanz.
        static_dir: Pfad zum Verzeichnis mit dem gebauten Bundle (index.html …).

    Returns:
        ``True`` wenn gemountet, sonst ``False``.
    """
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="dashboard")
        return True
    return False


mount_dashboard(app, get_settings().static_dir)
```

- [ ] **Step 5: Tests ausführen — müssen bestehen**

Run: `.venv/bin/python -m pytest tests/test_static_mount.py -v`
Expected: PASS (2 passed)

- [ ] **Step 6: Volle Backend-Suite + Lint**

Run: `.venv/bin/python -m pytest -q && .venv/bin/ruff check app/ tests/`
Expected: `75 passed`, `All checks passed!`
(Der Default `static_dir=/app/web` existiert im Testlauf nicht → Mount übersprungen → `/health` etc. unverändert.)

- [ ] **Step 7: Commit**

```bash
git add app/config.py app/main.py tests/test_static_mount.py
git commit -m "feat(api): Dashboard als statische Dateien ausliefern (konditionaler Mount)"
```

---

### Task 2: Dashboard auf relative URLs + vite-Dev-Proxy

**Files:**
- Modify: `dashboard/src/config.ts` (Default-Base auf `''`)
- Modify: `dashboard/vite.config.ts` (Dev-Proxy)
- Modify: `dashboard/.env` (lokale Arbeitskopie, git-ignored — URL entfernen)
- Modify: `dashboard/.env.example` (Override dokumentieren)

**Interfaces:**
- Consumes: `import.meta.env.VITE_API_BASE_URL`.
- Produces: `API_BASE_URL` = `''` (relativ) sofern kein Env-Override; Dev-Proxy für `/quote`, `/instruments`, `/env`, `/health`, `/refresh` → `http://localhost:8000` (Ziel via `VITE_DEV_API_TARGET` überschreibbar).

- [ ] **Step 1: `config.ts` auf relativen Default umstellen**

`dashboard/src/config.ts` komplett ersetzen:
```ts
/** Basis-URL der StockInfo-API.
 *
 * Leer (Default) → relative Aufrufe (`/quote/…`): in Prod same-origin (FastAPI
 * serviert das Dashboard), im Dev leitet der vite-Proxy die API-Präfixe ans
 * Backend weiter. Über `VITE_API_BASE_URL` bei Bedarf überschreibbar.
 */
export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? ''
```

- [ ] **Step 2: Vite-Dev-Proxy ergänzen**

`dashboard/vite.config.ts` komplett ersetzen:
```ts
/// <reference types="vitest/config" />
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// Ziel-Backend für den Dev-Proxy (überschreibbar per Env).
const apiTarget = process.env.VITE_DEV_API_TARGET ?? 'http://localhost:8000'

// Nur diese Präfixe sind API-Routen — alles andere serviert das SPA (Hash-Routing).
const apiPrefixes = ['/quote', '/instruments', '/env', '/health', '/refresh']

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: Object.fromEntries(
      apiPrefixes.map((prefix) => [prefix, { target: apiTarget, changeOrigin: true }]),
    ),
  },
  test: { environment: 'jsdom' },
})
```

- [ ] **Step 3: Lokale `.env` bereinigen + Beispiel dokumentieren**

`dashboard/.env` (git-ignored, lokale Arbeitskopie) komplett ersetzen:
```
# API wird im Dev über den vite-Proxy erreicht (siehe vite.config.ts).
# Leer lassen → relative URLs. Nur bei Bedarf einen direkten Override setzen:
# VITE_API_BASE_URL=http://localhost:8000
```

`dashboard/.env.example` komplett ersetzen:
```
# Optionaler Override der API-Basis-URL.
# Leer/ungesetzt (Default) → relative URLs; im Dev leitet der vite-Proxy
# die API-Präfixe an das Backend (http://localhost:8000) weiter.
# VITE_API_BASE_URL=http://localhost:8000
```

- [ ] **Step 4: Frontend-Tests + Build (Typecheck)**

Run: `cd dashboard && npm test && npm run build`
Expected: `Tests  10 passed (10)`; Build ohne Typfehler (`vue-tsc` + `vite build` grün).
(Die api-client-Tests mocken `fetch` und prüfen kein Base-URL-Präfix → unberührt.)

- [ ] **Step 5: Manuelle Dev-Verifikation (Proxy)**

Run:
```bash
cd /Volumes/DevLocal/DevWeb/Production/StockInfo
make dev-up
sleep 3
# vite-Proxy: /health über 5173 muss vom Backend (8000) beantwortet werden
curl -fsS http://localhost:5173/health
make dev-down
```
Expected: `curl` liefert JSON `{"status":"ok","version":"0.1.0"}` (über den Proxy vom Backend).

- [ ] **Step 6: Commit**

```bash
git add dashboard/src/config.ts dashboard/vite.config.ts dashboard/.env.example
git commit -m "feat(dashboard): relative API-URLs + vite-Dev-Proxy für lokalen Dev-Flow"
```
(`dashboard/.env` ist git-ignored und wird nicht committet — nur die Arbeitskopie geändert.)

---

### Task 3: Vereinheitlichtes `docker/Dockerfile` + `.dockerignore`

**Files:**
- Create: `docker/Dockerfile`
- Modify: `.dockerignore` (Root = Build-Kontext)
- Delete: `Dockerfile` (Root, alt), `dashboard/Dockerfile` (alt)

**Interfaces:**
- Consumes: `dashboard/` (Quelle), `app/`, `requirements.txt` aus dem Projekt-Root; `STATIC_DIR=/app/web` aus Task 1.
- Produces: lokales Image `mangolila/stockinfo`, Dashboard unter `/app/web`, Port 8000.

- [ ] **Step 1: `docker/Dockerfile` anlegen**

```dockerfile
# ─── Stage 1: Dashboard bauen ─────────────────────────────────────────────────
FROM node:22-slim AS dashboard

WORKDIR /dashboard

COPY dashboard/package.json dashboard/package-lock.json ./
RUN npm ci

COPY dashboard/ ./

# Leere API-Basis-URL → das Bundle ruft die API relativ auf (same-origin).
ENV VITE_API_BASE_URL=""
RUN npm run build

# ─── Stage 2: Backend + statisches Dashboard ──────────────────────────────────
FROM python:3.12-slim

# git für die justetf-scraping-Abhängigkeit (git+https), curl für den Healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Gebautes Dashboard aus Stage 1 — FastAPI serviert es an / (siehe STATIC_DIR).
COPY --from=dashboard /dashboard/dist ./web

# Cache liegt im Volume /data (überlebt Container-Neustarts)
ENV HOST=0.0.0.0 \
    PORT=8000 \
    DATABASE_PATH=/data/stockinfo.db \
    STATIC_DIR=/app/web
VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT}/health" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host \"$HOST\" --port \"$PORT\""]
```

- [ ] **Step 2: Root-`.dockerignore` um Dashboard-Artefakte ergänzen**

`.dockerignore` komplett ersetzen (bestehende Einträge + Dashboard):
```
.venv/
data/
*.db
__pycache__/
*.pyc
.git/
.gitignore
uvicorn.log
tests/
.env
.idea/
.libs/
dashboard/node_modules
dashboard/dist
dashboard/.env
docs/
```

- [ ] **Step 3: Alte Dockerfiles entfernen**

```bash
git rm Dockerfile dashboard/Dockerfile
```

- [ ] **Step 4: Image bauen (direkt, ohne build.sh — das kommt in Task 4)**

Run:
```bash
cd /Volumes/DevLocal/DevWeb/Production/StockInfo
docker build -f docker/Dockerfile -t mangolila/stockinfo:plantest .
```
Expected: Build läuft durch beide Stages ohne Fehler; letzte Zeile `naming to docker.io/mangolila/stockinfo:plantest`.

- [ ] **Step 5: Container starten und beide Origins prüfen**

Run:
```bash
docker run --rm -d --name stockinfo-plantest -p 8099:8000 mangolila/stockinfo:plantest
sleep 4
echo "--- /health ---"; curl -fsS http://localhost:8099/health
echo; echo "--- / (Dashboard) ---"; curl -fsS http://localhost:8099/ | grep -o '<title>[^<]*</title>'
docker stop stockinfo-plantest
docker image rm mangolila/stockinfo:plantest
```
Expected:
- `/health` → JSON `{"status":"ok","version":"0.1.0"}`
- `/` → `<title>StockInfo · MangoLila</title>` (das SPA wird ausgeliefert)

- [ ] **Step 6: Commit**

```bash
git add docker/Dockerfile .dockerignore
git rm --cached Dockerfile dashboard/Dockerfile 2>/dev/null || true
git commit -m "feat(docker): vereinheitlichtes Multi-Stage-Image (Backend serviert Dashboard)"
```

---

### Task 4: `docker/build.sh` aus dem Skill-Template + Git-Tag

**Files:**
- Create: `docker/build.sh`
- Create: git tag `v0.1.0`

**Interfaces:**
- Consumes: `docker/Dockerfile` (liest `FROM`), BashLib (`$BASH_LIBS`), Git-Tag (für `gitDockerTag`).
- Produces: `docker/build.sh` mit `--build`/`--push`/`--images`/`--samples`/`--update`; lokales Image `mangolila/stockinfo`.

- [ ] **Step 1: Template kopieren und Platzhalter ersetzen**

Run:
```bash
cd /Volumes/DevLocal/DevWeb/Production/StockInfo
mkdir -p docker
sed -e 's/@@NAMESPACE@@/mangolila/g' \
    -e 's/@@NAME@@/stockinfo/g' \
    -e 's/@@GITHUB_OWNER@@/MikeMitterer/g' \
    -e 's/@@PORT@@/8000/g' \
    /Users/macminipro/.claude/skills/docker-build-script/templates/build.sh \
    > docker/build.sh
chmod +x docker/build.sh
```

- [ ] **Step 2: `samples`-Array für Unraid anpassen**

In `docker/build.sh` den `declare -a samples=(...)`-Block ersetzen durch:
```bash
declare -a samples=(
"# StockInfo starten (Unraid: Cache im gemappten Pfad) ||
\t     docker run --name ${NAME} \\
\t         --rm -p 8000:8000 \\
\t         -v /mnt/user/appdata/stockinfo:/data \\
\t         --env-file .env \\
\t         ${NAMESPACE}/${NAME}
"
)
```

- [ ] **Step 3: Keine Platzhalter übrig + Syntax-Check**

Run:
```bash
grep -n '@@' docker/build.sh || echo "OK: keine Platzhalter"
bash -n docker/build.sh && echo "OK: Syntax gültig"
```
Expected: `OK: keine Platzhalter` und `OK: Syntax gültig`.

- [ ] **Step 4: Git-Tag `v0.1.0` anlegen (für gitDockerTag)**

Run:
```bash
git add docker/build.sh
git commit -m "feat(docker): build.sh (Build/Push nach Ökosystem-Konvention)"
git tag -a v0.1.0 -m "Initial release: Single-Container-Deployment"
```
Expected: Commit + Tag angelegt (`git tag -l` zeigt `v0.1.0`).

- [ ] **Step 5: `build.sh --help` und `--build` verifizieren**

Run:
```bash
BASH_LIBS="$(pwd)/.libs/BashLib/src" docker/build.sh --help
BASH_LIBS="$(pwd)/.libs/BashLib/src" docker/build.sh --build
BASH_LIBS="$(pwd)/.libs/BashLib/src" docker/build.sh --images
```
Expected:
- `--help` zeigt Optionen, `Target: ghcr → ghcr.io`, `Base Image: python:3.12-slim`.
- `--build` baut `mangolila/stockinfo:<gitDockerTag>` erfolgreich, schreibt `docker/.last-build-tag`.
- `--images` listet das gebaute Image.

(Falls `gitDockerTag` rc=3 „dirty" meldet: uncommittete Änderungen erst committen. `.libs/`-Symlink muss vorhanden sein; sonst `BASH_LIBS` auf den realen Pfad zeigen lassen.)

- [ ] **Step 6: Aufräumen (Test-Image des Builds behalten ist ok) + Commit der `.gitignore`-Ergänzung**

`.gitignore` um die build.sh-Artefakte ergänzen (falls nicht vorhanden):
```
docker/logs/
docker/.last-build-tag
```
Run:
```bash
git add .gitignore
git commit -m "chore(docker): build.sh-Artefakte ignorieren"
```

---

### Task 5: `docker-compose.yml` + Makefile + README verdrahten

**Files:**
- Modify: `docker-compose.yml` (ein Service)
- Modify: `Makefile` (Docker-Gruppe: `build`/`push`, `up` auf neues Dockerfile, hints)
- Modify: `README.md` (Docker-/Deployment-Abschnitt)

**Interfaces:**
- Consumes: `docker/Dockerfile`, `docker/build.sh` aus Tasks 3/4.
- Produces: `make up` (ein Container via compose), `make build`/`make push` (delegieren an `docker/build.sh`).

- [ ] **Step 1: `docker-compose.yml` auf einen Service umstellen**

Komplett ersetzen:
```yaml
services:
  stockinfo:
    build:
      context: .
      dockerfile: docker/Dockerfile
    image: mangolila/stockinfo
    ports:
      - "${PORT:-8000}:8000"
    env_file:
      - .env
    environment:
      # Im Container feste Werte — überschreiben ggf. .env
      HOST: 0.0.0.0
      PORT: 8000
      DATABASE_PATH: /data/stockinfo.db
    volumes:
      - stockinfo-data:/data
    restart: unless-stopped

volumes:
  stockinfo-data:
```

- [ ] **Step 2: `compose config` prüfen**

Run: `docker compose config -q && echo "OK: compose gültig"`
Expected: `OK: compose gültig` (keine Warnungen zu fehlenden Services/Volumes).

- [ ] **Step 3: Makefile — Docker-Gruppe erweitern**

In `Makefile` den `##@ Docker`-Block (ab Zeile 103) ersetzen durch:
```makefile
##@ Docker

.PHONY: up
up: ## Container-Stack starten (ein Image, Dashboard + API auf Port $(PORT))
	docker compose up -d --build
	@echo -e "  $(GREEN)✓$(RESET) Läuft — App $(BLUE)http://localhost:$(PORT)/$(RESET)"

.PHONY: down
down: ## Container-Stack stoppen und entfernen
	docker compose down

.PHONY: docker-logs
docker-logs: ## Container-Logs folgen
	docker compose logs -f

.PHONY: build
build: ## Docker-Image bauen (docker/build.sh — versioniert via gitDockerTag)
	docker/build.sh --build

.PHONY: push
push: ## Image in Registry pushen (TARGET=ghcr|dockerhub|ecr, Default ghcr)
	docker/build.sh --push
```

- [ ] **Step 4: Makefile — hints aktualisieren**

In `Makefile` in der `hints`-Regel den Dashboard-Hinweis (Zeilen 47–50) ersetzen durch:
```makefile
	@echo "  $(YELLOW)Dashboard$(RESET) $(WHITE)— Dev: cd dashboard && npm run dev (Port 5173, Proxy → Backend)$(RESET)"
	@echo
	@printf "    $(BLUE)%-10s$(RESET) $(WHITE)%s$(RESET)\n" "Dashboard" "http://localhost:5173/"
	@printf "    $(BLUE)%-10s$(RESET) $(WHITE)%s$(RESET)\n" "Container" "http://localhost:$(PORT)/  (make up — Dashboard + API)"
	@echo
```

- [ ] **Step 5: Makefile verifizieren**

Run: `make help && make hints`
Expected: `##@ Docker`-Gruppe zeigt `up`, `down`, `docker-logs`, `build`, `push`; hints zeigt Dev-Dashboard (5173) und Container (8000).

- [ ] **Step 6: README Docker-/Deployment-Abschnitt aktualisieren**

Im `README.md` den Docker-Abschnitt so anpassen, dass er den Ein-Container-Aufbau beschreibt. Ersetze die Passage, die zwei Container / getrenntes Dashboard erwähnt, durch:
```markdown
### Docker (ein Container)

Backend **und** Dashboard laufen in einem Image auf einem Port:

```bash
make up        # baut & startet den Container → http://localhost:8000/
make down      # stoppt & entfernt ihn
```

Das Dashboard wird von FastAPI mit ausgeliefert (relative API-Aufrufe), es
ist kein separater Webserver nötig. Der Cache liegt im Volume `/data`.

**Image bauen/pushen** (Ökosystem-Konvention, versioniert via `gitDockerTag`):

```bash
make build                    # docker/build.sh --build
make push                     # docker/build.sh --push   (TARGET=ghcr, Default)
TARGET=dockerhub make push    # alternativ Docker Hub
```

**Unraid:** Container aus dem Image `mangolila/stockinfo` (bzw.
`ghcr.io/MikeMitterer/mangolila-stockinfo`), Port `8000:8000`, Pfad
`/mnt/user/appdata/stockinfo → /data`, `.env` als Env-Variablen.
```

(Falls der bestehende README-Docker-Abschnitt anders strukturiert ist: die zwei-Container-/`5173`-Erwähnungen entfernen und obigen Inhalt sinngemäß einsetzen.)

- [ ] **Step 7: Volle Verifikation + Commit**

Run:
```bash
.venv/bin/python -m pytest -q
cd dashboard && npm test && cd ..
docker compose config -q && echo "compose OK"
```
Expected: `75 passed`; `10 passed`; `compose OK`.

```bash
git add docker-compose.yml Makefile README.md
git commit -m "chore(docker): compose auf ein Image, Makefile build/push, README-Deployment"
```

---

## Self-Review

**1. Spec coverage:**
- Multi-Stage-Dockerfile (Backend serviert Dashboard) → Task 3 ✓
- StaticFiles-Mount konditional + `static_dir`-Setting → Task 1 ✓
- Relative API-URLs (`config.ts`) → Task 2 ✓
- Vite-Dev-Proxy (fünf Präfixe) → Task 2 ✓
- `.env`/`.env.example` bereinigen → Task 2 ✓
- Root-`.dockerignore` (dashboard-Artefakte) → Task 3 ✓
- Alte Dockerfiles entfernen → Task 3 ✓
- `docker/build.sh` aus Template, Platzhalter, samples, gitDockerTag → Task 4 ✓
- Git-Tag `v0.1.0` → Task 4 ✓
- docker-compose ein Service → Task 5 ✓
- Makefile build/push + hints → Task 5 ✓
- README-Deployment → Task 5 ✓
- Dev-Flow bleibt funktionsfähig → Task 1 (Backend), Task 2 (WebUI, verifiziert per curl über Proxy) ✓

**2. Placeholder scan:** Kein TBD/TODO; alle Codeblöcke vollständig; Verifikationsschritte mit erwarteten Ausgaben. `@@…@@` werden in Task 4 Step 3 explizit geprüft.

**3. Type consistency:** `mount_dashboard(app, static_dir) -> bool` in Task 1 definiert und dort verwendet; `Settings.static_dir` in Task 1 definiert, in Dockerfile (`STATIC_DIR`) und `get_settings().static_dir` konsistent. `API_BASE_URL`/`VITE_API_BASE_URL` und die fünf Proxy-Präfixe stimmen zwischen `config.ts`, `vite.config.ts` und den verifizierten Routen überein. Image-Name `mangolila/stockinfo` durchgängig.
