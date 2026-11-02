SHELL := bash

.DEFAULT_GOAL := help

WORKSPACE    := $(CURDIR)
WORKSPACE_SQ := '$(subst ','\'',$(WORKSPACE))'
PROJECT_NAME := $(shell basename -- $(WORKSPACE_SQ))
# Werte von außen (Pfad, Umgebung) nur über die Umgebung in Rezepte geben, nie als $(VAR).
export WORKSPACE WORKSPACE_SQ PROJECT_NAME

# .env nur für Make selbst (PORT, HOST, …) — bewusst **ohne** `export`.
# Ein pauschales `export` reicht die Werte 1:1 an jeden Kindprozess weiter,
# inklusive Trailing-Whitespace, den Make im Gegensatz zu python-dotenv nicht
# abschneidet ('false   ' ist für pydantic kein Boolean). Die App liest .env
# ohnehin selbst (pydantic-settings), Docker via --env-file.
-include .env

# Entwicklungs-Targets (setup, dev-*, up/down) laufen ohne die Entwicklungswerkzeuge.
# Prüf-Targets (test, check, docs-check, status, changelog) brauchen ProjectTools,
# Maintainer-Targets (build, push, tag-*, version) BashLib; beide kommen über pipx.
#
# Tag und Quelle (Git oder Arbeitskopie) beider Werkzeuge stehen nur in .dev-tools.conf.sh;
# devtools (Paket mmit-devtools) liest sie, prüft, zeigt und installiert. pipx run holt
# devtools am Tag aus DEVTOOLS_TAG und hält die Umgebung zwischen den Aufrufen; der Tag
# geht über die Umgebung in die Befehle, nicht als Text.
include .dev-tools.conf.sh
export DEVTOOLS_SPEC := $(DEVTOOLS_SOURCE)@$(DEVTOOLS_TAG)
DEV_TOOLS = pipx run --spec "$$DEVTOOLS_SPEC" devtools

# BashLib für version, tag-*, docker/build.sh und scripts/. Ein von außen gesetztes
# BASH_LIBS geht vor, sonst bashlib-path aus der pipx-Installation; bei pipx install -e
# <Arbeitskopie> zeigt es auf deren src/.
BASHLIB_MIN := $(patsubst v%,%,$(firstword $(subst +, ,$(BASHLIB_TAG))))
ifndef BASH_LIBS
BASH_LIBS := $(shell bashlib-path 2>/dev/null)
BASHLIB_FROM_PIPX := $(if $(BASH_LIBS),yes)
endif
export BASH_LIBS

# Farben und Spalten der Hilfe, wie in agent-lessons ohne MakeLib. Von außen überschreibbar.
YELLOW ?= $(shell printf "\033[38;5;11m")
GREEN  ?= $(shell printf "\033[38;5;10m")
BLUE   ?= $(shell printf "\033[38;5;33m")
RED    ?= $(shell printf "\033[38;5;196m")
WHITE  ?= $(shell printf "\033[38;5;15m")
RESET  ?= $(shell printf "\033[0m")
THEME_COLOR_GROUP   ?= $(YELLOW)
THEME_COLOR_TARGET  ?= $(BLUE)
THEME_COLOR_DESC    ?= $(GREEN)
THEME_COLOR_DANGER  ?= $(RED)
THEME_INDENT_GROUP  ?= $(shell printf '%2s' '')
THEME_INDENT_TARGET ?= $(shell printf '%7s' '')
THEME_WIDTH_TARGET  ?= 22
THEME_COLUMN_GAP    ?= 1

# Kennzeichnet in der Hilfe Targets, die BashLib brauchen. In der
# Target-Beschreibung steht dafür am Ende „— Maintainer“.
MAINTAINER_MARK = $(THEME_COLOR_DANGER)[Maintainer]$(THEME_COLOR_DESC)

