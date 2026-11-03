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

# Interpreter, mit dem `make setup` die .venv anlegt (mindestens 3.11).
PYTHON_BOOTSTRAP ?= python3.11

VENV    := .venv
PYTEST  := $(VENV)/bin/pytest
# Was setup herstellt und require-setup prüft: Python-Pakete in der .venv und die
# Dashboard-Pakete. Eine geänderte Abhängigkeitsdatei macht den Stempel veraltet.
SETUP_STAMPS := $(VENV)/.installed dashboard/node_modules/.installed

# Ports des Dev-Stacks aus .dev-ports.conf.sh, dieselbe Quelle wie dev-ports.sh. Nur
# Ziffern werden übernommen; die Werte stehen danach als Zahlen in den Rezepten.
DEV_PORTS      := $(shell bash -c 'source ./.dev-ports.conf.sh && printf "%s %s" "$$DASHBOARD_PORT" "$$BACKEND_PORT"' 2>/dev/null | grep -xE '[0-9]+ [0-9]+')
DASHBOARD_PORT := $(word 1,$(DEV_PORTS))
BACKEND_PORT   := $(word 2,$(DEV_PORTS))

# Host-Port des Containers bei `make up`, aus .env oder der Umgebung.
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

# Diese Werte kommen von außen (.env, Umgebung, Kommandozeile). Rezepte lesen sie als
# "$${NAME}" aus der Umgebung, nie als $(NAME) im Shell-Text. strip entfernt den
# Trailing-Whitespace, den -include .env mitbringt.
PORT        := $(strip $(PORT))
PLATFORM    := $(strip $(PLATFORM))
IMAGE_NAME  := $(strip $(IMAGE_NAME))
CONTAINER   := $(strip $(CONTAINER))
DATA_VOLUME := $(strip $(DATA_VOLUME))
export PORT PLATFORM IMAGE_NAME CONTAINER DATA_VOLUME

IMAGE_HINT = Image ohne BashLib bauen: $(GREEN)docker build -f docker/Dockerfile -t $${IMAGE_NAME}:latest .$(RESET)

# Repo-Adresse aus git remote origin (SSH oder HTTPS) als https-URL; leer ohne Remote.
# Werte von außen landen im Rezept; Ref-Namen dürfen $, ( und ) enthalten. Nur
# erlaubte Zeichen übernehmen, sonst leer – ein Tag wie v1$(touch x) liefe sonst.
REPO_URL    := $(shell git remote get-url origin 2>/dev/null | sed -E 's|^git@([^:]+):|https://\1/|; s|\.git$$||' | grep -xE '[A-Za-z0-9._:/@+~-]+')
RELEASE_TAG := $(or $(shell git describe --tags --abbrev=0 2>/dev/null | grep -xE '[A-Za-z0-9._+-]+'),noch kein Release)
NO_REMOTE   := kein Remote origin (git remote add origin …)

# ─── Hilfe ────────────────────────────────────────────────────────────────────

# Liste der Makefiles unausgewertet über die Umgebung (siehe Kopf).
export HELP_FILES = $(value MAKEFILE_LIST)

# Platzhalter {major}, {minor} und {patch} der Hilfe: „<jetzt> → <danach>“ aus der
# Version, die help mit readProjectVersion liest; gerechnet wie semVerBump.
HELP_VALUES += if (ver ~ /^[0-9]+\.[0-9]+\.[0-9]+$$/ && split(ver, v, ".") == 3) { \
	  value["major"] = ver " → " (v[1] + 1) ".0.0"; \
	  value["minor"] = ver " → " v[1] "." (v[2] + 1) ".0"; \
	  value["patch"] = ver " → " v[1] "." v[2] "." (v[3] + 1) } \
	else { value["major"] = value["minor"] = value["patch"] = "(Version unbekannt: make version)" };

