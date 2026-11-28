SHELL := bash

.DEFAULT_GOAL := help

# MSG (Nachricht für tag-*) unausgewertet übernehmen, vor dem ersten $(shell …): Make exportiert
# eine Variable von der Kommandozeile und wertet sie dabei aus; aus „$HOME“ würde „OME“, und ein
# $(shell …) in der Nachricht liefe. Im Rezept nur als "$${MSG:-}".
override MSG := $(value MSG)
export MSG
# Ebenso den Interpreter für die .venv (unten).
ifdef PYTHON_BOOTSTRAP
override PYTHON_BOOTSTRAP := $(value PYTHON_BOOTSTRAP)
endif

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
# Checkouts (make setup); help, info, hints und die Statuszeilen über die Bash-Libs von
# CLITheme, die Version im Kopf von help über BashLib. Tag und Quelle
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
# zählt für require-tools nicht. Geerbte Werte (PATH, BASH_LIBS, CLI_LIBS, CLITHEME_EXPORT)
# unausgewertet mit $(value …): Ein make setup aus einem Target erbt sie, und ein $(…) im
# Checkout-Pfad liefe sonst als Make-Code.
TOOLS_DIR := .tools
export PATH := $(WORKSPACE)/$(TOOLS_DIR)/bin:$(value PATH)
# BashLib (Version im Kopf von help, tag-*, docker/build.sh, scripts/): ein von außen gesetztes
# BASH_LIBS geht vor, sonst die aus .tools/. Mit = statt :=: make ermittelt den Wert je Target
# neu, so sieht ein Target nach require-bash-libs (make setup) BashLib aus .tools/ im selben Lauf.
BASHLIB_FROM_OUTSIDE := $(if $(value BASH_LIBS),yes)
ifndef BASH_LIBS
BASH_LIBS = $(shell $(WORKSPACE_SQ)/$(TOOLS_DIR)/bin/bashlib-path 2>/dev/null)
else
override BASH_LIBS := $(value BASH_LIBS)
endif
export BASH_LIBS
# Bash-Libs von CLITheme (cli.lib.sh, make.lib.sh) für help, info, hints, Statuszeilen und die
# Skripte; ebenso aus .tools/, wenn nicht von außen gesetzt.
CLILIB_FROM_OUTSIDE := $(if $(value CLI_LIBS),yes)
ifndef CLI_LIBS
CLI_LIBS = $(shell $(WORKSPACE_SQ)/$(TOOLS_DIR)/bin/clilib-path 2>/dev/null)
else
override CLI_LIBS := $(value CLI_LIBS)
endif
export CLI_LIBS
# Theme einmal je make-Lauf statt je Rezeptzeile; ein geerbter Export gilt.
ifndef CLITHEME_EXPORT
CLITHEME_EXPORT := $(shell $(WORKSPACE_SQ)/$(TOOLS_DIR)/bin/clitheme export --bash 2>/dev/null)
else
override CLITHEME_EXPORT := $(value CLITHEME_EXPORT)
endif
export CLITHEME_EXPORT
# Vorspann für $(shell) mit einem Werkzeug aus .tools/: $(shell $(TOOL_ENV); befehl). GNU Make
# vor 4.4 (macOS: 3.81) gibt das exportierte PATH nicht an $(shell) weiter, und das BASH_ENV
# von help, info und hints gehört nicht in die Werkzeuge.
TOOL_ENV = unset BASH_ENV; PATH=$(WORKSPACE_SQ)/$(TOOLS_DIR)/bin:"$$PATH"

# Python für die .venv: python3 aus dem PATH, ein gesetztes PYTHON_BOOTSTRAP geht vor. Python ist
# Voraussetzung; das Makefile sucht kein passendes (makefile-conventions, „Python für die .venv“).
# Interpreter und Mindestversion (requires-python in pyproject.toml) setzt make selbst ein,
# PYTHON_BOOTSTRAP gequotet. PYTHON_MINIMUM ist leer, wenn die Zeile nicht ">=X.Y" lautet.
PYTHON_BOOTSTRAP_SQ := '$(subst ','\'',$(or $(PYTHON_BOOTSTRAP),python3))'
PYTHON_MINIMUM := $(shell sed -nE 's/^requires-python *= *">= *([0-9]+\.[0-9]+)".*/\1/p' pyproject.toml)
# Argumente für ein Python: gibt X.Y aus und endet mit Exit 1, wenn es älter als PYTHON_MINIMUM ist.
PYTHON_AT_LEAST = -c 'import sys; v = sys.version_info[:2]; print("%d.%d" % v); \
	sys.exit(v < tuple(map(int, sys.argv[1].split("."))))' $(PYTHON_MINIMUM)
