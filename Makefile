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

# Entwicklungs-Targets (setup, dev-*, test, check, up/down) laufen auch ohne
# die Bibliotheken unter .libs/. Maintainer-Targets (build, push, status,
# tag-*, version) brauchen die private BashLib und brechen sonst mit Hinweis ab.
DEV_MAKE ?= $(WORKSPACE)/.libs/MakeLib
-include ${DEV_MAKE}/colours.mk
-include ${DEV_MAKE}/tools.mk

# Fallbacks, wenn MakeLib nicht verfügbar ist
YELLOW ?= $(shell printf "\033[38;5;3m")
GREEN  ?= $(shell printf "\033[38;5;2m")
BLUE   ?= $(shell printf "\033[38;5;6m")
RED    ?= $(shell printf "\033[38;5;1m")
WHITE  ?= $(shell printf "\033[38;5;7m")
RESET  ?= $(shell printf "\033[0m")
THEME_COLOR_GROUP   ?= $(YELLOW)
THEME_COLOR_TARGET  ?= $(BLUE)
THEME_COLOR_DESC    ?= $(GREEN)
THEME_INDENT_GROUP  ?= $(shell printf '%2s' '')
THEME_INDENT_TARGET ?= $(shell printf '%7s' '')
THEME_COLOR_DANGER  ?= $(RED)

# Kennzeichnet in der Hilfe Targets, die die private BashLib brauchen. In der
# Target-Beschreibung steht dafür am Ende „— Maintainer“.
MAINTAINER_MARK = $(THEME_COLOR_DANGER)[Maintainer]$(THEME_COLOR_DESC)

# ProjectTools (geteilte Dev-Scripte) — Fallback für nicht-interaktive Shells (Jenkins etc.)
PROJECT_TOOLS ?= $(WORKSPACE)/.libs/ProjectTools/src
BASH_LIBS ?= $(WORKSPACE)/.libs/BashLib/src
export BASH_LIBS

# Prüft vor Maintainer-Targets, ob die private BashLib vorhanden ist.
# Optionaler Parameter: ein Hinweis, wie es ohne BashLib geht.
define require_bash_libs
	@test -r "$(BASH_LIBS)/version.lib.sh" || { \
		echo -e "  $(RED)✗$(RESET) Nur für Maintainer: benötigt die private BashLib ($(YELLOW)BASH_LIBS$(RESET))." >&2; \
		$(if $(1),echo -e "    $(1)" >&2;) \
		exit 1; }
endef

IMAGE_HINT = Image ohne BashLib bauen: $(GREEN)docker build -f docker/Dockerfile -t $(IMAGE_NAME):latest .$(RESET)
PYTHON ?= python3
# Interpreter, mit dem `make setup` die .venv anlegt (mindestens 3.11).
PYTHON_BOOTSTRAP ?= python3.11
export PROJECT_TOOLS

VENV    := .venv
PYTEST  := $(VENV)/bin/pytest

PORT    ?= 8000

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
	    /^[^#]/ { desc = $$2; sub(/ — Maintainer$$/, " $(MAINTAINER_MARK)", desc); \
	      printf "$(THEME_INDENT_TARGET)$(THEME_COLOR_TARGET)%-16s $(THEME_COLOR_DESC)%s$(RESET)\n", $$1, desc }'
	@echo

