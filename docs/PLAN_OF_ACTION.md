# VayuNetra — Plan of Action (v3.2)

> **Project:** VayuNetra — AI-Powered Urban Air Quality Intelligence (PS5)
> **Hackathon:** Economic Times AI Hackathon 2026 (2nd Edition)
> **Team:** Omkar · Abhinav · Sejal — **2 agents each · equal volume · equal difficulty** (see §0.1)
> **Source of truth:** [PRD.md](PRD.md) + [ARCHITECTURE.md](ARCHITECTURE.md) (v1.4). **Stage 1 + Stage 2 = the whole PRD** (coverage matrix in §12).

---

## 0. How this plan works (read first)

### Two stages
- **Stage 1 = the literal PS5 scope** — a **complete, submittable, competitive** entry on its own. Finish only Stage 1 → you can submit.
- **Stage 2 = everything in the PRD *above* PS5** — the enhancements (E1–E7, deep models, polish) that push to **#1**.
- **Rule:** never start Stage 2 until Stage 1's Definition of Done is met (core-first discipline).

### The agent split — 2 each (locked)
| Owner | Agents | Note |
|---|---|---|
| **Omkar** | **Agent 1 — Attribution** + **Agent 2 — Forecast** | The **2 main models** for the submission — the AI/ML core (by request). Attribution = the blame map (Innovation hero); Forecast = the beats-persistence headline (Technical hero). |
| **Abhinav** | **Agent 0 — Orchestrator** + **Agent 3 — Enforcement** | The multi-agent backbone + the action engine. |
| **Sejal** | **Agent 4 — Citizen Advisory** + **Agent 5 — Multi-City** | The public-facing + comparative intelligence. |

### Structure: balanced **vertical** ownership
Each person owns their features **end-to-end** (their data → model → API → UI panel). This balances hard-ML and frontend across all three and **maximises independence** — they meet only at the shared contracts + the stage-end Integration Window.

### Independence — the "contracts"
Code against **two seams**, not each other:
1. **Supabase schema** (ARCH §7.2) — the hub: each model/agent **writes** result rows; each UI **reads** them. No direct person-to-person calls.
2. **API contract** (ARCH §11). Plus a **Delhi seed dataset** (Day 1) + **mock JSON / DEMO_MODE fixtures** so each person works alone for days.

### Blocking policy — minimal, pushed to the *end* of each stage
- **During a stage: zero cross-person blocking** — build on seed data + mocks + fixtures.
- **All cross-person wiring is deferred to one stage-end "Integration Window"** — the **only planned blocking point per stage**.
- **Rule:** producer ships a stub/seed first, *or* consumer mocks it and defers real wiring to the Window. Mid-stage syncs are read-only — nobody waits.

### Definition of Done (every task)
Merged · CI green · smoke test · reads/writes agreed schema · README'd · demoable in DEMO_MODE.

---

## 0.1 Workload & difficulty balance (the fairness view)

Tiers: 🔴 **Hard** (deep/novel ML) · 🟡 **Medium** (engineering/integration) · 🟢 **Light** (config/templating).

| | **Omkar** (AI/ML core) | **Abhinav** (engine + backend) | **Sejal** (coverage + product) |
|---|---|---|---|
| **Agents** | A1 Attribution · A2 Forecast | A0 Orchestrator · A3 Enforcement | A4 Advisory · A5 Multi-City |
| 🔴 **Hard ML** | Attribution · Forecast · Dispersion · GNN/TFT | E1 Satellite-CV · E5 Optimiser · E3 what-if | E2 AOD→PM2.5 · E2 downscaling-CNN · E6 CLIP |
| 🟡 **Medium** | CAAQMS+satellite+weather connectors · 2 UI panels | RAG · read-API+auth · deploy/CI · pipelines · validation · enforcement UI | OSM/WorldPop + **mobility/traffic-proxy** connectors · citizen PWA · app-shell · 3 UI panels · E7 engine |
| 🟢 **Light** | model configs · seasonal calendars | fairness audit · CI/keep-alive config | i18n templates · ROI dashboard · deck/video |
| **Roughly** | 4 hard ML + their data + 2 panels | 3 hard ML + broad backend engineering | 3 hard ML + broad product/integration |

**Each person carries ~3–4 hard ML pieces + a comparable build load.** Omkar's lane skews *deepest ML* (his preference — the 2 hero models); Abhinav's skews *backend-engineering breadth*; Sejal's skews *product breadth + coverage ML*. **Honest caveat:** model-difficulty and build-volume aren't the same currency — this can't be equal to the decimal. It's a fair starting point; all-round, so **rebalance live** by actual speed.

