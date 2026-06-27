.PHONY: install api web seed migrate test lint

install:        ## install lean python (CPU, no CUDA) + web deps
	pip install -r requirements.txt
	cd web && npm install

install-ml:     ## heavy ML stack — CPU PyTorch + transformers (only if you need local embeddings/training)
	pip install torch --index-url https://download.pytorch.org/whl/cpu
	pip install -r requirements-ml.txt

api:            ## run the FastAPI backend (serves demo fixtures in DEMO_MODE)
	uvicorn api.main:app --reload

web:            ## run the Vite frontend
	cd web && npm run dev

seed:           ## generate the Delhi seed fixture
	python scripts/seed_delhi.py

link:           ## link the local repo to the remote Supabase project (one-time)
	npx supabase link --project-ref dwqjqpohgkxekqilhotr

migrate:        ## push migrations (schema + RLS + city seed) to the linked project
	npx supabase db push

db-status:      ## show which migrations are applied vs pending
	npx supabase migration list

test:           ## run tests with coverage
	pytest -q --cov=. --cov-report=term-missing

lint:           ## ruff lint
	ruff check .
