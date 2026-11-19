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
# Prüf-Targets (test, check, docs-check, status, hints, changelog) brauchen ProjectTools,
# Maintainer-Targets (build, push, tag-*, version) BashLib; alle kommen über pipx. help, info
# und hints geben mit BashLib und CLITheme im Theme aus, ohne sie schlicht.
#
# Tag und Quelle (Git oder Arbeitskopie) der Werkzeuge stehen nur in .dev-tools.conf.sh;
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

# Farben der Statuszeilen (✓, ✗, ⚠) in den übrigen Rezepten. Von außen überschreibbar.
YELLOW ?= $(shell printf "\033[38;5;11m")
GREEN  ?= $(shell printf "\033[38;5;10m")
BLUE   ?= $(shell printf "\033[38;5;33m")
RED    ?= $(shell printf "\033[38;5;196m")
WHITE  ?= $(shell printf "\033[38;5;15m")
RESET  ?= $(shell printf "\033[0m")

# help, info und hints geben über make.lib.sh aus BashLib im CLI-Theme aus: BASH_ENV lädt es
# in jede Rezeptzeile, CLITHEME_EXPORT reicht die Werte von clitheme export einmal je make-Lauf
# weiter. Ohne BashLib zeigt bash keinen Fehler (BASH_ENV auf eine fehlende Datei), und die
# Ausgabe bleibt schlicht; Entwicklungs-Targets brauchen BashLib nicht.
clitheme_export = $(eval clitheme_export := $$(shell clitheme export --bash 2>/dev/null))$(clitheme_export)
help info hints: export BASH_ENV := $${BASH_LIBS}/make.lib.sh
help info hints: export CLITHEME_EXPORT = $(clitheme_export)

# heading TEXT und value BEZEICHNUNG WERT: mit make.lib.sh im Theme, sonst schlicht. Gewählt
# wird danach, ob die Funktion geladen ist, nicht ob die Datei existiert.
# Im Rezept: @$(PRINT_ROWS); value "Bezeichnung" "Wert"
PRINT_ROWS = heading() { if declare -F printMakeHeading >/dev/null; then printMakeHeading "$$1"; \
		else printf '\n  %s\n' "$$1"; fi; }; \
	value() { if declare -F printMakeValue >/dev/null; then printMakeValue "$$@"; \
		else printf '       %-22s %s\n' "$$1" "$${2-}"; fi; }

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

# Repo-Adresse (https) und letzter Release-Tag (nur v[0-9]*) für hints, von repo-info aus
# ProjectTools; ohne Remote oder Tag gibt es selbst einen lesbaren Ersatz aus. Die Rezepte
# lesen beide über die Umgebung, nicht als Text im Rezept.
export REPO_URL    := $(shell repo-info --url 2>/dev/null)
export RELEASE_TAG := $(shell repo-info --release-tag 2>/dev/null)

# ─── Hilfe ────────────────────────────────────────────────────────────────────

# Liste der Makefiles unausgewertet über die Umgebung (siehe Kopf).
export HELP_FILES = $(value MAKEFILE_LIST)

# Kopf, Gruppen und Targets über make.lib.sh; {major}, {minor} und {patch} füllt
# showMakeTargets mit „<jetzt> → <danach>“, „ — Maintainer“ wird zur Markierung
# [Maintainer]. Ohne BashLib eine schlichte Liste der Targets.
.PHONY: help
help: ## Alle verfügbaren Befehle anzeigen
	@if declare -F showMakeTargets >/dev/null; then \
		showMakeHeader "$${PROJECT_NAME}" && echo && showMakeTargets $${HELP_FILES}; \
	else \
		printf '\nmake <target>, Projekt %s:\n\n' "$${PROJECT_NAME}"; \
		grep -hE '^[a-zA-Z0-9_-]+:.*## ' $${HELP_FILES} | sed -E 's/^([^:]+):.*## /  \1\t/'; \
		echo; \
	fi

.PHONY: info
info: ## Projektpfade, Ports und Werkzeugstand anzeigen
	@$(PRINT_ROWS); heading "Umgebung"
	@$(PRINT_ROWS); value WORKSPACE        "$${WORKSPACE}"
	@$(PRINT_ROWS); value VENV             '$(VENV)'
	@$(PRINT_ROWS); value BASH_LIBS        "$${BASH_LIBS:-nicht gesetzt}"
	@$(PRINT_ROWS); value PROJECT_TOOLS    "$${PROJECT_TOOLS:-nicht gesetzt}"
	@$(PRINT_ROWS); value "Dev-Ports"      '$(DASHBOARD_PORT) (Dashboard) · $(BACKEND_PORT) (Backend)'
	@$(PRINT_ROWS); value "PORT (make up)" "$${PORT}"
	@$(PRINT_ROWS); heading "Werkzeuge (.dev-tools.conf.sh)"
	@# devtools status gibt je Werkzeug „  Name  Stand“ aus; Name und Stand gehen einzeln an
	@# value, so stehen sie in denselben Spalten wie die Zeilen darüber.
	@$(PRINT_ROWS); set -o pipefail; $(DEV_TOOLS) status | while read -r TOOL_NAME TOOL_STATE; do \
		[[ -z "$$TOOL_NAME" ]] || value "$$TOOL_NAME" "$$TOOL_STATE"; done || \
		value "Stand" "nicht abrufbar: pipx run devtools"
	@echo

