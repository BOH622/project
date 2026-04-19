.PHONY: help install dev db.up db.down db.migrate db.revision seed test test.backend test.frontend lint format clean

help:
	@echo "install         - Install backend + frontend deps"
	@echo "dev             - Run backend (:8000) + frontend (:5173) locally"
	@echo "db.up           - Start Postgres via docker-compose"
	@echo "db.down         - Stop Postgres"
	@echo "db.migrate      - Apply Alembic migrations"
	@echo "db.revision m=MSG  - Create new Alembic revision"
	@echo "seed            - Seed sample data"
	@echo "test            - Run all tests"
	@echo "test.backend    - Run backend tests"
	@echo "test.frontend   - Run frontend tests"
	@echo "lint            - Lint backend + frontend"
	@echo "format          - Format backend + frontend"

install:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -e '.[dev]'
	cd frontend && npm install

dev:
	@echo "Starting backend + frontend. Ctrl-C to stop both."
	@(cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &) && \
	 (cd frontend && npm run dev)

db.up:
	docker compose up -d postgres

db.down:
	docker compose down

db.migrate:
	cd backend && . .venv/bin/activate && alembic upgrade head

db.revision:
	cd backend && . .venv/bin/activate && alembic revision --autogenerate -m "$(m)"

seed:
	cd backend && . .venv/bin/activate && python -m app.scripts.seed

test: test.backend test.frontend

test.backend:
	cd backend && . .venv/bin/activate && pytest -v

test.frontend:
	cd frontend && npm test

lint:
	cd backend && . .venv/bin/activate && ruff check . && mypy app
	cd frontend && npm run lint

format:
	cd backend && . .venv/bin/activate && ruff format .
	cd frontend && npm run format

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -rf backend/.venv frontend/node_modules frontend/dist