# Setzt $$py, in derselben Rezeptzeile zu nutzen; zu alt oder fehlend: Abbruch mit Grund.
REQUIRE_PYTHON = py=$(PYTHON_BOOTSTRAP_SQ); found=$$("$$py" $(PYTHON_AT_LEAST) 2>/dev/null) || { \
	echo "  ✗ Python $(PYTHON_MINIMUM) oder neuer nötig, $$py ist $${found:-nicht installiert}$${found:+ ($$(command -v "$$py"))}: neueres Python installieren oder seinen Ordner im PATH vor /usr/bin stellen" >&2; \
	exit 1; }

# override: Ein `make VENV=…` lenkte das rm -rf im Stempelrezept sonst auf einen anderen Ordner.
override VENV := .venv
PYTEST  := $(VENV)/bin/pytest
# Startet das Python der .venv in der Mindestversion? Falsch auch, wenn der Interpreter-Link ins
# Leere zeigt, etwa nachdem Homebrew das Python entfernt hat, mit dem die .venv angelegt wurde.
VENV_RUNS = $(VENV)/bin/python $(PYTHON_AT_LEAST) >/dev/null 2>&1
# Was setup herstellt und require-setup prüft: Python-Pakete in der .venv, die
# Dashboard-Pakete und die Werkzeuge in .tools/. Eine geänderte Abhängigkeitsdatei macht den
# Stempel veraltet. Der Stempel der .venv trägt die Mindestversion im Namen: Steigt sie, fehlt
# er, require-setup ruft make setup auf, und setup ersetzt eine .venv mit älterem Python.
VENV_STAMP   := $(VENV)/.installed-python$(PYTHON_MINIMUM)
TOOLS_STAMP  := $(TOOLS_DIR)/.installed
SETUP_STAMPS := $(VENV_STAMP) dashboard/node_modules/.installed $(TOOLS_STAMP)

# Ports des Dev-Stacks nennt dev-ports (--port-of NAME) aus ProjectTools; sie stehen dort, wo sie
# beim Start wirken: das Backend mit --port in Procfile.dev, das Dashboard als server.port in
# dashboard/vite.config.ts. Das Makefile legt keine der Dateien selbst aus. Ohne dev-ports
# (vor make setup) nennen info und hints statt der Adresse NO_DEV_PORTS; dev-up holt es dann
# in require-tools über make setup nach. Nur Ziffern werden übernommen; die Werte stehen danach als Zahlen in
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

# Liste der Makefiles unausgewertet über die Umgebung (siehe Kopf).
export HELP_FILES = $(value MAKEFILE_LIST)

# make.lib.sh von CLITheme (samt cli.lib.sh) in jeder Rezeptzeile von help, info und hints; eine
# Rezeptzeile ergibt eine Ausgabezeile. Bash wertet BASH_ENV aus: darum der Verweis auf CLI_LIBS
# statt des Pfads, ein $(…) im Checkout-Pfad bleibt Text. Leer, solange CLITheme fehlt.
help info hints: export BASH_ENV := $${CLI_LIBS:+$${CLI_LIBS}/make.lib.sh}

# Kopf mit Projektname und Version (readProjectVersion aus BashLib), darunter die Targets. Eine
# Beschreibung sagt, was nach dem Target anders ist; den Ablauf beschreibt docs/development.md.
.PHONY: help
help: require-bash-libs ## Alle verfügbaren Befehle anzeigen
	@showMakeTargets "$${PROJECT_NAME} $$(source "$${BASH_LIBS}/version.lib.sh" && readProjectVersion)" $${HELP_FILES}

