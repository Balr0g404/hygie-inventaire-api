# -----------------------------------------------------------------------------
# Makefile - Hygie Inventaire API (Docker local dev)
# -----------------------------------------------------------------------------

SHELL := /bin/bash

DC ?= docker compose

API_SERVICE ?= hygie-api-1
DB_SERVICE  ?= hygie-db-1

DJANGO_SETTINGS ?= config.settings
DJANGO_TEST_SETTINGS ?= config.settings

PYTEST_ARGS ?=
MANAGE := python manage.py

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z0-9_.-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-24s\033[0m %s\n", $$1, $$2}'

.PHONY: info
info: ## Show docker compose status
	@$(DC) ps

# -----------------------------------------------------------------------------
# Docker lifecycle
# -----------------------------------------------------------------------------

.PHONY: up
up: ## Start containers in background
	@$(DC) up -d

.PHONY: build
build: ## Build images
	@$(DC) build

.PHONY: up-build
up-build: ## Build then start containers
	@$(DC) up -d --build

.PHONY: down
down: ## Stop containers
	@$(DC) down

.PHONY: clean
clean: ## Stop containers and remove volumes (DANGER: deletes DB)
	@$(DC) down -v

.PHONY: logs
logs: ## Follow logs
	@$(DC) logs -f --tail=200

.PHONY: restart
restart: ## Restart containers
	@$(DC) restart

# -----------------------------------------------------------------------------
# Shell / Exec
# -----------------------------------------------------------------------------

.PHONY: sh
sh: ## Open a shell in API container
	@$(DC) exec $(API_SERVICE) bash

.PHONY: dbsh
dbsh: ## Open a mysql shell (requires MYSQL_ROOT_PASSWORD env in container)
	@$(DC) exec $(DB_SERVICE) bash

# -----------------------------------------------------------------------------
# Django / DB
# -----------------------------------------------------------------------------

.PHONY: manage
manage: ## Run a Django management command: make manage cmd="check"
	@$(DC) exec -e DJANGO_SETTINGS_MODULE=$(DJANGO_SETTINGS) $(API_SERVICE) $(MANAGE) $(cmd)

.PHONY: migrate
migrate: ## Apply migrations
	@$(DC) exec -e DJANGO_SETTINGS_MODULE=$(DJANGO_SETTINGS) $(API_SERVICE) $(MANAGE) migrate

.PHONY: makemigrations
makemigrations: ## Create migrations: make makemigrations app=inventory
	@$(DC) exec -e DJANGO_SETTINGS_MODULE=$(DJANGO_SETTINGS) $(API_SERVICE) $(MANAGE) makemigrations $(app)

.PHONY: superuser
superuser: ## Create a superuser
	@$(DC) exec -e DJANGO_SETTINGS_MODULE=$(DJANGO_SETTINGS) $(API_SERVICE) $(MANAGE) createsuperuser

.PHONY: shell
shell: ## Open Django shell
	@$(DC) exec -e DJANGO_SETTINGS_MODULE=$(DJANGO_SETTINGS) $(API_SERVICE) $(MANAGE) shell

.PHONY: run
run: ## Run Django dev server (inside container)
	@$(DC) exec -e DJANGO_SETTINGS_MODULE=$(DJANGO_SETTINGS) $(API_SERVICE) $(MANAGE) runserver 0.0.0.0:8000

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

.PHONY: test
test: ## Run pytest in API container
	@$(DC) exec -e DJANGO_SETTINGS_MODULE=$(DJANGO_TEST_SETTINGS) $(API_SERVICE) pytest $(PYTEST_ARGS)

.PHONY: test-vv
test-vv: ## Run pytest -vv
	@$(MAKE) test PYTEST_ARGS="-vv $(PYTEST_ARGS)"

.PHONY: test-one
test-one: ## Run one test: make test-one t="apps/inventory/tests/test_endpoints.py::test_inventory_crud_endpoints"
	@$(DC) exec -e DJANGO_SETTINGS_MODULE=$(DJANGO_TEST_SETTINGS) $(API_SERVICE) pytest -vv $(t)

.PHONY: test-keepdb
test-keepdb: ## Reuse test DB for speed (if using MySQL test DB)
	@$(DC) exec -e DJANGO_SETTINGS_MODULE=$(DJANGO_TEST_SETTINGS) $(API_SERVICE) pytest --reuse-db $(PYTEST_ARGS)

# -----------------------------------------------------------------------------
# Lint / Format
# -----------------------------------------------------------------------------

.PHONY: ruff
ruff: ## Run ruff linter
	@$(DC) exec $(API_SERVICE) ruff check .

.PHONY: ruff-fix
ruff-fix: ## Run ruff with auto-fix
	@$(DC) exec $(API_SERVICE) ruff check . --fix

.PHONY: format
format: ## Run ruff formatter
	@$(DC) exec $(API_SERVICE) ruff format .

.PHONY: format-check
format-check: ## Check formatting (CI-like)
	@$(DC) exec $(API_SERVICE) ruff format --check .

.PHONY: precommit
precommit: ## Run pre-commit on all files
	@$(DC) exec $(API_SERVICE) pre-commit run --all-files

# -----------------------------------------------------------------------------
# JS tooling (husky/commitlint/semantic-release)
# -----------------------------------------------------------------------------

.PHONY: npm-install
npm-install: ## Install node deps (inside API container if node is available there)
	@$(DC) exec $(API_SERVICE) npm ci

.PHONY: release-dry
release-dry: ## Run semantic-release dry-run (in CI you use GITHUB_TOKEN)
	@$(DC) exec $(API_SERVICE) npx semantic-release --dry-run

# -----------------------------------------------------------------------------
# Convenience shortcuts
# -----------------------------------------------------------------------------

.PHONY: init
init: up ## Init dev environment (containers up)
	@echo "✅ Containers started. Next: make migrate"

.PHONY: check
check: ruff format-check test ## Lint + format-check + tests
	@echo "✅ All checks passed"

.PHONY: reset-db
reset-db: clean up migrate ## Recreate DB from scratch (DANGER: deletes volumes)
	@echo "✅ DB reset complete"
