.PHONY: run build up down restart logs migrate ingest data-download shell test unit-tests integration-tests coverage lint format notebook install

DATA_DIR := tests/data
LINK_INFO_URL := https://cdn.urbansdk.com/data-engineering-interview/link_info.parquet.gz
SPEED_DATA_URL := https://cdn.urbansdk.com/data-engineering-interview/duval_jan1_2024.parquet.gz
LINK_INFO_PATH := $(DATA_DIR)/link_info.parquet.gz
SPEED_DATA_PATH := $(DATA_DIR)/duval_jan1_2024.parquet.gz

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

ingest: data-download
	docker compose exec app python -m app.ingest

data-download:
	mkdir -p $(DATA_DIR)
	test -f $(LINK_INFO_PATH) || curl -fL "$(LINK_INFO_URL)" -o "$(LINK_INFO_PATH)"
	test -f $(SPEED_DATA_PATH) || curl -fL "$(SPEED_DATA_URL)" -o "$(SPEED_DATA_PATH)"

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
