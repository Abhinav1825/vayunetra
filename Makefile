.PHONY: install api web seed migrate test lint

install:        ## install python + web deps
	pip install -r requirements.txt
	cd web && npm install

api:            ## run the FastAPI backend (serves demo fixtures in DEMO_MODE)
	uvicorn api.main:app --reload

web:            ## run the Vite frontend
	cd web && npm run dev

seed:           ## generate the Delhi seed fixture
	python scripts/seed_delhi.py

migrate:        ## apply Supabase migrations (needs SUPABASE_DB_URL)
	psql "$$SUPABASE_DB_URL" -f infra/supabase/migrations/0001_init.sql
	psql "$$SUPABASE_DB_URL" -f infra/supabase/migrations/0002_roles_rls.sql

test:           ## run tests with coverage
	pytest -q --cov=. --cov-report=term-missing

lint:           ## ruff lint
	ruff check .