.PHONY: hints
hints: ## Nützliche URLs und Hinweise anzeigen
	@echo
	@echo "  $(YELLOW)Erster Start$(RESET) $(WHITE)— make setup → cp .env.example .env → make dev-up$(RESET)"
	@echo
	@echo "  $(YELLOW)Backend (make dev-up)$(RESET) $(WHITE)— im Browser http:// verwenden, nicht https$(RESET)"
	@echo
	@printf "    $(BLUE)%-10s$(RESET) $(WHITE)%s$(RESET)\n" "API"     "http://localhost:$(PORT)/"
	@printf "    $(BLUE)%-10s$(RESET) $(WHITE)%s$(RESET)\n" "Swagger" "http://localhost:$(PORT)/docs"
	@printf "    $(BLUE)%-10s$(RESET) $(WHITE)%s$(RESET)\n" "Health"  "http://localhost:$(PORT)/health"
	@echo
	@echo "  $(YELLOW)Dashboard$(RESET) $(WHITE)— make dev-up startet es mit (Port 5173, Proxy → Backend)$(RESET)"
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
	@if [[ -r "$(BASH_LIBS)/tools.lib.sh" ]]; then \
		./scripts/setup-libs.sh --install; \
	else \
		echo -e "  $(YELLOW)⚠$(RESET) BashLib nicht verfügbar — .libs-Verlinkung übersprungen (nur Maintainer-Targets brauchen sie)"; \
	fi
	@$(PYTHON_BOOTSTRAP) -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else "Python 3.11 oder neuer erforderlich")'
	@test -x $(VENV)/bin/python || $(PYTHON_BOOTSTRAP) -m venv $(VENV)
	@$(VENV)/bin/python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else "Bestehende .venv benötigt Python 3.11 oder neuer")'
	@$(VENV)/bin/python -m pip install -q -r requirements-dev.txt
	@if [[ -d .libs/ProjectTools ]]; then $(VENV)/bin/python -m pip install -q -r requirements-maintainer.txt; fi
	@npm ci --prefix dashboard --no-audit --no-fund

# ─── Entwicklung ──────────────────────────────────────────────────────────────

##@ Entwicklung

.PHONY: dev-up
dev-up: ## Gesamten Stack starten — Backend + Dashboard (overmind, Daemon)
	overmind start -D -N -f Procfile.dev
	@echo -e "  $(GREEN)✓$(RESET) Stack läuft — Backend $(BLUE)http://localhost:$(PORT)$(RESET) · Dashboard $(BLUE)http://localhost:5173$(RESET)  ($(WHITE)make dev-logs$(RESET))"

.PHONY: dev-down
dev-down: ## Gesamten Stack stoppen (overmind quit, dann Ports freigeben)
	-@overmind quit 2>/dev/null || true
	@# Raeumt nach einem Absturz overmind/tmux DIESES Projekts, eine verwaiste
	@# .overmind.sock und die Ports aus .dev-ports.conf.sh auf.
	@if [[ -r "$(PROJECT_TOOLS)/bash/dev-ports.sh" ]]; then \
		"$(PROJECT_TOOLS)/bash/dev-ports.sh" --kill; \
	else \
		echo -e "  $(YELLOW)⚠$(RESET) ProjectTools nicht verfügbar — Reste nach einem Absturz nicht geprüft"; \
	fi
	@echo -e "  $(GREEN)✓$(RESET) Stack gestoppt"

.PHONY: dev-logs
dev-logs: ## Logs des Stacks folgen (overmind echo)
	overmind echo

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
build: ## Docker-Image bauen und prüfen (PLATFORM=x86|arm, Default x86) — Maintainer
	$(call require_bash_libs,$(IMAGE_HINT))
	docker/build.sh --build $(PLATFORM)

.PHONY: push
push: ## Geprüftes Image pushen, danach docker/README.md bei Docker Hub (TARGET=ghcr|dockerhub|ecr) — Maintainer
	$(call require_bash_libs,$(IMAGE_HINT))
	docker/build.sh --push

# ─── Status ───────────────────────────────────────────────────────────────────

##@ Status

.PHONY: status
status: ## Git-Status aller Workspace-Repos anzeigen — Maintainer
	$(require_bash_libs)
	@bash $(PROJECT_TOOLS)/bash/repo-status.sh --show

# ─── Versionierung ────────────────────────────────────────────────────────────

##@ Versionierung

# Ohne `##`: nicht in der Hilfe, laeuft aber als Abhaengigkeit von tag-*.
.PHONY: precheck
precheck:
	$(require_bash_libs)

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
version: ## Aktuelle Version anzeigen (Versionsdatei + git tag) — Maintainer
	$(require_bash_libs)
	@echo
	@VER=$$(source "$${BASH_LIBS}/version.lib.sh" 2>/dev/null && readProjectVersion 2>/dev/null); \
	 [[ -z "$$VER" ]] && VER='nicht gesetzt'; \
	 TAG=$$(git describe --tags --abbrev=0 2>/dev/null || echo 'kein Tag'); \
	 echo "    $(YELLOW)version$(RESET)      = $(BLUE)$$VER$(RESET)"; \
	 echo "    $(YELLOW)git tag$(RESET)      = $(BLUE)$$TAG$(RESET)"
	@echo
