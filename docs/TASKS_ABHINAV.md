# Abhinav — Task Checklist (VayuNetra / PS5)

> **Role:** **Core intelligence + backend/platform** — owns **Agent 0 (Orchestrator)** + **Agent 3 (Enforcement)**, the RAG layer, the read-API, deployment/CI, validation, and the Stage-2 CV/optimiser models.
> **Full plan:** [PLAN_OF_ACTION.md](PLAN_OF_ACTION.md) · **Specs:** [PRD.md](PRD.md) + [ARCHITECTURE.md](ARCHITECTURE.md)
> Difficulty: 🔴 hard ML · 🟡 medium · 🟢 light.

## How you stay unblocked
- You **own the two contracts** (Supabase schema F2 + API contract F3) — define them early so everyone (including you) is decoupled.
- Your agents/models **write rows to Supabase**; the API **reads rows** — no direct calls to anyone.
- Enforcement needs attribution (Omkar) + registry (Sejal): **work against seeded/mock tables** until the stage-end Window.

---

## Phase 0 — Foundation (do first)
- [x] **F1 — Monorepo scaffold** (ARCH §20) + secrets/.env. 🟡
- [x] **F2 — Supabase schema + migrations** (all tables — *the data contract*; everyone reviews). 🟡
- [x] **F3 — API contract** (endpoints + `{success,data,error,meta}` envelope — with Sejal). 🟡
- [x] **F7 — LangGraph skeleton** + a stub agent (canned output) + `evaluate.ipynb` skeleton. 🟡

---

## STAGE 1 — PS5 core (must-ship)
- [x] **Agent 0 — Orchestrator** (LangGraph): typed shared state, graph topology, spike/hotspot gate, `action_traces` latency stamping, + `/agent/query`. 🟡 *(dep: F7)*
- [x] **Agent 3 — Enforcement** — exposure-weighted prioritisation scorer + RAG-cited dossier → `enforcement_recs`. 🟡 *(dep: attribution + registry via DB — mock until Window)*
- [x] **RAG subsystem** — ingest NCAP/GRAP/CPCB-SPCB + health-breakpoint corpus → semantic chunk → embed (local `bge-small`) → `kb_chunks`; cited retrieval (serves enforcement **and** advisory). 🟡 *(indep)*
- [x] **Read-API + auth** — FastAPI serving `/cities`, `/aqi`, `/attribution`, `/forecast`, `/enforcement`, `/enforcement/{id}/dossier`, `/advisory`, `/live` from Supabase + Supabase Auth/roles (RLS). 🟡 *(dep: F3; reads tables — decoupled)*
- [x] **Pipelines + deployment** — GitHub Actions cron (ingest/forecast/rollup) + deploy (Vercel + Cloud Run + Supabase) + CI + keep-alive ping. 🟡 *(deploy at end of stage)*
- [x] **UI panel** — enforcement **worklist + dossier view** (cited → "Generate Notice / PDF"). 🟡 *(dep: /enforcement)*
- [x] **Validation harness / `evaluate.ipynb`** — attribution vs held-out SAFAR/TERI; **forecast RMSE vs persistence + climatology (with plots)**; enforcement **CPCB/GRAP rubric proxy**; signal-to-action latency. 🟡 *(dep: outputs via DB)*

**Your Stage-1 "done when":** the multi-agent loop runs end-to-end (signal→action <5 min, latency stamped); enforcement produces cited dossiers; the app is **deployed** + reachable; `evaluate.ipynb` regenerates every metric live.

---

## STAGE 2 — Enhancements (only after Stage-1 DoD)
- [x] **E1 — Satellite CV** (data + model): Sentinel-2 tiles + labels → **CNN/segmentation (transfer-learned)** → construction/kiln/burn detections → `emission_sources` (`source_origin='cv_detected'`); feeds your enforcement. 🔴 *(Kaggle GPU)*
- [x] **E3 — What-if simulator** engine (counterfactual over Omkar's forecast + dispersion, read via DB) → `/simulate`. 🔴 *(dep: forecast/dispersion outputs — mockable)*
- [x] **E5 — Prescriptive optimiser** (greedy / priority-knapsack over E3) → `/optimize`, **top-3 ranked intervention packages under an inspector-hour budget**. 🔴 *(dep: E3)*
- [x] **E4 — Spike/anomaly detector** (STL + isolation-forest/autoencoder) → proactive enforcement queue. 🟡 *(stretch)*
- [x] **Quantified fairness audit** (partial corr of priority vs ward income | pollution+exposure ≈ 0) + **`evaluate.ipynb` v2** (optimiser-vs-baseline · GNN skill · fairness · aggregates all E-feature metrics: E1 mAP/F1 · E2 RMSE · E6 precision@k · E7 100%-sourced). 🟡
- [x] **Live multi-city onboarding** (`POST /admin/cities`) → onboard a **4th city on stage**. 🟡

**Your Stage-2 "done when":** CV detections feed enforcement; what-if + optimiser run live with ranked packages; fairness ≈0 shown; onboarding demo works.

---

## Your dependencies (all mockable → no mid-stage blocking)
| You need | From | Until then |
|---|---|---|
| Attribution rows (for enforcement) | Omkar | seeded/mock `attribution` rows |
| Emission registry (for enforcement) | Sejal | seeded `emission_sources` |
| Forecast/dispersion (for E3) | Omkar | mock `forecasts` + a stub hook |
| App shell to host your panel | Sejal (F4) | build the panel as a component |

## Your risks to own
- **Live feed flaky in demo** → you own deploy: ship **DEMO_MODE** + pre-warm Cloud Run + OpenAQ backfill.
- **Supabase pause / cold start** → keep-alive cron + unpause/pre-warm 24h before judging.
- **Scope creep** → enforce the stage gate; never start Stage 2 before Stage-1 DoD.

## Quick stack ref
Python · FastAPI (Cloud Run) · LangGraph · Supabase (Postgres/PostGIS/pgvector/Auth) · local `bge-small` · GitHub Actions cron · PyTorch (Kaggle GPU for E1). **₹0.**