.PHONY: info
info: require-bash-libs ## Projektpfade, Ports und Werkzeugstand anzeigen
	@printThemeHeading "Umgebung"
	@printThemeValue WORKSPACE        "$${WORKSPACE}"
	@printThemeValue VENV             '$(VENV)'
	@printThemeValue BASH_LIBS        "$${BASH_LIBS:-nicht gefunden (make setup)}"
	@printThemeValue CLI_LIBS         "$${CLI_LIBS:-nicht gefunden (make setup)}"
	@printThemeValue "Dev-Ports"      '$(if $(BACKEND_PORT),$(DASHBOARD_PORT) (Dashboard) · $(BACKEND_PORT) (Backend),$(NO_DEV_PORTS))'
	@printThemeValue "PORT (make up)" "$${PORT}"
	@printThemeHeading "Werkzeuge (.dev-tools.conf.sh)"
	@# devtools status gibt je Werkzeug „  Name  Stand“ aus; Name und Stand gehen einzeln an
	@# printThemeValue, so stehen sie in denselben Spalten wie die Zeilen darüber.
	@set -o pipefail; $(DEV_TOOLS) status 2>/dev/null | while read -r TOOL_NAME TOOL_STATE; do \
		[[ -z "$$TOOL_NAME" ]] || printThemeValue "$$TOOL_NAME" "$$TOOL_STATE"; done || \
		printThemeValue "Stand" "nicht abrufbar: make setup"
	@echo

# Links, URLs und Tipps für den Alltag; das Einrichten beschreibt docs/development.md.
.PHONY: hints
hints: require-bash-libs ## Links, URLs und Tipps für die tägliche Arbeit
	@printThemeHeading "Links"
	@printThemeValue "Repository"      "$${REPO_URL}"
	@printThemeValue "Entwicklerdoku"  "$(if $(filter https://%,$(REPO_URL)),$${REPO_URL}/blob/master/docs/development.md,docs/development.md)"
	@printThemeValue "Letzter Release" "$${RELEASE_TAG}"
	@printThemeValue "Docker Hub"      "https://hub.docker.com/r/$${IMAGE_NAME}"
	@printThemeHeading "URLs nach make dev-up (http://, nicht https)"
	@printThemeValue "Dashboard"           '$(call dev_url,DASHBOARD_PORT,/)'
	@printThemeValue "API"                 '$(call dev_url,BACKEND_PORT,/)'
	@printThemeValue "Swagger"             '$(call dev_url,BACKEND_PORT,/docs)'
	@printThemeValue "Health"              '$(call dev_url,BACKEND_PORT,/health)'
	@printThemeValue "Container (make up)" "http://localhost:$${PORT}/"
	@printThemeHeading "Im Alltag"
	@printThemeValue "Vor dem Commit" "make check"
	@printThemeValue "Einzelne Tests" "make test-backend ARGS='-k name'"
	@printThemeValue "Stack hängt"    "make dev-down; dann make dev-up"
	@printThemeValue "Erster Kurs"    '$(if $(BACKEND_PORT),curl )$(call dev_url,BACKEND_PORT,/quote/IE00B4L5Y983)'
	@printThemeValue "Unraid-Test"    "wget -O /boot/config/plugins/dockerMan/templates-user/stockinfo-test.xml https://raw.githubusercontent.com/MikeMitterer/unraid-templates/master/templates/stockinfo.xml"
	@printThemeHeading "Werkzeuge (Tag und Quelle in .dev-tools.conf.sh)"
	@printThemeValue "Stand zeigen"      "make info"
	@printThemeValue "Auf Stand bringen" "make setup"
	@echo

# ─── Voraussetzungen ──────────────────────────────────────────────────────────

# Bereit: version.lib.sh von BashLib und cli.lib.sh samt make.lib.sh von CLITheme lesbar; aus
# .tools/ zudem in der Mindestversion aus .dev-tools.conf.sh. Von außen gesetzte Ordner
# (BASH_LIBS, CLI_LIBS) prüft es nur auf Lesbarkeit. Die Ordner aus .tools/ fragt es wie der Kopf
# selbst ab: Die Werte von require-bash-libs stehen vor dessen make setup schon fest.
BASHLIB_DIR = $(if $(BASHLIB_FROM_OUTSIDE),"$${BASH_LIBS}","$$("$${WORKSPACE}"/$(TOOLS_DIR)/bin/bashlib-path 2>/dev/null)")
CLILIB_DIR  = $(if $(CLILIB_FROM_OUTSIDE),"$${CLI_LIBS}","$$("$${WORKSPACE}"/$(TOOLS_DIR)/bin/clilib-path 2>/dev/null)")
LIBS_READY  = BASHLIB=$(BASHLIB_DIR); CLILIB=$(CLILIB_DIR); [[ -r "$$BASHLIB/version.lib.sh" && \
	-r "$$CLILIB/cli.lib.sh" && -r "$$CLILIB/make.lib.sh" ]] && \
	{ [[ -n '$(BASHLIB_FROM_OUTSIDE)' ]] || $(DEV_TOOLS) check bashlib >/dev/null 2>&1; } && \
	{ [[ -n '$(CLILIB_FROM_OUTSIDE)' ]] || $(DEV_TOOLS) check clitheme >/dev/null 2>&1; }

