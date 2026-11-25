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

# Prüfungen, Status und Releases laufen über die Befehle von ProjectTools in .tools/ dieses
# Checkouts (make setup); help, info, hints und die Statuszeilen über BashLib. Tag und Quelle
# der Werkzeuge und von DevTools selbst stehen nur in .dev-tools.conf.sh. Aufgerufen wird das
# einmal je Rechner installierte devtools (Starter); ist es älter als DEVTOOLS_TAG, gibt es an
# diesen Tag weiter. Mit --project installiert und prüft es die Werkzeuge in .tools/.
include .dev-tools.conf.sh
# Ohne die Git-Variablen eines Hooks (make docs-check im pre-commit): Ein älterer Starter gäbe
# sie an pipx weiter, und pip klonte in den Index dieses Repositorys.
DEV_TOOLS := env -u GIT_INDEX_FILE -u GIT_DIR -u GIT_WORK_TREE devtools --project
# Bricht ab, wenn der Starter fehlt, und nennt den Weg dorthin. Solange die Werkzeuge nicht
# veröffentlicht sind, kommt er aus der lokalen DevTools-Arbeitskopie. Im Rezept vor jedem
# Aufruf von devtools: @$(REQUIRE_STARTER); …
REQUIRE_STARTER = command -v devtools >/dev/null || { \
	echo "  ✗ devtools fehlt: einmal je Rechner in der DevTools-Arbeitskopie make install" >&2; exit 1; }

# Werkzeuge aus .tools/ dieses Checkouts vorn im PATH; ein global installiertes ProjectTools
# zählt für require-tools nicht. BashLib für help, info, hints, Statuszeilen, version, tag-*,
# docker/build.sh und scripts/: Ein von außen gesetztes BASH_LIBS geht vor, sonst die aus
# .tools/.
TOOLS_DIR := .tools
export PATH := $(WORKSPACE)/$(TOOLS_DIR)/bin:$(PATH)
BASHLIB_FROM_OUTSIDE := $(if $(BASH_LIBS),yes)
ifndef BASH_LIBS
BASH_LIBS := $(shell $(WORKSPACE_SQ)/$(TOOLS_DIR)/bin/bashlib-path 2>/dev/null)
endif
export BASH_LIBS
# BashLib zur Laufzeit eines Rezepts. Make ermittelt BASH_LIBS beim Lesen des Makefiles; hat
# erst precheck oder require-setup im selben Lauf eingerichtet, ist es noch leer, und
# bashlib-path aus .tools/ nennt den Ort. Exportiert, weil make.lib.sh die übrigen
# Bibliotheken über BASH_LIBS lädt. Im Rezept vor BashLib: @$(BASHLIB_ENV); …
BASHLIB_ENV = export BASH_LIBS="$${BASH_LIBS:-$$(bashlib-path 2>/dev/null)}"
# Vorspann für $(shell) mit einem Werkzeug aus .tools/: $(shell $(TOOL_ENV); befehl). GNU Make
# vor 4.4 (macOS: 3.81) gibt das exportierte PATH nicht an $(shell) weiter, und das BASH_ENV
# von help, info und hints gehört nicht in die Werkzeuge.
TOOL_ENV = unset BASH_ENV; PATH=$(WORKSPACE_SQ)/$(TOOLS_DIR)/bin:"$$PATH"

# Statuszeile und Zwischenüberschrift außerhalb von help, info und hints, im CLI-Theme von
# BashLib. Im Rezept: @$(STATUS) "✓" "Text" OK  (Rollen OK, WARN, ERR) bzw.
# @$(HEADING) "Text". Bewusst kein BASH_ENV für diese Targets: Es ginge an overmind, docker
# und die Skripte weiter.
STATUS  = $(BASHLIB_ENV); source "$${BASH_LIBS}/make.lib.sh" && printThemeStatus
HEADING = $(BASHLIB_ENV); source "$${BASH_LIBS}/make.lib.sh" && printMakeHeading