**Accepted team decisions (so this isn't re-litigated):**
- Balance is measured **over the whole project, not per-stage.** Because Omkar owns both hero models, **Stage 1 is Omkar-hard** (Attribution + Forecast + Dispersion) while Abhinav & Sejal do medium Stage-1 work and carry the hard ML (E1–E7) in **Stage 2**. Over both stages, hard-ML is ~even (4 / 3 / 3–4). This is intentional — the hero models must come first anyway.
- **Task-count is uneven by design** (Omkar ≈ 8 fewer-but-harder; Abhinav/Sejal ≈ 12–13 more-but-medium). It is **difficulty-weighted fair**, not count-equal.

---

## 1. Phase 0 — Foundation (shared, do FIRST; split evenly)

| # | Task | Owner | Dep |
|---|---|---|---|
| F1 | Monorepo scaffold (ARCH §20) + secrets/.env | Abhinav | — |
| F2 | **Supabase schema + migrations** (all tables — *data contract*) | Abhinav (all review) | — |
| F3 | **API contract** (endpoints + envelope — *app contract*) | Abhinav + Sejal | — |
| F4 | React app shell + MapLibre base map (renders Delhi from **mock JSON**) | Sejal | F3 |
| F5 | H3 utils + ward↔H3 + `config/cities/delhi.yml` | Omkar | F2 |
| F6 | **Delhi seed dataset** loaded to Supabase (everyone has data Day 1) | Omkar | F2,F5 |
| F7 | LangGraph skeleton + stub agent + `evaluate.ipynb` skeleton | Abhinav | F2 |
| F8 | DEMO_MODE fixture format (frozen snapshot JSON shape) | Sejal | F2,F3 |

**Phase 0 exit:** schema live, seed queryable, API shapes agreed, map renders Delhi, agent stub runs → **three independent verticals open.**

---

## 2. STAGE 1 — PS5 Core (the complete, submittable entry)

> All 5 PS5 builds + orchestrator + foundation + UX + deploy + deliverables. **If only this is done, you can submit and compete.**

### 2A. Omkar — Attribution + Forecast (the AI/ML core)
- [ ] **Connectors his models need:** CAAQMS/OpenAQ (hourly + backfill) + **Earth Engine** satellite (Sentinel-5P, MODIS/VIIRS) + **Open-Meteo** weather + seasonal calendars → `measurements`. 🟡 *(indep)*
- [ ] **Dispersion engine** — Gaussian plume + wind-advection of satellite NO₂/AOD → physics features. 🔴 *(indep)*
- [ ] **Agent 1 — Attribution** [MAIN] — chemical-signature priors + satellite + land-use + dispersion → gradient-boosting apportionment + confidence + **SHAP** → `attribution`. 🔴 *(indep; own data + seed)*
- [ ] **Agent 2 — Forecast** [MAIN] — LightGBM (quantile) 24/48/72h on H3; **persistence + climatology baselines side-by-side** → `forecasts`; **backtest → skill score `1 − RMSE_model/RMSE_persistence` (the headline number).** 🔴 *(dep: seed)*
- [ ] **His UI panels:** the **Blame Map** (Deck.gl `H3HexagonLayer` by dominant source + SHAP tooltips) + the **Forecast time-slider** (24–72h + spike alerts), plugged into Sejal's app shell. 🟡 *(dep: F4 shell; components independent)*

### 2B. Abhinav — Orchestrator + Enforcement (+ backend/platform)
- [ ] **Agent 0 — Orchestrator** (LangGraph): typed state, topology, spike gate, `action_traces` latency stamping + `/agent/query`. 🟡 *(dep: F7)*
- [ ] **Agent 3 — Enforcement** — exposure-weighted prioritisation scorer + RAG-cited dossier → `enforcement_recs`. 🟡 *(dep: attribution + registry via DB, RAG)*
- [ ] **RAG subsystem** — ingest NCAP/GRAP/CPCB-SPCB + health-breakpoint corpus → embed (local `bge-small`) → `kb_chunks`; cited retrieval (serves enforcement + advisory). 🟡 *(indep)*
- [ ] **Read-API + auth** — FastAPI serving `/cities`, `/aqi`, `/attribution`, `/forecast`, `/enforcement`, `/enforcement/{id}/dossier`, `/advisory`, `/live` from Supabase + Supabase Auth/roles. 🟡 *(dep: F3; reads tables — decoupled)*
- [ ] **Pipelines** (GitHub Actions cron) + **deployment** (Vercel + Cloud Run + Supabase) + CI + keep-alive. 🟡 *(dep: thin slice exists — end of stage)*
- [ ] **His UI panel:** enforcement **worklist + dossier view** (cited → "Generate Notice / PDF"). 🟡 *(dep: /enforcement)*
- [ ] **Validation harness / `evaluate.ipynb`** — attribution vs SAFAR/TERI; forecast RMSE vs persistence+climatology (plots); enforcement CPCB/GRAP rubric; latency. 🟡 *(dep: outputs via DB)*

### 2C. Sejal — Advisory + Multi-City (+ app shell & product)
- [ ] **Connectors:** OSM (roads, land use, industrial, hospitals/schools) + WorldPop (population) + emission-source registry → static layers / `emission_sources`. 🟡 *(indep)*
- [ ] **Mobility feeds** (PS5-named) — GTFS transit + a time-of-day/day-of-week **traffic proxy** built from the OSM road network → mobility feature in `measurements` (consumed by Omkar's attribution + forecast via DB). 🟡 *(indep)*
- [ ] **Agent 4 — Advisory** — health tiering (CPCB/WHO breakpoints × vulnerability) + LLM (Gemini) localisation **hi/en/kn/mr** → `advisories`; deliver via **Citizen PWA + Telegram + IVR + public display**. 🟡 *(dep: forecast + vulnerability via DB)*
- [ ] **Agent 5 — Multi-City** — cross-city trends + before/after intervention deltas + H3 signature matching → playbook recs. 🟡 *(dep: multi-city data via DB)*
- [ ] **App shell + integration** — React/Vite/Tailwind shell, routing, state (TanStack+Zustand), map base, WebSocket; **integrates the others' UI panels**. 🟡 *(dep: F4)*
- [ ] **Her UI panels:** **city switcher**, **comparative tab**, **latency widget**, Citizen PWA, language toggle. 🟡
- [ ] **DEMO_MODE wiring** in the app (one flag → offline) + **deliverables**: architecture diagram, deck, demo video, demo script (all contribute slides/metrics). 🟡/🟢
- [ ] **Multi-city data** — add `bengaluru.yml` + `mumbai.yml` configs (city-agnostic ingestion runs them). 🟢 *(coordinated with Omkar's connectors)*

### ✅ Stage 1 — Definition of Done (submittable)
- [ ] 3 cities live, switchable · blame map w/ confidence · **forecast beats persistence (number reported)** · enforcement worklist → cited dossier → notice/PDF · advisory in **4 languages** (app+Telegram+IVR) · **DEMO_MODE** offline · deployed URL · **architecture diagram + deck + demo video** · `evaluate.ipynb` regenerates every Stage-1 metric.
→ **A complete PS5 submission. You can stop here and compete.**

---

## 3. STAGE 2 — Above-PS Enhancements (the #1 push)

> Strictly additive. **Cut order if short: E4 → E6 → E7-deep → GNN → (PINN never).**

### 3A. Omkar — Forecast depth (Stage 2)
- [ ] **GNN/TFT forecast upgrade** over LightGBM — adopt only if it beats the baseline more. 🔴 *(Colab/Kaggle GPU)*
- [ ] **Forecast + dispersion hooks for E3** — expose the counterfactual interface Abhinav's what-if consumes (via DB/API). 🟢
- [ ] **Attribution v2 polish** — calibrate confidence + refine SHAP for the demo. 🟡
*(Omkar's Stage 2 is intentionally light — his Stage 1 carries the two hero models.)*

### 3B. Abhinav — Satellite-CV, optimiser & rigour (Stage 2)
- [ ] **E1 — Satellite CV** (data + model): Sentinel-2 tiles + labels → **CNN/segmentation** → construction/kiln/burn detections → `emission_sources` (`cv_detected`); feeds his enforcement. 🔴 *(Kaggle GPU)*
- [ ] **E3 — What-if simulator** engine (counterfactual over Omkar's forecast + dispersion, read via DB) → `/simulate`. 🔴 *(dep: forecast/dispersion outputs — mockable)*
- [ ] **E5 — Prescriptive optimiser** (greedy/knapsack over E3) → `/optimize`, top-3 ranked packages under inspector-budget. 🔴 *(dep: E3)*
- [ ] **E4 — Spike/anomaly detector** (STL + isolation-forest/autoencoder) → proactive enforcement queue. 🟡 *(stretch)*
- [ ] **Quantified fairness audit** (partial corr priority vs ward income | pollution+exposure ≈ 0) + **`evaluate.ipynb` v2**. 🟡
- [ ] **Live multi-city onboarding** (`POST /admin/cities`) → 4th city on stage. 🟡

### 3C. Sejal — Dense coverage, evidence & impact (Stage 2)
- [ ] **E2 — Dense-coverage** (data + 2 models): **AOD→PM2.5 regressor** + **1km downscaling CNN** → full-city field + "stations↔dense" toggle. 🔴🔴 *(Kaggle GPU)*
- [ ] **E6 — Multimodal evidence**: CLIP-embed Sentinel-2 patches → `kb_chunks(modality='image')`; **dossier shows the satellite patch** + PDF export. 🔴/🟡 *(dep: E1 detections)*
- [ ] **E7 — Health & carbon** (engine + UI): cited dose-response + emission factors → ₹/cases/CO₂e **cards** + **City ROI dashboard** (₹/yr + CO₂e → NCAP funding). 🟡/🟢
- [ ] **What-if + optimiser UI panels** (toggles, sliders, ranked package cards) + **SHAP/Fairness panels** + **detected-sources toggle**. 🟡 *(dep: /simulate, /optimize)*
- [ ] **Deck + video v2** — add optimiser, satellite-evidence, ₹/lives/CO₂e; final dry-run. 🟢/🟡

### ✅ Stage 2 — Definition of Done
- [ ] CV-detected sources auto-populate enforcement · "stations↔dense 1km" works · what-if **and** optimiser run live with ₹/lives/CO₂e + ranked packages · a dossier shows a real satellite patch · fairness ≈0 + ROI dashboard · all E-features in `evaluate.ipynb` + deck/video; dry-run scores 5/5.

---

## 4. Dependency map & blocking windows

| Dependency | Mitigation (stays parallel) |
|---|---|
| Omkar's models ↔ Sejal's OSM/WorldPop + Abhinav nothing | Omkar seeds his own CAAQMS/satellite/weather; Sejal seeds vulnerability tables Day 1 |
| Abhinav's enforcement needs attribution (Omkar) + registry (Sejal) | both **seed those tables**; Abhinav mocks until Integration Window |
| Sejal's advisory/UI needs forecast (Omkar) | reads `forecasts` table / mock JSON |
| Everyone's UI panel | reads Supabase / mock — never a direct call |
| DEMO_MODE | hand-fixtures during stage; snapshot at the Window |

**Only two blocking windows in the whole project — one at each stage's end.** Everything else is parallel.

---

## 5. Integration checkpoints
1. **End of Phase 0 (setup sync)** — contracts + seed + shells → independent verticals.
2. **Stage-1 mid (async, non-blocking).**
3. **🔗 Stage-1 Integration Window (planned blocking)** — mocks→live, wire end-to-end, DEMO_MODE snapshot, deploy, full PS5 dry-run → **submittable**.
4. **Stage-2 mid (async, non-blocking).**
5. **🔗 Stage-2 Integration Window** — wire E-features, refresh snapshot/deck/video, final dry-run 5/5.

*(Capability-gated, not date-gated.)*

---

## 6. Deliverables checklist (PS5-required)

| Deliverable | Stage 1 | Stage 2 | Lead |
|---|---|---|---|
| Working Prototype | Full PS5 app, deployed + DEMO_MODE | + E1–E7 | All (Sejal integrates) |
| Architecture Diagram | Core multi-agent + geo + RAG | + E-models | Sejal (Abhinav/Omkar accuracy) |
| Presentation Deck | Problem→blame→forecast→action→multi-city→impact | + optimiser/evidence/ROI | Sejal (all metrics) |
| Demo Video | ≤3 min PS5 narrative | + wow features | Sejal |

---

## 7. Judging-criteria ownership

| Criterion (weight) | Delivered by | Stage |
|---|---|---|
| **Innovation (25%)** | Blame map (Omkar) · optimiser (Abhinav) · multimodal evidence (Sejal) | 1+2 |
| **Business Impact (25%)** | Latency (Abhinav) + health/carbon ₹ (Sejal/E7) + India-scale narrative | 1+2 |
| **Technical Excellence (20%)** | Forecast-beats-persistence (Omkar) + multi-agent (Abhinav) + dispersion + validation | 1 |
| **Scalability (15%)** | City-agnostic + H3 + live onboarding (Abhinav) | 1(+2) |
| **User Experience (15%)** | Map-first console (all panels) + multilingual citizen (Sejal) | 1 |

---

## 8. Risk register (own your lane)

| Risk | Owner | Mitigation |
|---|---|---|
| Forecast skill < 25% | **Omkar** | strong met+dispersion features; honest skill + beat climatology; GNN only if it helps |
| Live feed flaky in demo | Abhinav (deploy) + Omkar (data) | **DEMO_MODE** + OpenAQ backfill + pre-warm |
| Scope creep endangers core | All | stage gate; never start Stage 2 before Stage-1 DoD; cut order |
| A panel blocked on a model | All | mock JSON + seeded tables + Integration Window |
| Supabase pause / cold start | Abhinav | keep-alive cron + pre-warm before judging |
| Multi-language awkwardness | Sejal | native-speaker review; short templated messages |
| Attribution / E2 hard to validate | Omkar / Sejal | calibrate to SAFAR/TERI + held-out stations; honest ±15–20% |

---

## 9. Tech stack (all free-tier — ARCH §5)
Python · FastAPI (Cloud Run) · Supabase (Postgres/PostGIS/pgvector/Auth) · Uber H3 · Google Earth Engine · Open-Meteo · LangGraph · Gemini Flash (free) + local `bge-small` · LightGBM→PyTorch (Colab/Kaggle) · React+MapLibre+Deck.gl (Vercel) · Telegram + Twilio-trial · GitHub Actions cron. **Infra cost: ₹0.**

---

## 10. First-week kickoff order
1. **All:** Phase 0 (F1–F8) — contracts + seed + shells.
2. **Omkar:** CAAQMS+satellite+weather live → Attribution + Forecast MVP on seed (the 2 mains). **Abhinav:** Orchestrator + Enforcement + read-API skeleton. **Sejal:** OSM/WorldPop + app shell + advisory + the panel that reads mock/live.
3. **All:** first integration sync → run down each vertical's Stage-1 list independently.

---

## 11. (reserved)

---

## 12. Coverage matrix — *proof nothing in the PRD is dropped*

> Every PRD/Architecture section → Stage + Owner. **Stage 1 + Stage 2 = the whole PRD.**

| PRD / ARCH section | Stage | Owner(s) |
|---|---|---|
| PRD §1–§3 Exec / Problem / Thesis | 1 | Sejal (deck) |
| PRD §4 Goals & Metrics | 1 | Abhinav (validation) + all |
| PRD §5 Win Strategy / Why-#1 | 1 | Sejal (deck) + all |
| PRD §6 Personas | 1 | Sejal |
| PRD §7 Product Scope | 1+2 | this plan |
| PRD §8 Agent 0 Orchestrator | 1 | **Abhinav** |
| PRD §8 Agent 1 Attribution | 1 | **Omkar** [MAIN] |
| PRD §8 Agent 2 Forecast | 1 | **Omkar** [MAIN] |
| PRD §8 Agent 3 Enforcement | 1 | **Abhinav** |
| PRD §8 Agent 4 Citizen Advisory | 1 | **Sejal** |
| PRD §8 Agent 5 Multi-City | 1 | **Sejal** |
| PRD §8 ⚡ E1 Satellite CV | 2 | **Abhinav** |
| PRD §8 ⚡ E2 Dense-coverage | 2 | **Sejal** |
| PRD §8 ⚡ E3 What-if | 2 | **Abhinav** (engine) + Sejal (UI) |
| PRD §8 ⚡ E4 Spike (stretch) | 2 | Abhinav |
| PRD §8 ⚡ E5 Optimiser | 2 | **Abhinav** (engine) + Sejal (UI) |
| PRD §8 ⚡ E6 Multimodal evidence | 2 | **Sejal** |
| PRD §8 ⚡ E7 Health & carbon + ROI | 2 | **Sejal** |
| PRD §9 System Architecture | 1 | all (diagram: Sejal) |
| PRD §10 Technology Stack | 1 | all |
| PRD §11 Data Sources (incl. **mobility feeds**) | 1 | Omkar (CAAQMS/satellite/weather) · Sejal (OSM/WorldPop/registry/**mobility**) |
| PRD §12 12.1 attribution / 12.2 forecast / 12.3 dispersion | 1 | **Omkar** |
| PRD §12 12.4 enforcement | 1 | Abhinav |
| PRD §12 12.5 advisory / 12.6 multi-city | 1 | Sejal |
| PRD §12 12.7 E1 | 2 | Abhinav |
| PRD §12 12.8 E2 / 12.14 E6 / 12.15 E7 | 2 | Sejal |
| PRD §12 12.9 E3 / 12.10 E4 / 12.13 E5 | 2 | Abhinav |
| PRD §12 12.0 model/training overview / 12.11 responsible-AI / 12.12 training-compute | 1 | Abhinav (+ all train) |
| PRD §13 Validation | 1(+2) | Abhinav |
| PRD §14 UX / Product Design | 1 | Sejal (shell) + each owns their panel |
| PRD §15 Scalability / Multi-City | 1(+2) | Abhinav (onboarding) + Sejal (A5) |
| PRD §16 Roadmap / §17 Team | — | this plan |
| PRD §18 Risks | 1+2 | all (§8) |
| PRD §19 Deliverables & Demo | 1(+2) | Sejal + all |
| PRD §20 Business Impact & GTM | 1(+E7) | Sejal + Abhinav |
| PRD §21 Appendix | ref | all |
| ARCH §1–2 Constraints & Guiding principles | 0/1 | all (₹0 · city-agnostic · physics+ML — design discipline) |
| ARCH §3–4 C4 diagrams | 1 | all (Sejal renders) |
| ARCH §5 Stack / §6 H3 | 1 | Omkar (H3) + all |
| ARCH §7 Data architecture (schema/pipelines) | 0/1 | Abhinav (schema) + Omkar (H3) + all connectors |
| ARCH §8 Multi-agent layer | 1 | Abhinav (orchestrator) + each agent owner |
| ARCH §9 ML 9.1 attribution / 9.2 forecast / 9.3 dispersion | 1 | **Omkar** |
| ARCH §9 9.4 model-ops / 9.9 training-compute / 9.10 responsible-AI | 1 | Abhinav (+ all train on Colab/Kaggle) |
| ARCH §9 9.5 E1 / 9.7 E3 / 9.8 E4 / 9.11 E5 | 2 | Abhinav (E1, E3, E4, E5) |
| ARCH §9 9.6 E2 / 9.12 E6 / 9.13 E7 | 2 | Sejal |
| ARCH §10 RAG (text) / (multimodal) | 1 / 2 | Abhinav (text) · Sejal (E6 image) |
| ARCH §11 API (reads) / (agent-exec) / (/simulate) / (/optimize) | 1 / 1 / 2 / 2 | Abhinav (reads, agent-exec, /simulate, /optimize) |
| ARCH §12 Frontend | 1 | Sejal (shell) + each owns their panel |
| ARCH §13 Citizen channels | 1 | Sejal |
| ARCH §14 Validation harness | 1+2 | Abhinav |
| ARCH §15 Deployment & CI/CD | 1 | Abhinav |
| ARCH §16 Security/Auth/Roles | 1 | Abhinav + Sejal |
| ARCH §17 Observability/latency | 1 | Abhinav (traces) + Sejal (widget) |
| ARCH §18 Scalability mechanics | 1(+2) | Abhinav |
| ARCH §19 NFRs / §22 Free-tier limits | 1 | all / Abhinav |
| ARCH §20 Repo structure | 0 | Abhinav |
| ARCH §21 Sequence flows | 1 | Abhinav |
| ARCH §23 Build order / §24 Open decisions | 1+2 | this plan / per topic |

→ **Every PRD + Architecture section is assigned to a stage and an owner. Nothing is dropped.**

---

*Plan of Action v3.2 — 2 agents each (Omkar: Attribution + Forecast = the 2 main models / AI-ML core; Abhinav: Orchestrator + Enforcement; Sejal: Advisory + Multi-City + mobility). Balanced over the whole project for difficulty-weighted volume (§0.1). Two blocking windows only. Stage 1 = a complete submittable PS5 entry; Stage 1 + Stage 2 = the entire PRD. v3.1 added mobility feeds (Sejal) + documented the accepted project-level balance. v3.2 fixes seasonal-calendar ownership (→ Omkar), adds the `/enforcement/{id}/dossier` read-endpoint, and closes the coverage-matrix gaps (ARCH §1–2 / §9.9; PRD §12.0 / §12.11 / §12.12) so the "nothing dropped" claim is literally true.*
