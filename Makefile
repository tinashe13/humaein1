SHELL := bash

.PHONY: dev backend frontend test lint seed

dev: ## Run backend (uvicorn) and frontend (vite) via docker-compose
	docker compose -f app/ops/compose.yml up --build

backend: ## Run backend locally (development)
	cd app/backend && poetry install && poetry run python -m app.devserver

frontend: ## Run frontend locally
	cd app/frontend && pnpm install && pnpm dev

test: ## Run tests
	cd app/backend && poetry run pytest -q

lint: ## Lint & typecheck
	cd app/backend && poetry run ruff check . && poetry run black --check . && poetry run mypy app

seed: ## Seed sample data
	cd app/backend && poetry run python -m app.scripts.seed

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'