# Mindestversion von Python, gelesen aus `requires-python = ">=X.Y"` in pyproject.toml, der
# einzigen Quelle. Leer, wenn die Zeile anders aussieht; setup bricht dann mit Meldung ab.
PYTHON_MIN := $(shell sed -n 's/^requires-python = ">=\([0-9][0-9.]*\)"$$/\1/p' pyproject.toml)
# Interpreter, mit dem `make setup` die .venv anlegt: PYTHON_BOOTSTRAP aus der Umgebung, sonst
# python$(PYTHON_MIN). Als Wert von außen liest ihn die Shell im Rezept, nicht Make: Ein Pfad mit
# Apostroph, Leerzeichen oder $(…) bliebe als $(PYTHON_BOOTSTRAP) im Rezepttext nicht heil.
BOOTSTRAP = "$${PYTHON_BOOTSTRAP:-python$(PYTHON_MIN)}"
# Python-Ausdruck für `-c`: Exit 0 ab PYTHON_MIN, sonst Abbruch mit der gefundenen Version.
PYTHON_MIN_CHECK = import sys; sys.exit(0 if sys.version_info >= tuple(map(int, "$(PYTHON_MIN)".split("."))) else "Python $(PYTHON_MIN) oder neuer erforderlich, gefunden " + sys.version.split()[0])

VENV    := .venv
PYTEST  := $(VENV)/bin/pytest
# Was setup herstellt und require-setup prüft: Python-Pakete in der .venv, die
# Dashboard-Pakete und die Werkzeuge in .tools/. Eine geänderte Abhängigkeitsdatei macht den
# Stempel veraltet. Der Stempel der .venv trägt die Mindestversion im Namen: Steigt sie, fehlt
# er, require-setup verlangt make setup, und setup ersetzt eine .venv mit älterem Python.
VENV_STAMP   := $(VENV)/.installed-python$(PYTHON_MIN)
TOOLS_STAMP  := $(TOOLS_DIR)/.installed
SETUP_STAMPS := $(VENV_STAMP) dashboard/node_modules/.installed $(TOOLS_STAMP)

