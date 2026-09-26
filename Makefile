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
	@echo
	@echo "  $(YELLOW)Beispiel$(RESET)"
	@echo
	@printf "    $(GREEN)%s$(RESET)\n" "curl http://localhost:$(PORT)/quote/IE00B4L5Y983"
	@echo
	@echo "  $(YELLOW)Unraid$(RESET) $(WHITE)— Template als User-Template installieren (auf dem Unraid ausführen)$(RESET)"
	@echo
	@printf "    $(GREEN)%s$(RESET)\n" "wget -O /boot/config/plugins/dockerMan/templates-user/my-stockinfo.xml https://raw.githubusercontent.com/MikeMitterer/unraid-templates/master/templates/stockinfo.xml"
	@echo

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
push: ## Geprüftes Image pushen, danach README bei Docker Hub (TARGET=ghcr|dockerhub|ecr)
	docker/build.sh --push

# ─── Status ───────────────────────────────────────────────────────────────────

##@ Status

.PHONY: status
status: ## Git-Status aller Workspace-Repos anzeigen
	@bash $(PROJECT_TOOLS)/bash/repo-status.sh --show

# ─── Versionierung ────────────────────────────────────────────────────────────

##@ Versionierung

.PHONY: precheck
precheck:  ## Prüft, ob BASH_LIBS gesetzt ist
	@if [[ -z "$${BASH_LIBS+x}" ]]; then \
		echo "$(RED)Achtung: '$(YELLOW)BASH_LIBS$(RED)' ist nicht gesetzt!$(RESET)"; \
		exit 1; \
	fi

.PHONY: tag-major
tag-major: precheck ## Version hochzählen — Major (X.y.z → X+1.0.0)  [MSG="..."]
	source "$${BASH_LIBS}/version.lib.sh" && semVerBump major auto "" "$${MSG:-}"

.PHONY: tag-minor
tag-minor: precheck ## Version hochzählen — Minor (x.Y.z → x.Y+1.0)  [MSG="..."]
	source "$${BASH_LIBS}/version.lib.sh" && semVerBump minor auto "" "$${MSG:-}"

.PHONY: tag-patch
tag-patch: precheck ## Version hochzählen — Patch (x.y.Z → x.y.Z+1)  [MSG="..."]
	source "$${BASH_LIBS}/version.lib.sh" && semVerBump patch auto "" "$${MSG:-}"

.PHONY: version
version: ## Aktuelle Version anzeigen (Versionsdatei + git tag)
	@echo
	@VER=$$(source "$${BASH_LIBS}/version.lib.sh" 2>/dev/null && readProjectVersion 2>/dev/null); \
	 [[ -z "$$VER" ]] && VER='nicht gesetzt'; \
	 TAG=$$(git describe --tags --abbrev=0 2>/dev/null || echo 'kein Tag'); \
	 echo "    $(YELLOW)version$(RESET)      = $(BLUE)$$VER$(RESET)"; \
	 echo "    $(YELLOW)git tag$(RESET)      = $(BLUE)$$TAG$(RESET)"
	@echo
