# Sejal — Task Checklist (VayuNetra / PS5)

> **Role:** **Product + coverage** — owns **Agent 4 (Citizen Advisory)** + **Agent 5 (Multi-City)**, the app shell + most of the frontend, the citizen channels, mobility data, and the Stage-2 coverage/evidence/impact models (E2/E6/E7) + the deck & demo video.
> **Full plan:** [PLAN_OF_ACTION.md](PLAN_OF_ACTION.md) · **Specs:** [PRD.md](PRD.md) + [ARCHITECTURE.md](ARCHITECTURE.md)
> Difficulty: 🔴 hard ML · 🟡 medium · 🟢 light.

## ⚠️ READ FIRST — v3.3 status (2026-07-10)
**Your Phase 0 + Stage 1 are DONE except the DEMO VIDEO — which is now the single critical-path
item of the whole submission. Record it before any Stage-2 code.** Also:
1. **Rebase onto latest `main`** — these files of yours changed there (fixes found in live testing, do NOT revert):
   `ml/coverage/dense_field.py` (lean no-torch fallback — Render has no torch and was going to 500) ·
   `api/main.py` `/coverage` (live fields now anchor on REAL measurements — synthetic anchors showed a fabricated field) ·
   `web/src/BlameMap.tsx` (sources overlay reads `geom.coordinates` — it rendered nothing on live data) ·
   `web/src/App.tsx` (coverage caption honest when skill is null).
2. **WorldPop item is superseded** — GPW v4.11 population per H3 cell is live (`connectors/population.py`); don't build it.
3. **Advisories auto-refresh daily** via `scripts/refresh_advisories.py` + the cron — don't duplicate.
4. **Deck:** paste from `docs/DECK_NOTES_ADDITIONS.md` (validation numbers, positioning ladder) into v2.
5. **Merge small + daily; open PRs early** — every PR gets reviewed like PR #8 was.

## How you stay unblocked
- You co-own the **API contract (F3)** and own the **app shell (F4)** — define them early so you can build the whole UI against **mock JSON** and **DEMO_MODE fixtures** without waiting on live models.
- Every UI panel **reads Supabase / the API** — never a direct call to a teammate.
- Others' panels (Omkar's blame map, Abhinav's enforcement panel) plug into **your shell** — agree the component interface in Phase 0.

---

## Phase 0 — Foundation (do first)
- [x] **F3 — API contract** (endpoints + envelope — with Abhinav). 🟡
- [x] **F4 — React app shell + MapLibre base map** rendering Delhi from **mock JSON**. 🟡
- [x] **F8 — DEMO_MODE fixture format** (the frozen-snapshot JSON shape). 🟡

---

## STAGE 1 — PS5 core (must-ship)
- [x] **Connectors** → static layers / `emission_sources`: OSM (roads, land use, industrial, hospitals/schools) + WorldPop (population) + emission-source registry. 🟡 *(indep)*
- [x] **Mobility feeds** (PS5-named) — GTFS transit + a time-of-day/day-of-week **traffic proxy** from the OSM road network → mobility feature in `measurements` (Omkar's models consume it via DB). 🟡 *(indep)*
- [x] **Agent 4 — Advisory** — health tiering (CPCB/WHO breakpoints × vulnerability) + LLM (Gemini) localisation into **hi/en/kn/mr** → `advisories`; deliver via **Citizen PWA + Telegram + IVR + public-display mode**. 🟡 *(dep: forecast + vulnerability via DB — mock until Window)*
- [x] **Agent 5 — Multi-City** — cross-city trends + before/after intervention deltas + H3 signature matching → playbook recommendations. 🟡 *(dep: multi-city data via DB)*
- [x] **App shell + integration** — React/Vite/Tailwind shell, routing, state (TanStack Query + Zustand), map base, WebSocket; **integrate Omkar's & Abhinav's UI panels**. 🟡
- [x] **Your UI panels** — **city switcher**, **comparative tab**, **live latency widget**, Citizen PWA, language toggle. 🟡
- [x] **Multi-city configs** — `bengaluru.yml` + `mumbai.yml` (city-agnostic ingestion runs them). 🟢 *(coordinate with Omkar's connectors)*
- [x] **DEMO_MODE wiring** in the app (one flag → entire app runs offline). 🟡
- [x] **Deliverables** — diagram ✅ deck ✅ script ✅ — **demo video ❌ (see READ FIRST: critical path)** 🟡/🟢

**Your Stage-1 "done when":** 3 cities switchable; advisory live in **4 languages** (app + Telegram + IVR); the console integrates all panels; DEMO_MODE runs offline; deck + video drafted.

---

## STAGE 2 — Enhancements (v3.3 statuses — most of yours SHIPPED in PR #8 🎉)
- [ ] 🔴 **DEMO VIDEO (≤3 min) — before anything below.** Stage-1 DoD's only missing deliverable. Runbook exists (`STAGE1_DEMO_VIDEO_RUNBOOK.md`); record against the LIVE site after the latest push.
- [x] **E2 — Dense-coverage** ✅ shipped *(rebase note above)*. 🔁 Real-data Kaggle training = **stretch**, not blocker — the shipped version is honestly labeled "synthetic-field validation".
- [ ] 🔁 **E6 — Multimodal evidence** — **wait for Abhinav's detection-lite** (needs detections to attach patches to); it's next in the cut order if time runs short. 🔴/🟡
- [x] **E7 — Health & carbon** ✅ *(factor tables now also cite WHO AirQ+ + Balakrishnan/Lancet-2019 — the 1.67M figure PS5 quotes)*
- [x] **What-if UI + SHAP + detected-sources toggle** ✅ — *optimiser package cards*: add when Abhinav ships `/optimize`; *Fairness panel*: after his audit.
- [ ] **Deck + video v2** — absorb `docs/DECK_NOTES_ADDITIONS.md`; add optimiser + ₹/lives/CO₂e moments once E5 lands. 🟢/🟡
- [ ] 🆕 **Telegram two-way subscribe** *(v3.3 addition, post-merge)*: `/start` → pick city → auto-receive advisories — lets judges subscribe their own phone during judging. 🟡

**Your Stage-2 "done when":** dense 1km toggle works; a dossier shows a real satellite patch; ₹/lives/CO₂e cards + ROI dashboard live; polished deck + video done.

---

## Your dependencies (all mockable → no mid-stage blocking)
| You need | From | Until then |
|---|---|---|
| Forecast rows (for advisory) | Omkar | mock `forecasts` / DEMO_MODE fixtures |
| Read-API endpoints | Abhinav | mock JSON against the F3 contract |
| Others' UI panels | Omkar / Abhinav | placeholders in the shell; integrate at the Window |
| E1 detections (for E6) | Abhinav | seeded detections / sample patches |

## Your risks to own
- **Multi-language quality** → get a **native-speaker review** for Kannada/Marathi; keep messages short + templated.
- **Demo/pitch is what judges see** → invest in clean deck visuals + a tight, rehearsed narrative; a rambling demo sinks a strong project.
- **E2 hard to validate** → validate AOD→PM2.5 + downscaling against **held-out stations**; report honest RMSE/skill.

## Quick stack ref
React + TypeScript + Vite + Tailwind + **MapLibre GL + Deck.gl** (Vercel) · Gemini (i18n) · Telegram + Twilio-trial (IVR) · PyTorch (Kaggle GPU for E2) · CLIP via sentence-transformers · reads Supabase/API. **₹0.**