.PHONY: help
help: ## Alle verfügbaren Befehle anzeigen
	@echo
	@echo "Please use \`make <$(THEME_COLOR_GROUP)target$(RESET)>' where <target> is one of"
	@echo
	@echo "Project: $(THEME_COLOR_GROUP)$${PROJECT_NAME}$(RESET)"
	@echo
	@set -o pipefail; \
	 VER=$$(source "$${BASH_LIBS}/version.lib.sh" 2>/dev/null && readProjectVersion 2>/dev/null); \
	 grep -hE '^(##@|[a-zA-Z0-9_-]+:.*?## )' $${HELP_FILES} | \
	  awk -v ver="$$VER" 'BEGIN {FS = ":.*?## "; $(HELP_VALUES)}; \
	    /^##@/ { printf "\n$(THEME_INDENT_GROUP)$(THEME_COLOR_GROUP)%s$(RESET)\n", substr($$0, 4); next }; \
	    /^[^#]/ { desc = $$2; sub(/ — Maintainer$$/, " $(MAINTAINER_MARK)", desc); \
	      for (k in value) gsub("\\{" k "\\}", value[k], desc); \
	      printf "$(THEME_INDENT_TARGET)$(THEME_COLOR_TARGET)%-$(THEME_WIDTH_TARGET)s%$(THEME_COLUMN_GAP)s$(THEME_COLOR_DESC)%s$(RESET)\n", $$1, "", desc }'
	@echo

.PHONY: info
info: ## Projektpfade, Ports und Werkzeugstand anzeigen
	@echo
	@printf '    $(YELLOW)%-16s$(RESET) = $(BLUE)%s$(RESET)\n' \
		'WORKSPACE' "$${WORKSPACE}" \
		'VENV' '$(VENV)' \
		'BASH_LIBS' "$${BASH_LIBS:-nicht gesetzt}" \
		'PROJECT_TOOLS' "$${PROJECT_TOOLS:-nicht gesetzt}" \
		'Dev-Ports' '$(DASHBOARD_PORT) (Dashboard) · $(BACKEND_PORT) (Backend)' \
		'PORT (make up)' "$${PORT}"
	@echo
	@echo "$(THEME_INDENT_GROUP)$(THEME_COLOR_GROUP)Werkzeuge (.dev-tools.conf.sh)$(RESET)"
	@# devtools rückt um zwei Zeichen ein; zwei mehr stellen die Zeilen unter die Variablen.
	@set -o pipefail; $(DEV_TOOLS) status | sed 's/^/  /'
	@echo

# Eine Zeile für hints: Beschriftung auf THEME_WIDTH_TARGET Zeichen aufgefüllt, dann der Wert.
# printf füllt nach Bytes auf; gezählt werden deshalb Zeichen (UTF-8-Folgebytes nicht).
# Aufruf: $(call hint_row,Beschriftung,Wert), ohne Komma in den Werten.
hint_row = LABEL="$(1)"; \
	CHARS=$$(printf '%s' "$$LABEL" | LC_ALL=C tr -d '\200-\277' | wc -c); \
	printf "$(THEME_INDENT_TARGET)$(THEME_COLOR_TARGET)%s$(RESET)%*s$(THEME_COLOR_DESC)%s$(RESET)\n" \
		"$$LABEL" $$(( $(THEME_WIDTH_TARGET) - CHARS + $(THEME_COLUMN_GAP) )) "" "$(2)"

