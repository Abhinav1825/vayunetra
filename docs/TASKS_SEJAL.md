# Sejal — Task Checklist (VayuNetra / PS5)

> **Role:** **Product + coverage** — owns **Agent 4 (Citizen Advisory)** + **Agent 5 (Multi-City)**, the app shell + most of the frontend, the citizen channels, mobility data, and the Stage-2 coverage/evidence/impact models (E2/E6/E7) + the deck & demo video.
> **Full plan:** [PLAN_OF_ACTION.md](PLAN_OF_ACTION.md) · **Specs:** [PRD.md](PRD.md) + [ARCHITECTURE.md](ARCHITECTURE.md)
> Difficulty: 🔴 hard ML · 🟡 medium · 🟢 light.

## How you stay unblocked
- You co-own the **API contract (F3)** and own the **app shell (F4)** — define them early so you can build the whole UI against **mock JSON** and **DEMO_MODE fixtures** without waiting on live models.
- Every UI panel **reads Supabase / the API** — never a direct call to a teammate.
- Others' panels (Omkar's blame map, Abhinav's enforcement panel) plug into **your shell** — agree the component interface in Phase 0.

---

## Phase 0 — Foundation (do first)
- [ ] **F3 — API contract** (endpoints + envelope — with Abhinav). 🟡
- [ ] **F4 — React app shell + MapLibre base map** rendering Delhi from **mock JSON**. 🟡
- [ ] **F8 — DEMO_MODE fixture format** (the frozen-snapshot JSON shape). 🟡

---

## STAGE 1 — PS5 core (must-ship)
- [ ] **Connectors** → static layers / `emission_sources`: OSM (roads, land use, industrial, hospitals/schools) + WorldPop (population) + emission-source registry. 🟡 *(indep)*
- [ ] **Mobility feeds** (PS5-named) — GTFS transit + a time-of-day/day-of-week **traffic proxy** from the OSM road network → mobility feature in `measurements` (Omkar's models consume it via DB). 🟡 *(indep)*
- [ ] **Agent 4 — Advisory** — health tiering (CPCB/WHO breakpoints × vulnerability) + LLM (Gemini) localisation into **hi/en/kn/mr** → `advisories`; deliver via **Citizen PWA + Telegram + IVR + public-display mode**. 🟡 *(dep: forecast + vulnerability via DB — mock until Window)*
- [ ] **Agent 5 — Multi-City** — cross-city trends + before/after intervention deltas + H3 signature matching → playbook recommendations. 🟡 *(dep: multi-city data via DB)*
- [ ] **App shell + integration** — React/Vite/Tailwind shell, routing, state (TanStack Query + Zustand), map base, WebSocket; **integrate Omkar's & Abhinav's UI panels**. 🟡
- [ ] **Your UI panels** — **city switcher**, **comparative tab**, **live latency widget**, Citizen PWA, language toggle. 🟡
- [ ] **Multi-city configs** — `bengaluru.yml` + `mumbai.yml` (city-agnostic ingestion runs them). 🟢 *(coordinate with Omkar's connectors)*
- [ ] **DEMO_MODE wiring** in the app (one flag → entire app runs offline). 🟡
- [ ] **Deliverables** — architecture diagram, **pitch deck (10–12 slides)**, **demo video (≤3 min)**, demo script (all teammates supply their slides/metrics). 🟡/🟢

**Your Stage-1 "done when":** 3 cities switchable; advisory live in **4 languages** (app + Telegram + IVR); the console integrates all panels; DEMO_MODE runs offline; deck + video drafted.

---

## STAGE 2 — Enhancements (only after Stage-1 DoD)
- [ ] **E2 — Dense-coverage** (data + **2 models**): **AOD→PM2.5 regressor** + **1km downscaling CNN** → full-city field + a **"stations-only ↔ dense 1km" toggle**. 🔴🔴 *(Kaggle GPU)*
- [ ] **E6 — Multimodal evidence** — CLIP-embed Sentinel-2 patches → `kb_chunks(modality='image')`; the **dossier shows the actual satellite patch** beside the citation + PDF export. 🔴/🟡 *(dep: E1 detections via DB)*
- [ ] **E7 — Health & carbon** (engine + UI): cited dose-response + emission factors → **₹ / cases-prevented / CO₂e cards** on what-if/optimiser/advisory + a **City ROI dashboard** (₹/yr + CO₂e → NCAP funding narrative). 🟡/🟢
- [ ] **What-if + optimiser UI panels** (intervention toggles, constraint sliders, ranked package cards) + **SHAP / Fairness panels** + **"detected sources" toggle**. 🟡 *(dep: /simulate, /optimize)*
- [ ] **Deck + video v2** — add the optimiser, satellite-evidence, and ₹/lives/CO₂e moments; final polished dry-run. 🟢/🟡

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
