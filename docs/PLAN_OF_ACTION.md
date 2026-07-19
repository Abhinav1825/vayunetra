# VayuNetra — Plan of Action (v3.3)

> **Project:** VayuNetra — AI-Powered Urban Air Quality Intelligence (PS5)
> **Hackathon:** Economic Times AI Hackathon 2026 (2nd Edition)
> **Team:** Omkar · Abhinav · Sejal — **2 agents each · equal volume · equal difficulty** (see §0.1)
> **Source of truth:** [PRD.md](PRD.md) + [ARCHITECTURE.md](ARCHITECTURE.md) (v1.4). **Stage 1 + Stage 2 = the whole PRD** (coverage matrix in §12).

---

## ⚡ v3.3 — CURRENT STATE + RE-SCOPES (updated 2026-07-10 — READ BEFORE CONTINUING ANY WORK)

**State:** Stage 1 is DONE and live (3 cities, all 6 agents, deployed on Vercel+Render) except the
items listed below. Stage 2 is ~65% done. §2/§3 items below are annotated ✅/⏳/🔁/❌ in place.
**Your personal checklist ([TASKS_OMKAR](TASKS_OMKAR.md) / [TASKS_ABHINAV](TASKS_ABHINAV.md) /
[TASKS_SEJAL](TASKS_SEJAL.md)) carries the same statuses + "if you already started X" instructions — read yours first.**

### 🔴 Critical path (updated 2026-07-19)
1. **DEMO VIDEO (≤3 min)** — the only missing *required* deliverable. Owner: **Sejal** (Omkar records screen flows). Everything else below is ✅.
2. ~~`OPENAQ_API_KEY` secret~~ ✅ **done** (openaq measurements fresh daily).
3. ~~E5 optimiser~~ ✅ **built & live** (`/optimize`, ranked packages in the What-If UI).

### 🔁 Re-scopes (decided 2026-07-10 — reasons in §3 annotations)
- **E1 Satellite CV:** full CNN → **"detection-lite v0"** (Earth-Engine heuristic detector: bare-soil/NDVI change for construction, thermal anomaly for burning → `emission_sources(source_origin='cv_detected')` with honest `detection_confidence`). CNN = cited roadmap. *If you already started the CNN and are >80% done, finish it; otherwise switch.*
- **E4 anomaly detector: CUT** (it was first in the official cut order — decided now so nobody spends time on it).
- **E2 real-data Kaggle run:** downgraded to **stretch** — the shipped method is honestly labeled ("synthetic-field validation"); real-data training is polish.
- **E6 multimodal:** proceed **only after** detection-lite lands (it depends on detections); second in cut order.

### ✅ Built beyond the original plan (DO NOT rebuild — already live on `main`)
OSM emission-source registry w/ daily auto-refresh (replaces hand-seeded) · **GPW v4.11 population per H3 cell**
(supersedes Sejal's WorldPop item) · attribution validated vs SAFAR/CSTEP inventories (cosine 0.92/0.88/0.79,
`evaluate.ipynb §10`) · hybrid GBM+SHAP attribution w/ R²-gate + rush-hour validation (§8) · CQR-calibrated
prediction intervals (§9) · E3 counterfactual engine + live `/simulate` w/ cited intervention magnitudes +
real tonnes-avoided · heat×smog compound alerts (`/alerts/compound` + header badge) · CAQM directive corpus in
RAG · notice PDF export · Telegram+IVR live broadcast (3 numbers) · cold-start insurance + keep-alive cron ·
`scripts/refresh_advisories.py` (advisories auto-refresh daily) · real vulnerability zones (2,366 zones from ~9,900 OSM facilities × GPW pop) · clean-air zones (`/clean-zones` from the E2 field) · QR codes (app + Telegram) · enforcement worklist filters/search · light-mode landing page with the updated architecture diagram.

### ⚠️ Process (this is how we avoid breaking each other)
- **Rebase onto latest `main` before continuing** — `agents/enforcement.py`, `agents/graph.py`, `api/main.py`,
  `ml/coverage/dense_field.py`, `web/src/*` all changed on main (fixes to YOUR files are annotated in your TASKS file — do not revert them).