# Prüft vor Maintainer-Targets, ob BashLib vorhanden ist.
# Optionaler Parameter: ein Hinweis, wie es ohne BashLib geht.
define require_bash_libs
	@test -r "$${BASH_LIBS}/version.lib.sh" || { \
		echo -e "  $(RED)✗$(RESET) Nur für Maintainer: benötigt BashLib ab $(BASHLIB_MIN): $(YELLOW)make install-tools$(RESET)" >&2; \
		$(if $(1),echo -e "    $(1)" >&2;) \
		exit 1; }
endef

IMAGE_HINT = Image ohne BashLib bauen: $(GREEN)docker build -f docker/Dockerfile -t $(IMAGE_NAME):latest .$(RESET)
# Interpreter, mit dem `make setup` die .venv anlegt (mindestens 3.11).
PYTHON_BOOTSTRAP ?= python3.11

VENV    := .venv
PYTEST  := $(VENV)/bin/pytest
# Was setup herstellt und require-setup prüft: Python-Pakete in der .venv und die
# Dashboard-Pakete. Eine geänderte Abhängigkeitsdatei macht den Stempel veraltet.
SETUP_STAMPS := $(VENV)/.installed dashboard/node_modules/.installed

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

# Liste der Makefiles unausgewertet über die Umgebung (siehe Kopf).
export HELP_FILES = $(value MAKEFILE_LIST)

.PHONY: help
help: ## Alle verfügbaren Befehle anzeigen
	@echo
	@echo "Please use \`make <$(THEME_COLOR_GROUP)target$(RESET)>' where <target> is one of"
	@echo
	@echo "Project: $(THEME_COLOR_GROUP)$${PROJECT_NAME}$(RESET)"
	@echo
	@grep -hE '^(##@|[a-zA-Z0-9_-]+:.*?## )' $${HELP_FILES} | \
	  awk 'BEGIN {FS = ":.*?## "}; \
	    /^##@/ { printf "\n$(THEME_INDENT_GROUP)$(THEME_COLOR_GROUP)%s$(RESET)\n", substr($$0, 4); next }; \
	    /^[^#]/ { desc = $$2; sub(/ — Maintainer$$/, " $(MAINTAINER_MARK)", desc); \
	      printf "$(THEME_INDENT_TARGET)$(THEME_COLOR_TARGET)%-$(THEME_WIDTH_TARGET)s%$(THEME_COLUMN_GAP)s$(THEME_COLOR_DESC)%s$(RESET)\n", $$1, "", desc }'
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
	@echo "  $(YELLOW)Werkzeuge$(RESET) $(WHITE)— Tag und Quelle in .dev-tools.conf.sh, einrichten mit make install-tools$(RESET)"
	@echo
	@cmd=$$($(DEV_TOOLS) command projecttools 2>/dev/null) || cmd="nicht abrufbar (pipx run devtools)"; \
	 printf "    $(BLUE)%-22s$(RESET) $(WHITE)%s$(RESET)\n" "ProjectTools" "$$cmd"
	@cmd=$$($(DEV_TOOLS) command bashlib 2>/dev/null) || cmd="nicht abrufbar (pipx run devtools)"; \
	 printf "    $(BLUE)%-22s$(RESET) $(WHITE)%s$(RESET)\n" "BashLib (Maintainer)" "$$cmd"
	@echo

# Läuft vor den Maintainer-Zielen; ohne Hilfeeintrag. Verlangt BashLib in Mindestversion und
# nennt sonst den Installationsbefehl. Ein von außen gesetztes BASH_LIBS prüft es nur auf Lesbarkeit.
.PHONY: precheck
precheck:
	$(require_bash_libs)
	@if [[ -n '$(BASHLIB_FROM_PIPX)' ]]; then $(DEV_TOOLS) check bashlib; fi

# Ohne Hilfeeintrag: verlangt ProjectTools in Mindestversion und nennt sonst den Installationsbefehl.
.PHONY: require-tools
require-tools:
	@$(DEV_TOOLS) check projecttools

# ─── Setup ────────────────────────────────────────────────────────────────────

##@ Setup