# Ohne `##`: Vorbedingung jedes Targets, das BashLib oder die Ausgabe von CLITheme braucht; BashLib
# setzt CLITheme voraus. Fehlt eines oder ist es zu alt, läuft einmal make setup (ohne das
# BASH_ENV von help, info und hints); reicht das nicht, bricht es mit dem Grund ab. Als
# Vorbedingung, nicht als Rezeptzeile: Das Target danach ermittelt BASH_LIBS und CLI_LIBS neu
# (Kopf). Bewusst ohne Theme-Ausgabe: Es meldet gerade, dass sie fehlt.
.PHONY: require-bash-libs
require-bash-libs:
	@$(LIBS_READY) || env -u BASH_ENV $(MAKE) --no-print-directory setup
	@$(LIBS_READY) || { echo "  ✗ BashLib oder CLITheme fehlt oder ist zu alt, auch nach make setup" >&2; \
		if [[ -n '$(BASHLIB_FROM_OUTSIDE)$(CLILIB_FROM_OUTSIDE)' ]]; then \
			echo "    BASH_LIBS oder CLI_LIBS zeigt ins Leere; ohne gelten die aus .tools/: unset BASH_LIBS CLI_LIBS" >&2; \
		else $(DEV_TOOLS) check bashlib; $(DEV_TOOLS) check clitheme; fi; exit 1; }

# Ohne `##`: verlangt ProjectTools in .tools/ in Mindestversion. Fehlt es oder ist es zu alt,
# läuft einmal make setup; reicht das nicht (etwa ein zu alter Tag in .dev-tools.conf.sh),
# nennt devtools den Grund. Mit require-bash-libs, weil die Targets dahinter (dev-up, dev-down,
# push) auch BashLib brauchen.
.PHONY: require-tools
require-tools: require-bash-libs
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
# requirements.txt installiert plugin_api editierbar; dessen Abhängigkeiten und Entry-Points
# kommen nur beim Installieren in die .venv, darum hängt der Stempel auch an
# plugin_api/pyproject.toml. Ein Versionssprung dort installiert mit neu (selten, von Hand
# gehoben); devtools tstamp lohnt dafür nicht (T-154). Hängt auch an .venv/bin/python: Fehlt der
# Link oder zeigt er ins Leere, etwa nachdem Homebrew das alte Python entfernt hat, ist die
# Einrichtung veraltet, auch mit aktuellem Stempel (T-156). Sein Zeitstempel ist der des Pythons
# dahinter; nach einem Update installiert setup die Pakete einmal neu.
$(VENV_STAMP): requirements.txt requirements-dev.txt plugin_api/pyproject.toml $(VENV)/bin/python
	@test -n '$(PYTHON_MINIMUM)' || { echo '  ✗ requires-python in pyproject.toml ist nicht als ">=X.Y" lesbar' >&2; exit 1; }
	@# Ist die .venv ein Link oder startet ihr Python nicht in der Mindestversion, neu anlegen: pip
	@# schriebe sonst ins Ziel des Links. rm -rf entfernt bei einem Link nur den Link, nie sein
	@# Ziel; venv --clear folgte ihm. Scheitert ein Schritt, scheitert das Rezept.
	@[[ ! -L $(VENV) ]] && $(VENV_RUNS) || { $(REQUIRE_PYTHON); \
		[[ ! -e $(VENV) && ! -L $(VENV) ]] || echo '  ⚠ .venv ohne lauffähiges Python ab $(PYTHON_MINIMUM) wird neu angelegt'; \
		rm -rf $(VENV) && "$$py" -m venv $(VENV); }
	@rm -f $(VENV)/.installed $(VENV)/.installed-python*
	@$(VENV)/bin/python -m pip install -q --disable-pip-version-check -r requirements-dev.txt
	@# Git-gepinnte Pakete behalten bei einem neuen Commit oft ihre Version;
	@# pip hält den alten Stand dann für erfüllt. Weicht der installierte Stand
	@# vom Pin ab, wird genau dieses Paket neu installiert.
	@grep -E '^[A-Za-z0-9_.-]+ @ git\+' requirements.txt | while read -r PIN; do \
		$(VENV)/bin/python -m pip freeze | grep -qxF "$$PIN" || \
			$(VENV)/bin/python -m pip install -q --disable-pip-version-check --no-deps --force-reinstall "$$PIN"; \
	done
	@touch "$@"

