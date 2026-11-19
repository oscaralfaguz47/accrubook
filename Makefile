.DEFAULT_GOAL := help

COMPOSE := docker compose
BACKEND := $(COMPOSE) exec backend

.PHONY: help setup up down restart logs ps migrate makemigrations superuser shell test lint format check

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# --- Environment ------------------------------------------------------------

setup: ## First-time setup: create .env (if missing) and build images
	@test -f .env || (cp .env.example .env && echo "Created .env from .env.example")
	$(COMPOSE) build

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

makemigrations: ## Create new migrations from model changes
	$(BACKEND) python manage.py makemigrations

superuser: ## Create a Django admin superuser
	$(BACKEND) python manage.py createsuperuser

shell: ## Open a Django shell
	$(BACKEND) python manage.py shell

# --- Quality ----------------------------------------------------------------

test: ## Run the backend test suite
	$(BACKEND) pytest

lint: ## Check linting and formatting (no changes)
	$(BACKEND) ruff check .
	$(BACKEND) ruff format --check .

format: ## Auto-fix lint issues and format code
	$(BACKEND) ruff check --fix .
	$(BACKEND) ruff format .

check: lint test ## Run everything CI runs