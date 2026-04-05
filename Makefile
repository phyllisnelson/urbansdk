.PHONY: run build up down restart logs migrate ingest shell test unit-tests integration-tests coverage lint format notebook install

# ── Local dev (no Docker) ─────────────────────────────────────────────────────
run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ── Docker ────────────────────────────────────────────────────────────────────
build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart app

logs:
	docker compose logs -f app

# ── Database ──────────────────────────────────────────────────────────────────
migrate:
	docker compose exec app python -m app.ingest --migrate

ingest:
	docker compose exec app python -m app.ingest

# ── Utilities ─────────────────────────────────────────────────────────────────
shell:
	docker compose exec app bash

test:
	docker compose exec app pytest tests/ -v --cov=app --cov-report=term-missing

unit-tests:
	docker compose exec app pytest tests/ -v --ignore=tests/integration --cov=app --cov-report=term-missing

integration-tests:
	docker compose exec app pytest tests/integration/ -v

coverage:
	docker compose exec app pytest tests/ --ignore=tests/integration --cov=app --cov-report=term-missing --cov-fail-under=100

lint:
	docker compose exec app flake8 app tests
	docker compose exec app isort --check-only app tests

format:
	docker compose exec app black app tests
	docker compose exec app isort app tests

JUPYTER := $(shell pip3 show jupyter 2>/dev/null | grep ^Location | awk '{print $$2}' | sed 's|lib/python.*/site-packages|bin|')/jupyter

install:
	pip3 install -q -r requirements.local.txt

notebook: install
	$(JUPYTER) notebook notebook.ipynb