# Leere Regel: Fehlt .venv/bin/python, ist die Einrichtung veraltet, statt dass make mit „keine
# Regel“ abbricht. Mit Rezept installierte setup erst beim zweiten Aufruf: Der neue Link trüge
# die alte Zeit des Pythons dahinter.
$(VENV)/bin/python: ;

dashboard/node_modules/.installed: dashboard/package-lock.json
	@npm ci --prefix dashboard --no-audit --no-fund
	@touch "$@"

# Werkzeuge auf Quelle und Tag aus .dev-tools.conf.sh nach .tools/; devtools meldet je Werkzeug
# eine Zeile. Mit rechnerlokaler Zuordnung von DevTools kommen sie aus den lokalen Repos.
$(TOOLS_STAMP): .dev-tools.conf.sh
	@$(REQUIRE_STARTER); $(DEV_TOOLS) install
	@touch "$@"

# Ohne Hilfeeintrag: Fehlt die Einrichtung oder ist sie veraltet (ein Stempel fehlt oder ist
# älter als seine Abhängigkeit, auch ein toter Interpreter-Link der .venv; Git-Hooks nicht
# aktiv), läuft make setup; sonst nichts. Eingerichtet wird nur über setup. Braucht kein
# BashLib, das erst mit setup kommt. Der pre-commit-Hook ruft es im Checkout, nicht in seiner
# Kopie des Index: Dort wäre jede Datei neuer als die Stempel.
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
# (ProjectTools) ist Voraussetzung, auch in Procfile.dev: require-tools holt es über make setup
# nach, bevor overmind startet oder beendet wird, und bricht ab, wenn das nicht reicht
# (makefile-conventions).
# Anders als StockPortfolio und Darwin+Finanzen ohne OVERMIND_SKIP_ENV: HOST aus .env erreicht
# uvicorn in Procfile.dev nur, weil overmind .env lädt; das Makefile exportiert HOST nicht.
.PHONY: dev-up
dev-up: require-tools ## Backend und Dashboard laufen im Hintergrund, mit Auto-Reload
	@command -v overmind >/dev/null || { source "$${CLI_LIBS}/cli.lib.sh" && printThemeStatus "✗" "overmind fehlt: brew install overmind tmux" ERR; exit 1; }
	@command -v tmux >/dev/null || { source "$${CLI_LIBS}/cli.lib.sh" && printThemeStatus "✗" "tmux fehlt: brew install tmux" ERR; exit 1; }
	@dev-ports --check
	@# overmind bricht auch ab, wenn der Stack schon läuft oder eine verwaiste .overmind.sock
	@# eines Absturzes liegt; aufräumen kann nur dev-down.
	@overmind start -D -N -f Procfile.dev || { \
		source "$${CLI_LIBS}/cli.lib.sh" && printThemeStatus "⚠" "Nicht gestartet. Läuft der Stack schon: make dev-logs. Nach einem Absturz räumt make dev-down die Reste auf." WARN; \
		exit 1; }
	@source "$${CLI_LIBS}/cli.lib.sh" && printThemeStatus "✓" 'Stack läuft — Backend $(call dev_url,BACKEND_PORT,) · Dashboard $(call dev_url,DASHBOARD_PORT,)  (make dev-logs)' OK

# Räumt nach einem Absturz overmind/tmux DIESES Projekts, eine verwaiste .overmind.sock und
# die Ports aus Procfile.dev und der Vite-Konfiguration auf (dev-ports --kill).
.PHONY: dev-down
dev-down: require-tools ## Dev-Stack gestoppt, Reste nach einem Absturz beseitigt, Ports frei
	-@overmind quit 2>/dev/null || true
	@dev-ports --kill
	@source "$${CLI_LIBS}/cli.lib.sh" && printThemeStatus "✓" "Stack gestoppt" OK

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
quality: require-setup require-bash-libs ## Messbare Grenzen geprüft: Ruff, Modulgröße, doppelter Code
	@source "$${CLI_LIBS}/cli.lib.sh" && printThemeHeading "Ruff: Fehler, Komplexität, Vereinfachungen"
	$(VENV)/bin/ruff check app tests scripts plugin_api
	@source "$${CLI_LIBS}/cli.lib.sh" && printThemeHeading "Pylint: Modulgröße und doppelter Code"
	$(VENV)/bin/python -m pylint app scripts plugin_api/src plugin_api/examples \
		--disable=all --enable=too-many-lines,duplicate-code --score=n
	@source "$${CLI_LIBS}/cli.lib.sh" && printThemeHeading "Bericht, bricht nicht: doppelter Code in Tests"
	@$(VENV)/bin/python -m pylint tests plugin_api/tests \
		--disable=all --enable=duplicate-code --score=n --exit-zero

