.PHONY: dev prod down logs logs-worker logs-all migrate migrate-prod download-model

## Download the embedding model locally before building the prod image
download-model:
	@echo "Downloading embedding model into ./models/ ..."
	uv run python scripts/download_model.py


## Development — hot-reload, source mounted (docker-compose.override.yml auto-loaded)
dev:
	@echo "Starting development server..."
	docker compose up


## Production
prod:
	@echo "Starting production server..."
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d


## Teardown
down:
	docker compose down


## Logs
logs:
	docker compose logs -f app

logs-worker:
	docker compose logs -f worker

logs-all:
	docker compose logs -f


## Migrations
migrate: ## Run alembic migrations inside the running dev app container
	docker compose exec app uv run alembic upgrade head

migrate-prod: ## Run alembic migrations using the prod image (one-shot container)
	docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm migrate


## Utilities
clear-worker-cache: ## Clear .pyc files in the worker container to avoid stale bytecode
	docker compose run --user root worker find /app/src -name "*.pyc" -delete