# setup ist der einzige Weg, das Projekt einzurichten, auch als worktree_setup in Workspaces
# und im Prüf-Worktree. Prüf-Targets richten nichts selbst ein, sie hängen an require-setup.
# Wiederholbar: Die Stempel machen einen eingerichteten Stand zum Nulllauf.
.PHONY: setup
setup: ## Git-Hooks, Python-.venv und Dashboard-Pakete einrichten; zeigt den Werkzeugstand
	@git config core.hooksPath .githooks
	@$(MAKE) -s --no-print-directory $(SETUP_STAMPS)
	@# Nur anzeigen: Ohne pipx oder Netz scheitert die Einrichtung daran nicht.
	@$(DEV_TOOLS) status 2>/dev/null || echo -e "  $(YELLOW)⚠$(RESET) Werkzeugstand nicht abrufbar (pipx run devtools); Prüf-Targets brauchen ProjectTools: $(YELLOW)make install-tools$(RESET)"

.PHONY: install-tools
install-tools: ## ProjectTools und BashLib auf den Stand aus .dev-tools.conf.sh bringen (pipx)
	@command -v pipx >/dev/null || { echo -e "  $(RED)✗$(RESET) pipx fehlt; etwa mit $(YELLOW)brew install pipx$(RESET) installieren." >&2; exit 1; }
	@$(DEV_TOOLS) install

# Stempelregeln: nur setup erreicht sie; neu, sobald eine Abhängigkeitsdatei neuer ist.
$(VENV)/.installed: requirements.txt requirements-dev.txt
	@$(PYTHON_BOOTSTRAP) -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else "Python 3.11 oder neuer erforderlich")'
	@test -x $(VENV)/bin/python || $(PYTHON_BOOTSTRAP) -m venv $(VENV)
	@$(VENV)/bin/python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else "Bestehende .venv benötigt Python 3.11 oder neuer")'
	@$(VENV)/bin/python -m pip install -q -r requirements-dev.txt
	@# Git-gepinnte Pakete behalten bei einem neuen Commit oft ihre Version;
	@# pip hält den alten Stand dann für erfüllt. Weicht der installierte Stand
	@# vom Pin ab, wird genau dieses Paket neu installiert.
	@grep -E '^[A-Za-z0-9_.-]+ @ git\+' requirements.txt | while read -r PIN; do \
		$(VENV)/bin/python -m pip freeze | grep -qxF "$$PIN" || \
			$(VENV)/bin/python -m pip install -q --no-deps --force-reinstall "$$PIN"; \
	done
	@touch "$@"

dashboard/node_modules/.installed: dashboard/package-lock.json
	@npm ci --prefix dashboard --no-audit --no-fund
	@touch "$@"

# Ohne Hilfeeintrag: meldet eine fehlende oder veraltete Einrichtung, statt sie nachzuholen.
.PHONY: require-setup
require-setup:
	@$(MAKE) --no-print-directory -q $(SETUP_STAMPS) || { \
		echo -e "  $(RED)✗$(RESET) Nicht eingerichtet oder veraltet: $(YELLOW)make setup$(RESET)" >&2; \
		exit 1; }

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
	@# .overmind.sock und die Ports aus .dev-ports.conf.sh auf. dev-ports hat im
	@# pipx-Paket noch keinen Befehl (ProjectTools T-16); bis dahin aus PROJECT_TOOLS.
	@if [[ -r "$${PROJECT_TOOLS:-}/bash/dev-ports.sh" ]]; then \
		"$${PROJECT_TOOLS}/bash/dev-ports.sh" --kill; \
	else \
		echo -e "  $(YELLOW)⚠$(RESET) PROJECT_TOOLS nicht gesetzt — Reste nach einem Absturz nicht geprüft"; \
	fi
	@echo -e "  $(GREEN)✓$(RESET) Stack gestoppt"

.PHONY: dev-logs
dev-logs: ## Logs des Stacks folgen (overmind echo)
	overmind echo

# ─── Tests ────────────────────────────────────────────────────────────────────

##@ Tests

