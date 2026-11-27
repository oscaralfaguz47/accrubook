.DEFAULT_GOAL := help

COMPOSE := docker compose
BACKEND := $(COMPOSE) exec backend
FRONTEND := npm --prefix frontend
OPENAPI_TOOL := npm --prefix frontend/tools/openapi-typescript
PRE_COMMIT := uv run --project backend --frozen pre-commit

.PHONY: help setup hooks precommit up down restart logs ps migrate makemigrations schema api-types superuser shell test lint format check image smoke-image frontend-install frontend-dev frontend-check frontend-test


help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# --- Environment ------------------------------------------------------------

setup: ## First-time setup: create .env (if missing), build images, install frontend deps
	@test -f .env || (cp .env.example .env && echo "Created .env from .env.example")
	$(COMPOSE) build
	$(MAKE) frontend-install

hooks: ## Install the git pre-commit hook (once per clone, needs uv on the host)
	$(PRE_COMMIT) install

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

schema: ## Regenerate backend/openapi.yaml (the API contract) from the code
	$(BACKEND) python manage.py spectacular --file openapi.yaml --validate --fail-on-warn

api-types: schema ## Regenerate the API contract and the frontend types in one step
	$(FRONTEND) run generate:api

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

precommit: ## Run every pre-commit hook on all files (not just staged ones)
	$(PRE_COMMIT) run --all-files

check: lint test frontend-check frontend-test ## Run everything CI runs (backend + frontend)

# --- Production image -------------------------------------------------------

IMAGE ?= accrubook-backend:local

image: ## Build the production backend image (no dev dependencies)
	docker build --tag $(IMAGE) backend

smoke-image: ## Run the production image against a throwaway PostgreSQL and check /api/health/
	./scripts/smoke-image.sh $(IMAGE)

# --- Frontend ---------------------------------------------------------------

frontend-install: ## Install frontend deps exactly as in package-lock.json
	$(FRONTEND) ci
	$(OPENAPI_TOOL) ci

frontend-dev: ## Start the Vite dev server (http://localhost:5173)
	$(FRONTEND) run dev

frontend-check: ## Check API types are up to date, then lint, format and type check
	$(FRONTEND) run check

frontend-test: ## Run the frontend test suite (Vitest)
	$(FRONTEND) test