- **Merge small and daily.** CI is green and guards the repo; a big unmerged drop near the deadline is our likeliest way to lose. Open PRs early — Omkar('s agent) reviews every PR the way PR #8 was audited.

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
- [x] **Connectors his models need** ✅ *(OpenAQ+Open-Meteo+EE live; CPCB connector ready but data.gov.in is down — external, retry only)*
- [x] **Dispersion engine** ✅
- [x] **Agent 1 — Attribution** [MAIN] ✅ *(hybrid GBM+SHAP live in 3 cities, R²-gated, rush-hour-validated 2.30×, inventory-validated 0.92 vs SAFAR)*
- [x] **Agent 2 — Forecast** [MAIN] ✅ *(skill reported honestly; CQR-calibrated intervals)*
- [x] **His UI panels** ✅ *(blame map + SHAP tooltips + forecast slider + cell-story loop)*

### 2B. Abhinav — Orchestrator + Enforcement (+ backend/platform)
- [x] **Agent 0 — Orchestrator** ✅ *(note: enforcement node now loads FULL city attribution — changed on main, don't revert)*
- [x] **Agent 3 — Enforcement** ✅ *(now: per-source nearest-cell matching, <2% filter, real GPW pop_exposed, idempotent writes — all on main)*
- [x] **RAG subsystem** ✅ *(14 kb_chunks incl. 3 CAQM directive docs)*
- [x] **Read-API + auth** ✅ *(+ new: /simulate live, /roi, /coverage, /alerts/compound, notice.pdf)*
- [x] **Pipelines + deployment** ✅ ⚠️ *one op left: add the `OPENAQ_API_KEY` GitHub secret (hourly openaq ingest silently no-ops without it)*
- [x] **His UI panel** ✅ *(worklist + dossier + Notice PDF, cell-focused sort)*
- [x] **Validation harness / `evaluate.ipynb`** ✅ *(now 10 sections: + TFT verdict §7, attribution safeguards §8, CQR §9, inventory validation §10)*

### 2C. Sejal — Advisory + Multi-City (+ app shell & product)
- [x] **Connectors → emission_sources** ✅ 🔁 *(OSM registry now auto-ingests from Overpass daily; **WorldPop item superseded — GPW v4.11 population per cell is live** (`connectors/population.py`) — do NOT build WorldPop)*
- [x] **Mobility feeds** ✅
- [x] **Agent 4 — Advisory** ✅ *(4 languages, app+Telegram+IVR all working; advisories auto-refresh daily via `scripts/refresh_advisories.py` — don't duplicate)*
- [x] **Agent 5 — Multi-City** ✅
- [x] **App shell + integration** ✅
- [x] **Her UI panels** ✅
- [x] **DEMO_MODE wiring** ✅ + diagram ✅ + deck ✅ (v1) — ⏳ **demo video NOT recorded — THE critical-path item**
- [x] **Multi-city data** ✅ *(3 cities fully populated: measurements/attribution/forecasts)*
- [ ] ⏳ *(optional polish, not DoD)* ward boundary GeoJSONs (`wards 0` shows in City Intel)

### ✅ Stage 1 — Definition of Done (submittable)
- [x] ~~everything~~ **except the demo video**: 3 cities ✅ · blame map ✅ · forecast number ✅ · worklist→dossier→PDF ✅ · 4-language advisory (app+Telegram+IVR) ✅ · DEMO_MODE ✅ · deployed URLs ✅ · diagram ✅ · deck ✅ · **demo video ❌ (record it!)** · evaluate.ipynb ✅
→ **A complete PS5 submission. You can stop here and compete.**

---

## 3. STAGE 2 — Above-PS Enhancements (the #1 push)

> Strictly additive. ~~Cut order if short: E4 → E6 → E7-deep → GNN → (PINN never).~~
> **v3.3: E4 is CUT (decided 2026-07-10). GNN evaluated + honestly rejected (§ evaluate.ipynb §7). Next cut if short: E6.**

### 3A. Omkar — Forecast depth (Stage 2) — ✅ COMPLETE
- [x] **GNN/TFT forecast upgrade** ✅ *(evaluated on Colab T4 with identical walk-forward folds — LightGBM won 3/3 horizons → KEPT the baseline per this plan's own rule; recorded in evaluate.ipynb §7 + notebooks/colab_tft_forecast.ipynb)*
- [x] **Forecast + dispersion hooks for E3** ✅ *(went further: the full E3 engine is built — `ml/simulator/counterfactual.py`, live on `/simulate`, with cited intervention magnitudes + GPW population + real tonnes-avoided)*
- [x] **Attribution v2 polish** ✅ *(hybrid GBM+SHAP, R² gate, calibrated confidence, SHAP tooltips)*
- [x] 🆕 **Agent Trace Viewer + "run pipeline live" button** ✅ *(live: `web/src/TraceViewer.tsx` — animated multi-agent timeline + "Run agents live")*

### 3B. Abhinav — Satellite-CV, optimiser & rigour (Stage 2) — ✅ COMPLETE (verified 2026-07-19)
- [x] 🔁 **E1 — detection-lite v0** ✅ *(live: 487 `cv_detected` rows via Earth-Engine heuristics, honest confidence; U-Net = cited CNN-in-training roadmap — PR #14)*
- [x] **E3 — What-if engine** ✅ *(built by Omkar as the "hooks" item — live on /simulate. Nothing to build here; build E5 ON TOP of `ml.simulator.simulate_intervention()`.)*
- [x] 🔴 **E5 — Prescriptive optimiser** ✅ *(live: `ml/simulator/optimizer.py` → `/optimize`, ranked packages in the What-If UI)*
- [x] ❌ **E4 — CUT** (v3.3 decision — IsolationForest built anyway + validated in evaluate.ipynb, not scope)
- [x] **Quantified fairness audit** ✅ *(evaluate.ipynb §11 + REAL live-rec audit surfaced in the UI FairnessPanel — n=390, contribution r=0.95 dominant, no socio-economic inputs by construction)*
- [x] **Live multi-city onboarding demo** ✅ *(rehearsed against production 2026-07-19: forbidden→onboard→appears→cleanup; ADMIN_KEY confirmed on Render; 3-line stage script in ONBOARDING.md)*
- [x] ⚠️ **Op task: `OPENAQ_API_KEY` secret** ✅ *(set — openaq data fresh daily)*
- ⚠️ **Ops note (2026-07-19):** the daily cron once left the worklist EMPTY (OSM refresh cleared recs; spike gate skipped regeneration on a calm day). Fixed: OSM clear is now scoped to OSM-referencing recs + the cron regenerates enforcement **unconditionally** every day.

### 3C. Sejal — Dense coverage, evidence & impact (Stage 2) — ✅ COMPLETE except the video (verified 2026-07-19)
- [x] **E2 — Dense-coverage** ✅ *(AOD→PM2.5 + downscaling CNN + toggle shipped; on main since: lean no-torch fallback + live fields anchor on REAL measurements — rebase, don't revert)*. 🔁 *Real-data Kaggle training = **stretch**, not blocker (shipped version is honestly labeled "synthetic-field validation").*
- [x] 🔁 **E6 — Multimodal evidence** ✅ *(487 image chunks in `kb_chunks`; top rec-referenced sources carry REAL Sentinel-2 RGB composites (`scripts/ingest_e6_real_patches.py`), rest are honestly-labeled markers; live dossiers show the patch — verified on production)*
- [x] **E7 — Health & carbon** ✅ *(cited factors — now incl. WHO AirQ+ + Balakrishnan/Lancet-2019 anchors — ImpactCards + ROI panel live)*
- [x] **What-if UI + SHAP + detected-sources toggle** ✅ · **Fairness panel** ✅ *(live in the impact tab — real audit on n=390 recs)*
- [ ] **Deck ✅ / video ❌** — deck absorbed the validation numbers + optimiser + ₹/lives/CO₂e (`PITCH_DECK.html`); **the ≤3-min video is the LAST remaining deliverable — record at the end against the live site.** 🔴
- [x] 🆕 **Telegram two-way subscribe** ✅ *(webhook registered → production `/telegram/webhook`; `/start` → city picker → subscribe flow proven end-to-end 2026-07-19; `advisory_subscribers` live — judges can subscribe their own phone)*

### ✅ Stage 2 — Definition of Done (status 2026-07-19)
- [x] CV-detected sources auto-populate enforcement ✅ *(390 recs over 547 sources incl. 487 cv_detected)* · "stations↔dense 1km" works ✅ · what-if **and** optimiser run live with ₹/lives/CO₂e + ranked packages ✅ · a dossier shows a real satellite patch ✅ *(verified on production)* · fairness audit + ROI dashboard ✅ · all E-features in `evaluate.ipynb` + deck ✅
- [ ] **video** ❌ + judging-morning **dry-run 5/5** ⏳ — the only two boxes left.

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
Python · FastAPI (Cloud Run) · Supabase (Postgres/PostGIS/pgvector/Auth) · Uber H3 · Google Earth Engine · Open-Meteo · LangGraph · local `bge-small` (LLM: Gemini Flash on roadmap — advisories are deliberately deterministic templates) · LightGBM→PyTorch (Colab/Kaggle) · React+MapLibre+Deck.gl (Vercel) · Telegram + Twilio-trial · GitHub Actions cron. **Infra cost: ₹0.**

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
