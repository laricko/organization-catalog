
seed_dev:
	PYTHONPATH=. uv run scripts/seed.py


migrate:
	docker exec -i org_catalog_api uv run alembic -c src/infra/alembic.ini upgrade head


psql:
	docker compose exec db psql -U catalog -d catalog


format:
	uv run black src