# Links, URLs und Tipps für den Alltag; das Einrichten beschreibt docs/development.md.
.PHONY: hints
hints: ## Links, URLs und Tipps für die tägliche Arbeit
	@echo
	@echo "$(THEME_INDENT_GROUP)$(THEME_COLOR_GROUP)Links$(RESET)"
	@$(call hint_row,Repository,$(or $(REPO_URL),$(NO_REMOTE)))
	@$(call hint_row,Entwicklerdoku,$(if $(REPO_URL),$(REPO_URL)/blob/master/docs/development.md,docs/development.md))
	@$(call hint_row,Letzter Release,$(RELEASE_TAG))
	@$(call hint_row,Docker Hub,https://hub.docker.com/r/$${IMAGE_NAME})
	@echo
	@echo "$(THEME_INDENT_GROUP)$(THEME_COLOR_GROUP)URLs nach make dev-up (http://, nicht https)$(RESET)"
	@$(call hint_row,Dashboard,http://localhost:$(DASHBOARD_PORT)/)
	@$(call hint_row,API,http://localhost:$(BACKEND_PORT)/)
	@$(call hint_row,Swagger,http://localhost:$(BACKEND_PORT)/docs)
	@$(call hint_row,Health,http://localhost:$(BACKEND_PORT)/health)
	@$(call hint_row,Container (make up),http://localhost:$${PORT}/)
	@echo
	@echo "$(THEME_INDENT_GROUP)$(THEME_COLOR_GROUP)Im Alltag$(RESET)"
	@$(call hint_row,Vor dem Commit,make check)
	@$(call hint_row,Einzelne Tests,make test-backend ARGS='-k name')
	@$(call hint_row,Stack hängt,make dev-down; dann make dev-up)
	@$(call hint_row,Erster Kurs,curl http://localhost:$(BACKEND_PORT)/quote/IE00B4L5Y983)
	@$(call hint_row,Unraid-Test,wget -O /boot/config/plugins/dockerMan/templates-user/stockinfo-test.xml https://raw.githubusercontent.com/MikeMitterer/unraid-templates/master/templates/stockinfo.xml)
	@echo
	@echo "$(THEME_INDENT_GROUP)$(THEME_COLOR_GROUP)Werkzeuge (Tag und Quelle in .dev-tools.conf.sh)$(RESET)"
	@CMD=$$($(DEV_TOOLS) command projecttools 2>/dev/null) || CMD="nicht abrufbar: make info"; $(call hint_row,ProjectTools,$$CMD)
	@CMD=$$($(DEV_TOOLS) command bashlib 2>/dev/null) || CMD="nicht abrufbar: make info"; $(call hint_row,BashLib (Maintainer),$$CMD)
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

# ─── Status ───────────────────────────────────────────────────────────────────

##@ Status

.PHONY: status
status: require-tools ## Git-Status aller Workspace-Repos anzeigen
	@repo-status --show

# ─── Entwicklung ──────────────────────────────────────────────────────────────

##@ Entwicklung

.PHONY: dev-up
dev-up: ## Backend und Dashboard laufen im Hintergrund, mit Auto-Reload
	overmind start -D -N -f Procfile.dev
	@echo -e "  $(GREEN)✓$(RESET) Stack läuft — Backend $(BLUE)http://localhost:$(BACKEND_PORT)$(RESET) · Dashboard $(BLUE)http://localhost:$(DASHBOARD_PORT)$(RESET)  ($(WHITE)make dev-logs$(RESET))"

.PHONY: dev-down
dev-down: ## Dev-Stack gestoppt, Reste nach einem Absturz beseitigt, Ports frei
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
dev-logs: ## Logs des Dev-Stacks live verfolgen
	overmind echo

# ─── Tests ────────────────────────────────────────────────────────────────────

##@ Tests

.PHONY: test
test: docs-check test-backend test-plugin-api test-example test-dashboard ## Alle Tests — Doku, Backend, Plugin-API, Beispielpaket, Dashboard

# Teil von test und check: Ohne ProjectTools scheitert es laut, statt die Doku still zu
# überspringen. Regeln in .docs-check.conf.sh.
.PHONY: docs-check
docs-check: require-tools ## Nutzerdoku gegen das Projekt prüfen (Links, Befehle, Variablen, Abhängigkeiten)
	@docs-check --run

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

# ─── Docker ───────────────────────────────────────────────────────────────────

##@ Docker

.PHONY: up
up: ## Container läuft mit Dashboard und API auf dem Port aus PORT (Image aus make build)
	-@docker rm -f "$${CONTAINER}" 2>/dev/null || true
	docker run -d --name "$${CONTAINER}" \
		-p "$${PORT}":8000 \
		--env-file .env \
		-e HOST=0.0.0.0 -e PORT=8000 -e DATABASE_PATH=/data/stockinfo.db \
		-v "$${DATA_VOLUME}":/data \
		--restart unless-stopped \
		"$${IMAGE_NAME}":latest
	@echo -e "  $(GREEN)✓$(RESET) Läuft — App $(BLUE)http://localhost:$${PORT}/$(RESET)  ($(WHITE)zuvor: make build$(RESET))"

.PHONY: down
down: ## Container gestoppt und entfernt
	-@docker rm -f "$${CONTAINER}" 2>/dev/null \
		&& echo -e "  $(GREEN)✓$(RESET) Gestoppt" \
		|| echo -e "  $(YELLOW)⚠$(RESET) Kein Container '$${CONTAINER}'"

.PHONY: docker-logs
docker-logs: ## Container-Logs live verfolgen
	docker logs -f "$${CONTAINER}"

.PHONY: build
build: ## Geprüftes Image für PLATFORM=x86|arm (Vorgabe x86) — Maintainer
	$(call require_bash_libs,$(IMAGE_HINT))
	docker/build.sh --build "$${PLATFORM}"

.PHONY: push
push: ## Geprüftes Image und docker/README.md veröffentlicht (TARGET=ghcr|dockerhub|ecr) — Maintainer
	$(call require_bash_libs,$(IMAGE_HINT))
	docker/build.sh --push

# ─── Versionierung ────────────────────────────────────────────────────────────

##@ Versionierung

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

.PHONY: tags
tags: ## Letzte 10 Tags mit Message anzeigen
	@echo
	@git tag --sort=-version:refname -n1 | head -10 | \
	  awk '{printf "    $(BLUE)%-28s$(RESET) $(GREEN)%s$(RESET)\n", $$1, substr($$0, index($$0,$$2))}'
	@echo

# Der Changelog ist englisch wie die übrige Doku; LANGUAGE=en gilt auch auf deutschem Locale.
CHANGELOG_GENERATE := LANGUAGE=en changelog --generate

.PHONY: changelog
changelog: require-tools ## CHANGELOG.md aus Release-Tags erstellen (ohne Commit)
	@$(CHANGELOG_GENERATE)

# $(call release,major|minor|patch): bumpen, taggen und CHANGELOG.md committen, alles
# nur lokal; veröffentlicht wird mit git push --follow-tags. changelog --publish pusht
# selbst, darum --generate und ein eigener Commit (bis ProjectTools T-20).
define release
	@test -z "$$(git status --porcelain)" || { \
		echo -e "  $(RED)✗$(RESET) Release abgebrochen: Arbeitsbaum nicht sauber (git status)" >&2; exit 1; }
	@source "$${BASH_LIBS}/version.lib.sh" && semVerBump $(1) auto "" "$${MSG:-}"
	@$(CHANGELOG_GENERATE)
	@git add -- CHANGELOG.md
	@git diff --cached --quiet -- CHANGELOG.md || git commit -q -m "docs(changelog): update release history" -- CHANGELOG.md
endef

# require-tools vor precheck: ohne ProjectTools bricht ein Release vor dem Bump ab,
# nicht erst nach dem Tag.
.PHONY: tag-major
tag-major: require-tools precheck ## Major-Release {major}, inkompatible Änderung  [MSG="..."] — Maintainer
	$(call release,major)

.PHONY: tag-minor
tag-minor: require-tools precheck ## Minor-Release {minor}, neue Funktion  [MSG="..."] — Maintainer
	$(call release,minor)

.PHONY: tag-patch
tag-patch: require-tools precheck ## Patch-Release {patch}, Fehlerbehebung  [MSG="..."] — Maintainer
	$(call release,patch)