.PHONY: test
test: docs-check test-backend test-plugin-api test-example test-dashboard ## Alle Tests — Doku, Backend, Plugin-API, Beispielpaket, Dashboard

# Wie `test`, aber ohne Netz: Die mit `integration` markierten Tests fragen
# echte Online-Anbieter und bleiben bei `test`. Dazu Ruff und die Typprüfung
# des Dashboards, die `test` nicht enthält.
.PHONY: check
check: docs-check test-plugin-api test-example test-dashboard ## Alle netzfreien Prüfungen — Doku, Backend ohne Online-Tests, Plugin-API, Beispiel, Dashboard, Ruff, Typen
	$(PYTEST) -q -m "not integration"
	$(VENV)/bin/ruff check app tests scripts
	cd dashboard && npx vue-tsc -b

.PHONY: test-backend
test-backend: require-setup ## Backend-Tests (pytest)  [ARGS="-k name"]
	$(PYTEST) -q $(ARGS)

# Eigener Lauf, nicht Teil von test-backend: `plugin_api/` ist ein
# eigenständiges Paket mit eigenem Import-Pfad. Ohne dieses Target prüft die
# reguläre Suite den öffentlichen Plugin-Vertrag überhaupt nicht.
.PHONY: test-plugin-api
test-plugin-api: require-setup ## Tests des Plugin-Vertrags (eigenes Paket)
	cd plugin_api && "$${WORKSPACE}"/$(PYTEST) -q

# Das Entwicklerbeispiel läuft mit, obwohl es nichts ausliefert. Ein Beispiel,
# das niemand ausführt, stimmt genau bis zur nächsten Vertragsänderung — und
# ein fremder Autor liest es als Vorlage, ohne zu ahnen, dass es veraltet ist.
#
# Über `PYTHONPATH` statt einer Installation: Das Paket ist absichtlich **nicht**
# Teil der Arbeitsumgebung, sonst prüfte der Lauf eine Version, die niemand
# gebaut hat.
.PHONY: test-example
test-example: require-setup ## Tests des Beispiel-Plugins (us-example)
	cd plugin_api/examples/us-example && \
		PYTHONPATH="src:$${WORKSPACE}/plugin_api/src" "$${WORKSPACE}"/$(PYTEST) -q

.PHONY: lint-dashboard
lint-dashboard: require-setup ## Dashboard prüfen (ESLint und Foundation-Speicherregeln)
	npm --prefix dashboard run lint

.PHONY: test-dashboard
test-dashboard: lint-dashboard ## Dashboard prüfen und testen (ESLint + Vitest)
	npm --prefix dashboard test

# Teil von test und check: Ohne ProjectTools scheitert es laut, statt die Doku still zu
# überspringen. Regeln in .docs-check.conf.sh.
.PHONY: docs-check
docs-check: require-tools ## Nutzerdoku gegen das Projekt prüfen (Links, Befehle, Variablen, Abhängigkeiten)
	@docs-check --run

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
status: require-tools ## Git-Status aller Workspace-Repos anzeigen
	@repo-status --show

# ─── Versionierung ────────────────────────────────────────────────────────────

##@ Versionierung

.PHONY: changelog
changelog: require-tools ## CHANGELOG.md aus Release-Tags erstellen (ohne Commit)
	@LANGUAGE=en changelog --generate

.PHONY: tag-major tag-minor tag-patch
tag-major: ## Version committen, taggen UND pushen — Major; danach Changelog [MSG="..."]
tag-minor: ## Version committen, taggen UND pushen — Minor; danach Changelog [MSG="..."]
tag-patch: ## Version committen, taggen UND pushen — Patch; danach Changelog [MSG="..."]

# Alle Stufen verwenden dieselbe Reihenfolge: Release, dann Changelog-Commit.
tag-major tag-minor tag-patch: require-tools precheck
	@test -z "$$(git status --porcelain)"
	@source "$${BASH_LIBS}/version.lib.sh" && semVerBump "$(patsubst tag-%,%,$@)" auto "" "$${MSG:-}"
	@LANGUAGE=en changelog --publish

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
