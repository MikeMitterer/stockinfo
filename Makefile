SHELL := /bin/bash

.DEFAULT_GOAL := help

WORKSPACE    := $(realpath $(shell pwd))
PROJECT_NAME := $(notdir $(WORKSPACE))

# .env nur für Make selbst (PORT, HOST, …) — bewusst **ohne** `export`.
# Ein pauschales `export` reicht die Werte 1:1 an jeden Kindprozess weiter,
# inklusive Trailing-Whitespace, den Make im Gegensatz zu python-dotenv nicht
# abschneidet ('false   ' ist für pydantic kein Boolean). Die App liest .env
# ohnehin selbst (pydantic-settings), Docker via --env-file.
-include .env

include ${DEV_MAKE}/colours.mk
include ${DEV_MAKE}/tools.mk

# ProjectTools (geteilte Dev-Scripte) — Fallback für nicht-interaktive Shells (Jenkins etc.)
PROJECT_TOOLS ?= $(WORKSPACE)/.libs/ProjectTools/src
PYTHON ?= python3
# Interpreter, mit dem `make setup` die .venv anlegt (mindestens 3.11).
PYTHON_BOOTSTRAP ?= python3.11
export PROJECT_TOOLS

VENV    := .venv
UVICORN := $(VENV)/bin/uvicorn
PYTEST  := $(VENV)/bin/pytest

APP_MODULE ?= app.main:app
HOST       ?= 0.0.0.0
PORT       ?= 8000
PID_FILE   := $(VENV)/uvicorn.pid
LOG_FILE   := uvicorn.log

# Docker (Image via docker/build.sh, Start via 'make up')
# Zielplattform des Images. Vorgabe x86, **nicht** die des Rechners: Der Server,
# auf dem das Image läuft, ist amd64 — ein ARM-Mac baute sonst still ein Image,
# das dort nicht startet, und der Fehler fiele erst beim Update auf.
# Überschreibbar: `make build PLATFORM=arm`. Mehrplattform-Builds würden
# vor der lokalen Image-Prüfung veröffentlichen und sind hier gesperrt.
PLATFORM    ?= x86
IMAGE_NAME  ?= mangolila/stockinfo
CONTAINER   ?= stockinfo
# sources-profile.sh --target docker verwendet denselben Standardnamen.
DATA_VOLUME ?= stockinfo-data

# ─── Hilfe ────────────────────────────────────────────────────────────────────

.PHONY: help
help: ## Alle verfügbaren Befehle anzeigen
	@echo
	@echo "Please use \`make <$(THEME_COLOR_GROUP)target$(RESET)>' where <target> is one of"
	@echo
	@echo "Project: $(THEME_COLOR_GROUP)$(PROJECT_NAME)$(RESET)"
	@echo
	@grep -hE '^(##@|[a-zA-Z0-9_-]+:.*?## )' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; \
	    /^##@/ { printf "\n$(THEME_INDENT_GROUP)$(THEME_COLOR_GROUP)%s$(RESET)\n", substr($$0, 4); next }; \
	    /^[^#]/ { printf "$(THEME_INDENT_TARGET)$(THEME_COLOR_TARGET)%-16s $(THEME_COLOR_DESC)%s$(RESET)\n", $$1, $$2 }'
	@echo

.PHONY: hints
hints: ## Nützliche URLs und Hinweise anzeigen
	@echo
	@echo "  $(YELLOW)Erster Start$(RESET) $(WHITE)— make setup → cp .env.example .env → make dev$(RESET)"
	@echo
	@echo "  $(YELLOW)Backend (make dev / make start)$(RESET) $(WHITE)— im Browser http:// verwenden, nicht https$(RESET)"
	@echo
	@printf "    $(BLUE)%-10s$(RESET) $(WHITE)%s$(RESET)\n" "API"     "http://localhost:$(PORT)/"
	@printf "    $(BLUE)%-10s$(RESET) $(WHITE)%s$(RESET)\n" "Swagger" "http://localhost:$(PORT)/docs"
	@printf "    $(BLUE)%-10s$(RESET) $(WHITE)%s$(RESET)\n" "Health"  "http://localhost:$(PORT)/health"
	@echo
	@echo "  $(YELLOW)Dashboard$(RESET) $(WHITE)— Dev: cd dashboard && npm run dev (Port 5173, Proxy → Backend)$(RESET)"
	@echo
	@printf "    $(BLUE)%-10s$(RESET) $(WHITE)%s$(RESET)\n" "Dashboard" "http://localhost:5173/"
	@printf "    $(BLUE)%-10s$(RESET) $(WHITE)%s$(RESET)\n" "Container" "http://localhost:$(PORT)/  (make up — Dashboard + API)"
	@printf "    $(BLUE)%-10s$(RESET) $(WHITE)%s$(RESET)\n" "Docker Hub" "https://hub.docker.com/r/mangolila/stockinfo"
	@echo
	@echo "  $(YELLOW)Beispiel$(RESET)"
	@echo
	@printf "    $(GREEN)%s$(RESET)\n" "curl http://localhost:$(PORT)/quote/IE00B4L5Y983"
	@echo
	@echo "  $(YELLOW)Unraid$(RESET) $(WHITE)— Template als User-Template installieren (auf dem Unraid ausführen)$(RESET)"
	@echo
	@printf "    $(GREEN)%s$(RESET)\n" "wget -O /boot/config/plugins/dockerMan/templates-user/my-stockinfo.xml https://raw.githubusercontent.com/MikeMitterer/unraid-templates/master/templates/stockinfo.xml"
	@echo

# ─── Setup ────────────────────────────────────────────────────────────────────

##@ Setup

# Idempotent: vorhandene Links und .venv bleiben, pip und npm gleichen nur ab.
.PHONY: setup
setup: ## .libs-Symlinks, Python-.venv und Dashboard-Pakete einrichten
	@./scripts/setup-libs.sh --install
	@$(PYTHON_BOOTSTRAP) -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else "Python 3.11 oder neuer erforderlich")'
	@test -x $(VENV)/bin/python || $(PYTHON_BOOTSTRAP) -m venv $(VENV)
	@$(VENV)/bin/python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else "Bestehende .venv benötigt Python 3.11 oder neuer")'
	@$(VENV)/bin/python -m pip install -q -r requirements-dev.txt
	@npm ci --prefix dashboard --no-audit --no-fund