# Links, URLs und Tipps für den Alltag; das Einrichten beschreibt docs/development.md.
.PHONY: hints
hints: require-tools ## Links, URLs und Tipps für die tägliche Arbeit
	@$(PRINT_ROWS); heading "Links"
	@$(PRINT_ROWS); value "Repository"      "$${REPO_URL}"
	@$(PRINT_ROWS); value "Entwicklerdoku"  "$(if $(filter https://%,$(REPO_URL)),$${REPO_URL}/blob/master/docs/development.md,docs/development.md)"
	@$(PRINT_ROWS); value "Letzter Release" "$${RELEASE_TAG}"
	@$(PRINT_ROWS); value "Docker Hub"      "https://hub.docker.com/r/$${IMAGE_NAME}"
	@$(PRINT_ROWS); heading "URLs nach make dev-up (http://, nicht https)"
	@$(PRINT_ROWS); value "Dashboard"           "http://localhost:$(DASHBOARD_PORT)/"
	@$(PRINT_ROWS); value "API"                 "http://localhost:$(BACKEND_PORT)/"
	@$(PRINT_ROWS); value "Swagger"             "http://localhost:$(BACKEND_PORT)/docs"
	@$(PRINT_ROWS); value "Health"              "http://localhost:$(BACKEND_PORT)/health"
	@$(PRINT_ROWS); value "Container (make up)" "http://localhost:$${PORT}/"
	@$(PRINT_ROWS); heading "Im Alltag"
	@$(PRINT_ROWS); value "Vor dem Commit" "make check"
	@$(PRINT_ROWS); value "Einzelne Tests" "make test-backend ARGS='-k name'"
	@$(PRINT_ROWS); value "Stack hängt"    "make dev-down; dann make dev-up"
	@$(PRINT_ROWS); value "Erster Kurs"    "curl http://localhost:$(BACKEND_PORT)/quote/IE00B4L5Y983"
	@$(PRINT_ROWS); value "Unraid-Test"    "wget -O /boot/config/plugins/dockerMan/templates-user/stockinfo-test.xml https://raw.githubusercontent.com/MikeMitterer/unraid-templates/master/templates/stockinfo.xml"
	@$(PRINT_ROWS); heading "Werkzeuge (Tag und Quelle in .dev-tools.conf.sh)"
	@$(PRINT_ROWS); value "Stand zeigen"      "make setup"
	@$(PRINT_ROWS); value "Auf Stand bringen" "make install-tools"
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
install-tools: ## ProjectTools, BashLib und CLITheme auf den Stand aus .dev-tools.conf.sh bringen (pipx)
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
check: docs-check test-plugin-api test-example test-dashboard quality ## Alle netzfreien Prüfungen — Doku, Backend ohne Online-Tests, Plugin-API, Beispiel, Dashboard, Grenzen, Typen
	$(PYTEST) -q -m "not integration"
	cd dashboard && npx vue-tsc -b

# Messbare Grenzen (T-144). Die Zahlen stehen nur in pyproject.toml. Ruff mit
# Komplexität und Vereinfachungen sowie Modulgröße und doppelter Code in App,
# Skripten und Plugin-API brechen `check`; doppelter Code in Tests ist nur Bericht.
.PHONY: quality
quality: require-setup ## Messbare Grenzen — Ruff (Komplexität, Vereinfachungen), Modulgröße, doppelter Code
	@$(PRINT_ROWS); heading "Ruff: Fehler, Komplexität, Vereinfachungen"
	$(VENV)/bin/ruff check app tests scripts plugin_api
	@$(PRINT_ROWS); heading "Pylint: Modulgröße und doppelter Code"
	$(VENV)/bin/python -m pylint app scripts plugin_api/src plugin_api/examples \
		--disable=all --enable=too-many-lines,duplicate-code --score=n
	@$(PRINT_ROWS); heading "Bericht, bricht nicht: doppelter Code in Tests"
	@$(VENV)/bin/python -m pylint tests plugin_api/tests \
		--disable=all --enable=duplicate-code --score=n --exit-zero

# Braucht Netz und gehört deshalb nicht zu `check`. Ein Fund bricht den Lauf
# nicht ab (Entscheidung q-11); beide Prüfungen laufen immer.
.PHONY: audit
audit: require-setup ## Bekannte Lücken in Abhängigkeiten — pip-audit und npm audit (Bericht, braucht Netz)
	@$(PRINT_ROWS); heading "Python (pip-audit, requirements.txt)"
	-$(VENV)/bin/pip-audit -r requirements.txt
	@$(PRINT_ROWS); heading "Dashboard (npm audit, ohne Entwicklungspakete)"
	-npm --prefix dashboard audit --omit=dev

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
	 TAG="$${RELEASE_TAG:-nicht abrufbar: make install-tools}"; \
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
