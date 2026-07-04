# VayuNetra — AI-Powered Urban Air Quality Intelligence

> *"We don't just measure the air. We trace it, predict it, and act on it."*
> PS5 · Economic Times AI Hackathon 2026 · City-agnostic multi-agent platform · **₹0 / free-tier**.

A multi-agent **action engine** that fuses CAAQMS ground sensors, Sentinel-5P/MODIS satellite,
mobility feeds, weather, and land use into: **source attribution → hyperlocal forecast →
enforcement intelligence → citizen advisory → multi-city comparison.**

## 📚 Docs (read in this order)
1. [docs/PRD.md](docs/PRD.md) — product requirements (the "what" and "why")
2. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — buildable blueprint (the "how")
3. [docs/PLAN_OF_ACTION.md](docs/PLAN_OF_ACTION.md) — two-stage plan, 2 agents each
4. **Your checklist:** [Omkar](docs/TASKS_OMKAR.md) · [Abhinav](docs/TASKS_ABHINAV.md) · [Sejal](docs/TASKS_SEJAL.md)
5. [docs/API_CONTRACT.md](docs/API_CONTRACT.md) — the app contract everyone codes against

## 👥 Ownership (2 agents each)
| Person | Agents | Lane |
|---|---|---|
| **Omkar** | A1 Attribution · A2 Forecast | AI/ML core (the 2 hero models) + dispersion |
| **Abhinav** | A0 Orchestrator · A3 Enforcement | multi-agent backbone + backend/platform + RAG |
| **Sejal** | A4 Advisory · A5 Multi-City | app shell + frontend + channels + mobility |

## 🚀 Quick start
```bash
# 0. Secrets
cp .env.example .env          # fill keys; keep DEMO_MODE=true to run offline first

# 1. Database (the data contract) — push migrations via the Supabase CLI
npx supabase login                                   # one-time (browser)
npx supabase link --project-ref dwqjqpohgkxekqilhotr # one-time (enter DB password)
npx supabase db push                                 # applies schema + RLS + city seed
python scripts/seed_delhi.py --push                  # synthetic Delhi measurements

# Optional live bootstrap after the live attribution/forecast tables exist
make live-bootstrap                                  # kb_chunks + enforcement_recs + action_traces

# 2. API (serves demo fixtures in DEMO_MODE — works with zero live deps)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt        # lean, CPU-only (no CUDA)
# need local embeddings (RAG/CLIP) or local training? add the heavy stack:
#   make install-ml   (installs CPU PyTorch + transformers — GPU training is on Colab/Kaggle)
uvicorn api.main:app --reload          # -> http://localhost:8000/health

# 3. Web (Sejal owns the app shell)
cd web && npm install && npm run dev    # -> http://localhost:5173
```

## 🗂 Repo layout (ARCHITECTURE.md §20)
```
connectors/  core/{spatial,schemas,config/cities}  ml/{attribution,forecast,dispersion,
vision,coverage,simulator,impact,anomaly}  agents/  rag/  api/  web/  channels/  eval/
demo/  supabase/migrations/  infra/workflows/  .github/workflows/  tests/  docs/
```
*Adding a city = drop a `core/config/cities/<city>.yml`. That's the scalability story in one folder.*

## 🔑 The two seams (so nobody blocks anybody)
1. **Supabase schema** ([20260627000001_init.sql](supabase/migrations/20260627000001_init.sql)) — models/agents **write** rows, UIs **read** them.
2. **API contract** ([API_CONTRACT.md](docs/API_CONTRACT.md)) — `{success, data, error, meta}` envelope.

Work against seed data + `demo/fixtures/*` until the stage-end **Integration Window**. ₹0 infra throughout.