# ─── Entwicklung ──────────────────────────────────────────────────────────────

##@ Entwicklung

.PHONY: dev-up
dev-up: ## Gesamten Stack starten — Backend + Dashboard (overmind, Daemon)
	overmind start -D -N -f Procfile.dev
	@echo -e "  $(GREEN)✓$(RESET) Stack läuft — Backend $(BLUE)http://localhost:$(PORT)$(RESET) · Dashboard $(BLUE)http://localhost:5173$(RESET)  ($(WHITE)make dev-logs$(RESET))"

.PHONY: dev-down
dev-down: ## Gesamten Stack stoppen (overmind quit)
	-@overmind quit 2>/dev/null || true
	-@pkill -f "overmind" 2>/dev/null || true
	-@rm -f $(CURDIR)/.overmind.sock
	@echo -e "  $(GREEN)✓$(RESET) Stack gestoppt"

.PHONY: dev-logs
dev-logs: ## Logs des Stacks folgen (overmind echo)
	overmind echo

.PHONY: dev
dev: ## Nur Backend im Vordergrund (uvicorn --reload)
	$(UVICORN) $(APP_MODULE) --host $(HOST) --port $(PORT) --reload

.PHONY: start
start: ## Server im Hintergrund starten
	@if [[ -f $(PID_FILE) ]] && kill -0 $$(cat $(PID_FILE)) 2>/dev/null; then \
		echo -e "  $(YELLOW)⚠$(RESET) Läuft bereits (PID $$(cat $(PID_FILE)))"; \
	else \
		nohup $(UVICORN) $(APP_MODULE) --host $(HOST) --port $(PORT) > $(LOG_FILE) 2>&1 & echo $$! > $(PID_FILE); \
		echo -e "  $(GREEN)✓$(RESET) Gestartet (PID $$(cat $(PID_FILE))) → http://$(HOST):$(PORT)"; \
	fi

.PHONY: stop
stop: ## Hintergrund-Server stoppen
	@if [[ -f $(PID_FILE) ]] && kill $$(cat $(PID_FILE)) 2>/dev/null; then \
		rm -f $(PID_FILE); echo -e "  $(GREEN)✓$(RESET) Gestoppt"; \
	else \
		rm -f $(PID_FILE); echo -e "  $(YELLOW)⚠$(RESET) Kein laufender Server"; \
	fi

.PHONY: logs
logs: ## Server-Logs folgen
	@tail -f $(LOG_FILE)

# ─── Tests ────────────────────────────────────────────────────────────────────

##@ Tests

.PHONY: test
test: test-backend test-plugin-api test-example test-dashboard ## Alle Tests — Backend + Plugin-API + Beispielpaket + Dashboard

# Wie `test`, aber ohne Netz: Die mit `integration` markierten Tests fragen
# echte Online-Anbieter und bleiben bei `test`. Dazu Ruff und die Typprüfung
# des Dashboards, die `test` nicht enthält.
.PHONY: check
check: test-plugin-api test-example test-dashboard ## Alle netzfreien Prüfungen — Backend ohne Online-Tests, Plugin-API, Beispiel, Dashboard, Ruff, Typen
	$(PYTEST) -q -m "not integration"
	$(VENV)/bin/ruff check app tests scripts
	cd dashboard && npx vue-tsc -b

.PHONY: test-backend
test-backend: ## Backend-Tests (pytest)  [ARGS="-k name"]
	$(PYTEST) -q $(ARGS)

# Eigener Lauf, nicht Teil von test-backend: `plugin_api/` ist ein
# eigenständiges Paket mit eigenem Import-Pfad. Ohne dieses Target prüft die
# reguläre Suite den öffentlichen Plugin-Vertrag überhaupt nicht.
.PHONY: test-plugin-api
test-plugin-api: ## Tests des Plugin-Vertrags (eigenes Paket)
	cd plugin_api && $(WORKSPACE)/$(PYTEST) -q

