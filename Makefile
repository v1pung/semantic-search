.PHONY: dev prod down logs logs-worker logs-all migrate 

## Development (hot-reload, source mounted)
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
logs: ## Tail logs for the app service
	docker compose logs -f app

logs-worker: ## Tail logs for the celery worker
	docker compose logs -f worker

logs-all: ## Tail logs for all services
	docker compose logs -f


## Utilities
migrate: ## Run alembic migrations inside the app container
	docker compose exec app uv run alembic upgrade head

clear-worker-cache: ## Clear .pyc files in the worker container to avoid stale bytecode issues
	docker compose run --user root app/worker find /app/src -name "*.pyc" -delete