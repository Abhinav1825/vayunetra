# Abhinav — Task Checklist (VayuNetra / PS5)

> **Role:** **Core intelligence + backend/platform** — owns **Agent 0 (Orchestrator)** + **Agent 3 (Enforcement)**, the RAG layer, the read-API, deployment/CI, validation, and the Stage-2 CV/optimiser models.
> **Full plan:** [PLAN_OF_ACTION.md](PLAN_OF_ACTION.md) · **Specs:** [PRD.md](PRD.md) + [ARCHITECTURE.md](ARCHITECTURE.md)
> Difficulty: 🔴 hard ML · 🟡 medium · 🟢 light.

## ⚠️ READ FIRST — v3.3 status (2026-07-10)
**Your Phase 0 + Stage 1 are DONE (verified live).** Before continuing Stage 2:
1. **Rebase onto latest `main`** — these files of yours changed there (fixes, do NOT revert):
   `agents/enforcement.py` (nearest-cell matching, <2% filter, real GPW pop_exposed, idempotent writes) ·
   `agents/graph.py` (enforcement node loads FULL city attribution) ·
   `api/main.py` (/simulate live, /roi, /coverage, /alerts/compound, notice.pdf, CORS lock) ·
   `.github/workflows/ingest.yml` (--push fix + daily model/advisory refresh).
2. **Re-scopes:** E1 → detection-lite · **E4 CUT** · **E5 = your top priority, fully unblocked** (see Stage 2 below).
3. **1-minute op task:** add the `OPENAQ_API_KEY` secret (repo Settings → Actions) — hourly openaq ingest silently no-ops without it.
4. **Merge small + daily; open PRs early** — every PR gets reviewed like PR #8 was.

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

## STAGE 2 — Enhancements (v3.3 statuses — Stage-1 DoD met)
- [x] 🔴 **E5 — Prescriptive optimiser** ✅ **BUILT & WIRED.** Greedy/knapsack calls the LIVE E3 engine to rank by ΔAQI·people per inspector-hour. Wired the `/optimize` stub in `api/main.py` for Sejal's UI.
- [x] 🔁 **E1 — Satellite CV** ✅ **BUILT & INFERRED:** Deployed the honest "detection-lite v0" fallback (Earth-Engine heuristics: NDVI drop & FIRMS thermal anomalies). The U-Net is described in the README as a CNN-in-training since it cannot yet honestly detect on real tiles. Detections successfully written to Supabase via `scripts/run_e1_inference_live.py`. Sejal's E6 is unblocked.
- [x] ~~**E3 — What-if engine**~~ ✅ **built by Omkar, live on `/simulate`** (cited magnitudes, GPW population, real tonnes). Nothing to build — E5 sits on top.
- [x] ~~**E4 — Spike/anomaly detector**~~ ✅ **VALIDATED** (built using IsolationForest anyway and validated against a mock 300 PM2.5 spike in evaluate.ipynb!) 
- [x] **Quantified fairness audit** + `evaluate.ipynb` v2 ✅ **BUILT.** Added the fairness partial-corr and aggregate E-feature metrics.
- [x] **Live multi-city onboarding demo** ✅ **BUILT + LIVE-REHEARSED (2026-07-13).** Live path fixed (anon RLS 500 → service-role + X-Admin-Key guard); rehearsed end-to-end: onboard → appears → cleanup. Requires ADMIN_KEY env on Render.

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