# Das Entwicklerbeispiel läuft mit, obwohl es nichts ausliefert. Ein Beispiel,
# das niemand ausführt, stimmt genau bis zur nächsten Vertragsänderung — und
# ein fremder Autor liest es als Vorlage, ohne zu ahnen, dass es veraltet ist.
#
# Über `PYTHONPATH` statt einer Installation: Das Paket ist absichtlich **nicht**
# Teil der Arbeitsumgebung, sonst prüfte der Lauf eine Version, die niemand
# gebaut hat.
.PHONY: test-example
test-example: ## Tests des Beispiel-Plugins (us-example)
	cd plugin_api/examples/us-example && \
		PYTHONPATH=src:$(WORKSPACE)/plugin_api/src $(WORKSPACE)/$(PYTEST) -q

.PHONY: lint-dashboard
lint-dashboard: ## Dashboard prüfen (ESLint und Foundation-Speicherregeln)
	npm --prefix dashboard run lint

.PHONY: test-dashboard
test-dashboard: lint-dashboard ## Dashboard prüfen und testen (ESLint + Vitest)
	npm --prefix dashboard test

# ─── Docker ───────────────────────────────────────────────────────────────────

##@ Docker

.PHONY: up
up: ## Container starten (Image aus 'make build'; Dashboard + API auf Port $(PORT))
	-@docker rm -f $(CONTAINER) 2>/dev/null || true
	docker run -d --name $(CONTAINER) \
		-p $(PORT):8000 \
		--env-file .env \
		-e HOST=0.0.0.0 -e PORT=8000 -e DATABASE_PATH=/data/stockinfo.db \
		-v $(DATA_VOLUME):/data \
		--restart unless-stopped \
		$(IMAGE_NAME):latest
	@echo -e "  $(GREEN)✓$(RESET) Läuft — App $(BLUE)http://localhost:$(PORT)/$(RESET)  ($(WHITE)zuvor: make build$(RESET))"

.PHONY: down
down: ## Container stoppen und entfernen
	-@docker rm -f $(CONTAINER) 2>/dev/null \
		&& echo -e "  $(GREEN)✓$(RESET) Gestoppt" \
		|| echo -e "  $(YELLOW)⚠$(RESET) Kein Container '$(CONTAINER)'"

.PHONY: docker-logs
docker-logs: ## Container-Logs folgen
	docker logs -f $(CONTAINER)

.PHONY: build
build: ## Docker-Image bauen und prüfen (PLATFORM=x86|arm, Default x86)
	docker/build.sh --build $(PLATFORM)

.PHONY: push
push: ## Geprüftes Image pushen, danach docker/README.md bei Docker Hub (TARGET=ghcr|dockerhub|ecr)
	docker/build.sh --push

# ─── Status ───────────────────────────────────────────────────────────────────

##@ Status

.PHONY: status
status: ## Git-Status aller Workspace-Repos anzeigen
	@bash $(PROJECT_TOOLS)/bash/repo-status.sh --show

# ─── Versionierung ────────────────────────────────────────────────────────────

##@ Versionierung

.PHONY: precheck
precheck:  ## Prüft die Versionierungsbibliothek
	@test -r "$${BASH_LIBS:-}/version.lib.sh" || { echo "BashLib fehlt: make setup ausführen." >&2; exit 1; }

.PHONY: changelog
changelog: ## CHANGELOG.md aus Release-Tags erstellen (ohne Commit)
	@LANGUAGE=en "$(PYTHON)" "$(PROJECT_TOOLS)/python/changelog.py" --generate

.PHONY: tag-major tag-minor tag-patch
tag-major: ## Version committen, taggen UND pushen — Major; danach Changelog [MSG="..."]
tag-minor: ## Version committen, taggen UND pushen — Minor; danach Changelog [MSG="..."]
tag-patch: ## Version committen, taggen UND pushen — Patch; danach Changelog [MSG="..."]

# Alle Stufen verwenden dieselbe Reihenfolge: Release, dann Changelog-Commit.
tag-major tag-minor tag-patch: precheck
	@test -r "$(PROJECT_TOOLS)/python/changelog.py"
	@test -z "$$(git status --porcelain)"
	@source "$${BASH_LIBS}/version.lib.sh" && semVerBump "$(patsubst tag-%,%,$@)" auto "" "$${MSG:-}"
	@LANGUAGE=en "$(PYTHON)" "$(PROJECT_TOOLS)/python/changelog.py" --publish

.PHONY: version
version: ## Aktuelle Version anzeigen (Versionsdatei + git tag)
	@echo
	@VER=$$(source "$${BASH_LIBS}/version.lib.sh" 2>/dev/null && readProjectVersion 2>/dev/null); \
	 [[ -z "$$VER" ]] && VER='nicht gesetzt'; \
	 TAG=$$(git describe --tags --abbrev=0 2>/dev/null || echo 'kein Tag'); \
	 echo "    $(YELLOW)version$(RESET)      = $(BLUE)$$VER$(RESET)"; \
	 echo "    $(YELLOW)git tag$(RESET)      = $(BLUE)$$TAG$(RESET)"
	@echo
