SHELL := /bin/bash

.DEFAULT_GOAL := help

WORKSPACE    := $(realpath $(shell pwd))
PROJECT_NAME := $(notdir $(WORKSPACE))

-include .env
export

include ${DEV_MAKE}/colours.mk
include ${DEV_MAKE}/tools.mk

VENV    := .venv
UVICORN := $(VENV)/bin/uvicorn

APP_MODULE ?= app.main:app
HOST       ?= 0.0.0.0
PORT       ?= 8000
PID_FILE   := $(VENV)/uvicorn.pid
LOG_FILE   := uvicorn.log

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
	    /^[^#]/ { printf "$(THEME_INDENT_TARGET)$(THEME_COLOR_TARGET)%-12s $(THEME_COLOR_DESC)%s$(RESET)\n", $$1, $$2 }'
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

# ─── Docker ───────────────────────────────────────────────────────────────────

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