# Ports des Dev-Stacks nennt dev-ports (--port-of NAME) aus ProjectTools; sie stehen dort, wo sie
# beim Start wirken: das Backend mit --port in Procfile.dev, das Dashboard als server.port in
# dashboard/vite.config.ts. Das Makefile legt keine der Dateien selbst aus. Ohne dev-ports
# (vor make setup) nennen info und hints statt der Adresse NO_DEV_PORTS; dev-up bricht dann
# schon in require-tools ab. Nur Ziffern werden übernommen; die Werte stehen danach als Zahlen in
# den Rezepten. Ermittelt erst beim ersten Gebrauch und dann gemerkt, damit die übrigen Targets
# dev-ports nicht starten.
NO_DEV_PORTS := ? (dev-ports fehlt: make setup)
dev_port     = $(shell $(TOOL_ENV); dev-ports --port-of $(1) 2>/dev/null | grep -xE '[0-9]+')
# Adresse eines Dienstes mit Pfad $(2), ohne bekannten Port NO_DEV_PORTS.
dev_url      = $(if $($(1)),http://localhost:$($(1))$(2),$(NO_DEV_PORTS))
# override: Ein gleichnamiges Make-Argument oder `make -e` setzt sie nicht, sonst stünde ein
# fremder Wert ungeprüft im Rezepttext. unexport: Stehen sie in der Umgebung, gäbe Make sie an
# $(shell) weiter und müsste sie dafür mitten in ihrer eigenen Ermittlung auswerten (leerer
# Port unter Make 4.4).
override DASHBOARD_PORT = $(eval override DASHBOARD_PORT := $$(call dev_port,dashboard))$(DASHBOARD_PORT)
override BACKEND_PORT   = $(eval override BACKEND_PORT := $$(call dev_port,backend))$(BACKEND_PORT)
unexport DASHBOARD_PORT BACKEND_PORT

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

# Repo-Adresse (https) und letzter Release-Tag (nur v[0-9]*) für hints, von repo-info aus
# ProjectTools; ohne Remote oder Tag gibt es selbst einen lesbaren Ersatz aus, ohne ProjectTools
# nennt die Zeile, was fehlt. hints läuft so auch auf einem frischen Klon. Ermittelt nur, wenn
# hints aufgerufen wird, und schon beim Lesen des Makefiles: Bei der Ausführung gäbe Make die
# für hints exportierten Werte an $(shell) weiter und müsste sie dafür mitten in ihrer eigenen
# Ermittlung auswerten (leerer Wert unter Make 4.4). Beide lassen sich als Make-Argument
# setzen; die Rezepte lesen sie darum als "$${REPO_URL}" aus der Umgebung, nie als Text.
NO_REPO_INFO := repo-info fehlt (ProjectTools): make setup
repo_info    = $(or $(shell $(TOOL_ENV); repo-info $(1) 2>/dev/null),$(NO_REPO_INFO))
ifneq ($(filter hints,$(MAKECMDGOALS)),)
repo_url    := $(call repo_info,--url)
release_tag := $(call repo_info,--release-tag)
endif
hints: export REPO_URL = $(repo_url)
hints: export RELEASE_TAG = $(release_tag)

# ─── Hilfe ────────────────────────────────────────────────────────────────────

# help, info und hints geben über BashLib make.lib.sh aus, geladen über BASH_ENV in jede
# Rezeptzeile; eine Rezeptzeile ergibt eine Ausgabezeile. Bash wertet BASH_ENV aus: darum der
# Verweis auf BASH_LIBS statt des Pfads, ein $(…) im Checkout-Pfad bleibt Text.
# CLITHEME_EXPORT reicht die Werte von clitheme export einmal je make-Lauf weiter, statt
# clitheme in jeder Zeile zu starten.
clitheme_export = $(eval clitheme_export := $$(shell $$(TOOL_ENV); clitheme export --bash 2>/dev/null))$(clitheme_export)
help info hints: export BASH_ENV := $${BASH_LIBS}/make.lib.sh
help info hints: export CLITHEME_EXPORT = $(clitheme_export)

# Liste der Makefiles unausgewertet über die Umgebung (siehe Kopf).
export HELP_FILES = $(value MAKEFILE_LIST)

# Eine Beschreibung sagt, was nach dem Target anders ist; den Ablauf beschreibt
# docs/development.md. {major}, {minor} und {patch} füllt showMakeTargets mit
# „<jetzt> → <danach>“.
.PHONY: help
help: ## Alle verfügbaren Befehle anzeigen
	@showMakeHeader "$${PROJECT_NAME}"
	@showMakeTargets $${HELP_FILES}

.PHONY: info
info: ## Projektpfade, Ports und Werkzeugstand anzeigen
	@printMakeHeading "Umgebung"
	@printMakeValue WORKSPACE        "$${WORKSPACE}"
	@printMakeValue VENV             '$(VENV)'
	@printMakeValue BASH_LIBS        "$${BASH_LIBS:-nicht gefunden (make setup)}"
	@printMakeValue "Dev-Ports"      '$(if $(BACKEND_PORT),$(DASHBOARD_PORT) (Dashboard) · $(BACKEND_PORT) (Backend),$(NO_DEV_PORTS))'
	@printMakeValue "PORT (make up)" "$${PORT}"
	@printMakeHeading "Werkzeuge (.dev-tools.conf.sh)"
	@# devtools status gibt je Werkzeug „  Name  Stand“ aus; Name und Stand gehen einzeln an
	@# printMakeValue, so stehen sie in denselben Spalten wie die Zeilen darüber.
	@set -o pipefail; $(DEV_TOOLS) status 2>/dev/null | while read -r TOOL_NAME TOOL_STATE; do \
		[[ -z "$$TOOL_NAME" ]] || printMakeValue "$$TOOL_NAME" "$$TOOL_STATE"; done || \
		printMakeValue "Stand" "nicht abrufbar: make setup"
	@echo

# Links, URLs und Tipps für den Alltag; das Einrichten beschreibt docs/development.md.
.PHONY: hints
hints: ## Links, URLs und Tipps für die tägliche Arbeit
	@printMakeHeading "Links"
	@printMakeValue "Repository"      "$${REPO_URL}"
	@printMakeValue "Entwicklerdoku"  "$(if $(filter https://%,$(REPO_URL)),$${REPO_URL}/blob/master/docs/development.md,docs/development.md)"
	@printMakeValue "Letzter Release" "$${RELEASE_TAG}"
	@printMakeValue "Docker Hub"      "https://hub.docker.com/r/$${IMAGE_NAME}"
	@printMakeHeading "URLs nach make dev-up (http://, nicht https)"
	@printMakeValue "Dashboard"           '$(call dev_url,DASHBOARD_PORT,/)'
	@printMakeValue "API"                 '$(call dev_url,BACKEND_PORT,/)'
	@printMakeValue "Swagger"             '$(call dev_url,BACKEND_PORT,/docs)'
	@printMakeValue "Health"              '$(call dev_url,BACKEND_PORT,/health)'
	@printMakeValue "Container (make up)" "http://localhost:$${PORT}/"
	@printMakeHeading "Im Alltag"
	@printMakeValue "Vor dem Commit" "make check"
	@printMakeValue "Einzelne Tests" "make test-backend ARGS='-k name'"
	@printMakeValue "Stack hängt"    "make dev-down; dann make dev-up"
	@printMakeValue "Erster Kurs"    '$(if $(BACKEND_PORT),curl )$(call dev_url,BACKEND_PORT,/quote/IE00B4L5Y983)'
	@printMakeValue "Unraid-Test"    "wget -O /boot/config/plugins/dockerMan/templates-user/stockinfo-test.xml https://raw.githubusercontent.com/MikeMitterer/unraid-templates/master/templates/stockinfo.xml"
	@printMakeHeading "Werkzeuge (Tag und Quelle in .dev-tools.conf.sh)"
	@printMakeValue "Stand zeigen"      "make info"
	@printMakeValue "Auf Stand bringen" "make setup"
	@echo

# ─── Precheck ─────────────────────────────────────────────────────────────────

# BashLib bereit: die Bibliotheken, die das Makefile lädt (version.lib.sh für Releases,
# make.lib.sh für Statuszeilen und Ausgabe), lesbar; aus .tools/ zudem in der Mindestversion
# aus .dev-tools.conf.sh. Ein von außen gesetztes BASH_LIBS prüft es nur auf Lesbarkeit.
BASHLIB_READY = $(BASHLIB_ENV); [[ -r "$$BASH_LIBS/version.lib.sh" && -r "$$BASH_LIBS/make.lib.sh" ]] && \
	{ [[ -n '$(BASHLIB_FROM_OUTSIDE)' ]] || $(DEV_TOOLS) check bashlib >/dev/null 2>&1; }

# Ohne `##`: läuft vor dev-up, dev-down, up, down, version, tags, build, push und
# require-tools. Fehlt BashLib oder ist sie zu alt, läuft einmal make setup; reicht das nicht,
# bricht es mit dem Grund ab. Bewusst ohne BashLib-Ausgabe: precheck meldet gerade, dass sie fehlt.
.PHONY: precheck
precheck:
	@$(BASHLIB_READY) || $(MAKE) --no-print-directory setup
	@$(BASHLIB_READY) || { echo "  ✗ BashLib fehlt oder ist unvollständig (BASH_LIBS oder .tools/)" >&2; \
		[[ -n '$(BASHLIB_FROM_OUTSIDE)' ]] || $(DEV_TOOLS) check bashlib; exit 1; }

# Ohne `##`: verlangt ProjectTools in .tools/ in Mindestversion. Fehlt es oder ist es zu alt,
# läuft einmal make setup; reicht das nicht (etwa ein zu alter Tag in .dev-tools.conf.sh),
# nennt devtools den Grund.
.PHONY: require-tools
require-tools: precheck
	@$(REQUIRE_STARTER); $(DEV_TOOLS) check projecttools >/dev/null 2>&1 || \
		{ $(MAKE) --no-print-directory setup && $(DEV_TOOLS) check projecttools; }

# ─── Setup ────────────────────────────────────────────────────────────────────

##@ Setup

# setup ist der einzige Weg, das Projekt einzurichten, auch als worktree_setup in Workspaces
# und im Prüf-Worktree. Prüf-Targets hängen an require-setup, das bei Bedarf make setup
# aufruft. Wiederholbar: Die Stempel machen einen eingerichteten Stand zum Nulllauf.
.PHONY: setup
setup: ## Bereit zum Entwickeln: .venv, Dashboard-Pakete, .tools/, Git-Hooks
	@git config core.hooksPath .githooks
	@$(MAKE) -s --no-print-directory $(SETUP_STAMPS)

# Stempelregeln: nur setup erreicht sie; neu, sobald eine Abhängigkeitsdatei neuer ist.
# Eine .venv ohne lauffähiges Python ab PYTHON_MIN wird mit --clear neu angelegt; sie ist ein
# Erzeugnis von setup. Ein Zweig für fehlende .venv, ins Leere zeigenden Interpreter-Link (etwa
# nachdem Homebrew das alte Python entfernt hat) und zu altes Python: venv ohne --clear
# scheiterte an den toten Links mit Errno 2.
$(VENV_STAMP): requirements.txt requirements-dev.txt
	@test -n '$(PYTHON_MIN)' || { echo '  ✗ requires-python in pyproject.toml ist nicht als ">=X.Y" lesbar' >&2; exit 1; }
	@command -v $(BOOTSTRAP) >/dev/null || { echo "  ✗ "$(BOOTSTRAP)" nicht gefunden: Python $(PYTHON_MIN) installieren oder PYTHON_BOOTSTRAP=<Interpreter> make setup" >&2; exit 1; }
	@$(BOOTSTRAP) -c '$(PYTHON_MIN_CHECK)' || { echo '  ✗ PYTHON_BOOTSTRAP ist zu alt: PYTHON_BOOTSTRAP=python$(PYTHON_MIN) make setup' >&2; exit 1; }
	@if ! $(VENV)/bin/python -c '$(PYTHON_MIN_CHECK)' 2>/dev/null; then \
		test -e $(VENV) && echo '  ⚠ .venv ohne lauffähiges Python ab $(PYTHON_MIN) wird neu angelegt'; \
		$(BOOTSTRAP) -m venv --clear $(VENV); \
	fi
	@rm -f $(VENV)/.installed $(VENV)/.installed-python*
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

# Werkzeuge auf Quelle und Tag aus .dev-tools.conf.sh nach .tools/; devtools meldet je Werkzeug
# eine Zeile. Mit rechnerlokaler Zuordnung von DevTools kommen sie aus den lokalen Repos.
$(TOOLS_STAMP): .dev-tools.conf.sh
	@$(REQUIRE_STARTER); $(DEV_TOOLS) install
	@touch "$@"

# Ohne Hilfeeintrag: Fehlt die Einrichtung oder ist sie veraltet (ein Stempel fehlt oder ist
# älter als seine Abhängigkeit, Git-Hooks nicht aktiv), läuft make setup; sonst nichts.
# Eingerichtet wird nur über setup. Braucht kein BashLib, das erst mit setup kommt. Der
# pre-commit-Hook ruft es im Checkout, nicht in seiner Kopie des Index: Dort wäre jede Datei
# neuer als die Stempel.
.PHONY: require-setup
require-setup:
	@{ $(MAKE) --no-print-directory --question $(SETUP_STAMPS) && \
		[[ "$$(git config core.hooksPath)" == .githooks ]]; } 2>/dev/null || \
		$(MAKE) --no-print-directory setup

# Entfernt nur, was setup, Tests und Builds im Checkout erzeugen. Die Pfade stehen fest im
# Rezept, nicht in einer Variable, die ein Make-Argument überschreiben könnte (VENV,
# TOOLS_DIR). __pycache__ und *.egg-info nur in den Code-Ordnern, nie im Projekt-Root:
# Umgebungsdatei, data/ samt Plugin-Daten und der Build-Nachweis docker/.last-build-tag sind
# Arbeitsstand, kein Erzeugnis; .worktrees/ und _tickets/ sind eigene Checkouts.
.PHONY: clean
clean: ## Checkout zurückgesetzt: .venv, Dashboard-Pakete, .tools/, Caches weg
	@rm -rf -- .venv .tools dashboard/node_modules dashboard/tsconfig.tsbuildinfo \
		.pytest_cache .ruff_cache plugin_api/.pytest_cache .tmp build dist
	@find app tests scripts plugin_api -type d \( -name __pycache__ -o -name '*.egg-info' \) \
		-prune -exec rm -rf -- {} +
	@echo "  ✓ Checkout zurückgesetzt; weiter mit make setup"

# ─── Status ───────────────────────────────────────────────────────────────────

##@ Status

.PHONY: status
status: require-tools ## Git-Status aller Workspace-Repos anzeigen
	@repo-status --show

# ─── Entwicklung ──────────────────────────────────────────────────────────────

##@ Entwicklung

# Ein belegter Port bricht den Start ab, statt dass eine App still ausweicht. dev-ports
# (ProjectTools) ist Voraussetzung, auch in Procfile.dev: require-tools bricht ohne es ab und
# nennt den Installationsbefehl, bevor overmind startet oder beendet wird (makefile-conventions).
# Anders als StockPortfolio und Darwin+Finanzen ohne OVERMIND_SKIP_ENV: HOST aus .env erreicht
# uvicorn in Procfile.dev nur, weil overmind .env lädt; das Makefile exportiert HOST nicht.
.PHONY: dev-up
dev-up: require-tools ## Backend und Dashboard laufen im Hintergrund, mit Auto-Reload
	@command -v overmind >/dev/null || { $(STATUS) "✗" "overmind fehlt: brew install overmind tmux" ERR; exit 1; }
	@command -v tmux >/dev/null || { $(STATUS) "✗" "tmux fehlt: brew install tmux" ERR; exit 1; }
	@dev-ports --check
	@# overmind bricht auch ab, wenn der Stack schon läuft oder eine verwaiste .overmind.sock
	@# eines Absturzes liegt; aufräumen kann nur dev-down.
	@overmind start -D -N -f Procfile.dev || { \
		$(STATUS) "⚠" "Nicht gestartet. Läuft der Stack schon: make dev-logs. Nach einem Absturz räumt make dev-down die Reste auf." WARN; \
		exit 1; }
	@$(STATUS) "✓" 'Stack läuft — Backend $(call dev_url,BACKEND_PORT,) · Dashboard $(call dev_url,DASHBOARD_PORT,)  (make dev-logs)' OK

# Räumt nach einem Absturz overmind/tmux DIESES Projekts, eine verwaiste .overmind.sock und
# die Ports aus Procfile.dev und der Vite-Konfiguration auf (dev-ports --kill).
.PHONY: dev-down
dev-down: require-tools ## Dev-Stack gestoppt, Reste nach einem Absturz beseitigt, Ports frei
	-@overmind quit 2>/dev/null || true
	@dev-ports --kill
	@$(STATUS) "✓" "Stack gestoppt" OK

.PHONY: dev-logs
dev-logs: ## Logs des Dev-Stacks live verfolgen
	overmind echo

# ─── Tests ────────────────────────────────────────────────────────────────────

##@ Tests

# require-setup zuerst: Es richtet bei Bedarf ein, bevor etwas anläuft.
.PHONY: test
test: require-setup docs-check test-backend test-plugin-api test-example test-dashboard ## Alle Tests — Doku, Backend, Plugin-API, Beispielpaket, Dashboard

# Teil von test und check: Ohne ProjectTools richtet es ein, statt die Doku still zu
# überspringen. Regeln in .docs-check.conf.sh.
DOCS_CHECK_RUN = docs-check --run

.PHONY: docs-check docs-check-only
docs-check: require-setup require-tools ## Nutzerdoku gegen das Projekt geprüft (Links, Befehle, Variablen)
	@$(DOCS_CHECK_RUN)

# Ohne Hilfeeintrag: die Prüfung ohne require-setup, für die Kopie des Index im pre-commit-Hook;
# der Hook ruft vorher require-setup und require-tools im Checkout.
docs-check-only:
	@$(DOCS_CHECK_RUN)

# Wie `test`, aber ohne Netz: Die mit `integration` markierten Tests fragen
# echte Online-Anbieter und bleiben bei `test`. Dazu Ruff und die Typprüfung
# des Dashboards, die `test` nicht enthält.
.PHONY: check
check: require-setup docs-check test-plugin-api test-example test-dashboard quality ## Alles ohne Netz geprüft: Doku, Tests (ohne Online), Grenzen, Typen
	$(PYTEST) -q -m "not integration"
	cd dashboard && npx vue-tsc -b

# Messbare Grenzen (T-144). Die Zahlen stehen nur in pyproject.toml. Ruff mit
# Komplexität und Vereinfachungen sowie Modulgröße und doppelter Code in App,
# Skripten und Plugin-API brechen `check`; doppelter Code in Tests ist nur Bericht.
.PHONY: quality
quality: require-setup ## Messbare Grenzen geprüft: Ruff, Modulgröße, doppelter Code
	@$(HEADING) "Ruff: Fehler, Komplexität, Vereinfachungen"
	$(VENV)/bin/ruff check app tests scripts plugin_api
	@$(HEADING) "Pylint: Modulgröße und doppelter Code"
	$(VENV)/bin/python -m pylint app scripts plugin_api/src plugin_api/examples \
		--disable=all --enable=too-many-lines,duplicate-code --score=n
	@$(HEADING) "Bericht, bricht nicht: doppelter Code in Tests"
	@$(VENV)/bin/python -m pylint tests plugin_api/tests \
		--disable=all --enable=duplicate-code --score=n --exit-zero

# Braucht Netz und gehört deshalb nicht zu `check`. Ein Fund bricht den Lauf
# nicht ab (Entscheidung q-11); beide Prüfungen laufen immer.
.PHONY: audit
audit: require-setup ## Bericht zu Lücken in Abhängigkeiten: pip-audit, npm audit (Netz)
	@$(HEADING) "Python (pip-audit, requirements.txt)"
	-$(VENV)/bin/pip-audit -r requirements.txt
	@$(HEADING) "Dashboard (npm audit, ohne Entwicklungspakete)"
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

# precheck vorab wie bei dev-up: ohne BashLib scheitern up und down vor docker, nicht danach.
.PHONY: up
up: precheck ## Container mit Dashboard und API läuft auf PORT (Image aus make build)
	-@docker rm -f "$${CONTAINER}" 2>/dev/null || true
	docker run -d --name "$${CONTAINER}" \
		-p "$${PORT}":8000 \
		--env-file .env \
		-e HOST=0.0.0.0 -e PORT=8000 -e DATABASE_PATH=/data/stockinfo.db \
		-v "$${DATA_VOLUME}":/data \
		--restart unless-stopped \
		"$${IMAGE_NAME}":latest
	@$(STATUS) "✓" "Läuft — App http://localhost:$${PORT}/  (zuvor: make build)" OK

.PHONY: down
down: precheck ## Container gestoppt und entfernt
	-@if docker rm -f "$${CONTAINER}" 2>/dev/null; then $(STATUS) "✓" "Gestoppt" OK; \
	else $(STATUS) "⚠" "Kein Container $${CONTAINER}" WARN; fi

.PHONY: docker-logs
docker-logs: ## Container-Logs live verfolgen
	docker logs -f "$${CONTAINER}"

# docker/build.sh braucht BashLib; ohne sie baut docs/development.md das Image direkt mit
# docker build. BASH_LIBS zur Laufzeit, falls precheck erst eingerichtet hat.
.PHONY: build
build: precheck ## Geprüftes Image für PLATFORM=x86|arm (Vorgabe x86)
	@$(BASHLIB_ENV); docker/build.sh --build "$${PLATFORM}"

# Startet das zuletzt gebaute Image wie ein User ohne Klon (Wegwerf-Container, freier Port an
# 127.0.0.1) und prüft /health und das Dashboard; Ablauf in docker/build.sh --check.
.PHONY: build-check
build-check: precheck ## Gebautes Image startet, /health ok, Dashboard unter /
	@$(BASHLIB_ENV); docker/build.sh --check

.PHONY: push
push: require-tools ## Image und docker/README.md veröffentlicht (TARGET=ghcr|dockerhub|ecr)
	@$(BASHLIB_ENV); docker/build.sh --push

# ─── Versionierung ────────────────────────────────────────────────────────────

##@ Versionierung

.PHONY: version
version: precheck ## Version aus pyproject.toml und letzter Release-Tag
	@echo
	@$(BASHLIB_ENV); source "$${BASH_LIBS}/make.lib.sh" && showProjectVersion
	@echo

.PHONY: tags
tags: precheck ## Letzte 10 Release-Tags mit Nachricht anzeigen
	@echo
	@$(BASHLIB_ENV); source "$${BASH_LIBS}/make.lib.sh" && showReleaseTags 10
	@echo

# Sprache von CHANGELOG.md, unabhängig von der Locale der Shell (changelog folgt sonst LANG).
# Englisch wie die übrige Doku. Überschreiben: make … CHANGELOG_LANGUAGE=de
CHANGELOG_LANGUAGE ?= en
export CHANGELOG_LANGUAGE

.PHONY: changelog
changelog: require-tools ## CHANGELOG.md aus Release-Tags erstellen (ohne Commit)
	@LANGUAGE="$${CHANGELOG_LANGUAGE}" changelog --generate

# MSG von der Kommandozeile unausgewertet; sonst macht Make aus $HOME oder $(…) schon beim
# Export an das Rezept etwas anderes. Im Rezept nur als "$${MSG:-}".
override MSG := $(value MSG)
export MSG

# Je Target eine Hilfezeile; showMakeTargets liest nur Zeilen mit einem Target.
.PHONY: tag-major tag-minor tag-patch
tag-major: ## Major-Release {major}, inkompatible Änderung  [MSG="..."]
tag-minor: ## Minor-Release {minor}, neue Funktion  [MSG="..."]
tag-patch: ## Patch-Release {patch}, Fehlerbehebung  [MSG="..."]

# Version heben und lokal taggen, CHANGELOG.md committen, die Stufe develop auf master
# vorspulen; alles nur lokal, veröffentlicht wird mit git push --follow-tags. Prüfung und
# Ablauf stehen nur in tag-version (ProjectTools): Es bricht ab, solange develop Commits hat,
# die noch nicht auf master sind (nicht abgenommene Tickets). changelog nennt bei Erfolg den
# Pfad der Datei, darum ohne stdout; Fehler kommen über stderr.
# require-tools vor precheck: ohne ProjectTools bricht ein Release vor dem Bump ab, nicht erst
# nach dem Tag.
tag-major tag-minor tag-patch: require-tools precheck
	@tag-version "$(patsubst tag-%,%,$@)" --message "$${MSG:-}"
	@LANGUAGE="$${CHANGELOG_LANGUAGE}" changelog --commit >/dev/null
	@tag-version --fast-forward
