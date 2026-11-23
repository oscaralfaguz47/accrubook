.DEFAULT_GOAL := help

COMPOSE := docker compose
BACKEND := $(COMPOSE) exec backend
FRONTEND := npm --prefix frontend

.PHONY: help setup up down restart logs ps migrate makemigrations superuser shell test lint format check frontend-install frontend-dev frontend-check

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# --- Environment ------------------------------------------------------------

setup: ## First-time setup: create .env (if missing), build images, install frontend deps
	@test -f .env || (cp .env.example .env && echo "Created .env from .env.example")
	$(COMPOSE) build
	$(FRONTEND) ci

up: ## Start all services in the background
	$(COMPOSE) up -d

down: ## Stop all services
	$(COMPOSE) down

restart: ## Recreate all services (picks up .env changes)
	$(COMPOSE) down
	$(COMPOSE) up -d

logs: ## Follow logs of all services
	$(COMPOSE) logs -f

ps: ## List running services
	$(COMPOSE) ps

# --- Django -----------------------------------------------------------------

migrate: ## Apply database migrations
	$(BACKEND) python manage.py migrate

makemigrations: ## Create new migrations from model changes (and format them)
	$(BACKEND) python manage.py makemigrations
	$(BACKEND) ruff format .

superuser: ## Create a Django admin superuser
	$(BACKEND) python manage.py createsuperuser

shell: ## Open a Django shell
	$(BACKEND) python manage.py shell

# --- Quality ----------------------------------------------------------------

test: ## Run the backend test suite
	$(BACKEND) pytest

lint: ## Check backend linting and formatting (no changes)
	$(BACKEND) ruff check .
	$(BACKEND) ruff format --check .

format: ## Auto-fix lint issues and format code (backend + frontend)
	$(BACKEND) ruff check --fix .
	$(BACKEND) ruff format .
	$(FRONTEND) run format

check: lint test frontend-check ## Run everything CI runs (backend + frontend)

# --- Frontend ---------------------------------------------------------------

frontend-install: ## Install frontend deps exactly as in package-lock.json
	$(FRONTEND) ci

frontend-dev: ## Start the Vite dev server (http://localhost:5173)
	$(FRONTEND) run dev

frontend-check: ## Lint, format check and type check the frontend
	$(FRONTEND) run check