# Braucht Netz und gehört deshalb nicht zu `check`. Ein Fund bricht den Lauf
# nicht ab (Entscheidung q-11); beide Prüfungen laufen immer.
.PHONY: audit
audit: require-setup require-bash-libs ## Bericht zu Lücken in Abhängigkeiten: pip-audit, npm audit (Netz)
	@source "$${CLI_LIBS}/cli.lib.sh" && printThemeHeading "Python (pip-audit, requirements.txt)"
	-$(VENV)/bin/pip-audit -r requirements.txt
	@source "$${CLI_LIBS}/cli.lib.sh" && printThemeHeading "Dashboard (npm audit, ohne Entwicklungspakete)"
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

# require-bash-libs vorab wie bei dev-up: ohne BashLib scheitern up und down vor docker, nicht
# danach.
.PHONY: up
up: require-bash-libs ## Container mit Dashboard und API läuft auf PORT (Image aus make build)
	-@docker rm -f "$${CONTAINER}" 2>/dev/null || true
	docker run -d --name "$${CONTAINER}" \
		-p "$${PORT}":8000 \
		--env-file .env \
		-e HOST=0.0.0.0 -e PORT=8000 -e DATABASE_PATH=/data/stockinfo.db \
		-v "$${DATA_VOLUME}":/data \
		--restart unless-stopped \
		"$${IMAGE_NAME}":latest
	@source "$${CLI_LIBS}/cli.lib.sh" && printThemeStatus "✓" "Läuft — App http://localhost:$${PORT}/  (zuvor: make build)" OK

.PHONY: down
down: require-bash-libs ## Container gestoppt und entfernt
	-@source "$${CLI_LIBS}/cli.lib.sh" && if docker rm -f "$${CONTAINER}" 2>/dev/null; \
	then printThemeStatus "✓" "Gestoppt" OK; else printThemeStatus "⚠" "Kein Container $${CONTAINER}" WARN; fi

.PHONY: docker-logs
docker-logs: ## Container-Logs live verfolgen
	docker logs -f "$${CONTAINER}"

# docker/build.sh braucht BashLib; ohne sie baut docs/development.md das Image direkt mit
# docker build.
.PHONY: build
build: require-bash-libs ## Geprüftes Image für PLATFORM=x86|arm (Vorgabe x86)
	@docker/build.sh --build "$${PLATFORM}"

# Startet das zuletzt gebaute Image wie ein User ohne Klon (Wegwerf-Container, freier Port an
# 127.0.0.1) und prüft /health und das Dashboard; Ablauf in docker/build.sh --check.
.PHONY: build-check
build-check: require-bash-libs ## Gebautes Image startet, /health ok, Dashboard unter /
	@docker/build.sh --check

.PHONY: push
push: require-tools ## Image und docker/README.md veröffentlicht (TARGET=ghcr|dockerhub|ecr)
	@docker/build.sh --push

# ─── Versionierung ────────────────────────────────────────────────────────────

##@ Versionierung

# Ohne `##`: läuft vor tag-*; richtet BashLib über require-bash-libs bei Bedarf mit make setup
# ein. Die Version steht im Kopf von make help, den letzten Release-Tag nennt make hints; eigene
# Targets version und tags gibt es nicht (versioning-conventions §4).
.PHONY: precheck
precheck: require-bash-libs

# Sprache von CHANGELOG.md, unabhängig von der Locale der Shell (changelog folgt sonst LANG).
# Englisch wie die übrige Doku. Überschreiben: make … CHANGELOG_LANGUAGE=de
CHANGELOG_LANGUAGE ?= en
export CHANGELOG_LANGUAGE

.PHONY: changelog
changelog: require-tools ## CHANGELOG.md aus Release-Tags erstellen (ohne Commit)
	@LANGUAGE="$${CHANGELOG_LANGUAGE}" changelog --generate

# Je Target eine Hilfezeile; showMakeTargets liest nur Zeilen mit einem Target.
.PHONY: tag-major tag-minor tag-patch
tag-major: ## Major-Release, inkompatible Änderung  [MSG="..."]
tag-minor: ## Minor-Release, neue Funktion  [MSG="..."]
tag-patch: ## Patch-Release, Fehlerbehebung  [MSG="..."]

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
