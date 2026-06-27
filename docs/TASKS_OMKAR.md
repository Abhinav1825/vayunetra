# Omkar — Task Checklist (VayuNetra / PS5)

> **Role:** **AI/ML core** — owns the **two main models for the submission**: **Agent 1 (Attribution / blame map)** + **Agent 2 (Forecast / beats-persistence)**, plus dispersion + the deep-forecast upgrade.
> **Full plan:** [PLAN_OF_ACTION.md](PLAN_OF_ACTION.md) · **Specs:** [PRD.md](PRD.md) + [ARCHITECTURE.md](ARCHITECTURE.md)
> Difficulty: 🔴 hard ML · 🟡 medium · 🟢 light.

## How you stay unblocked
- Work against the **Supabase schema** (the data contract) + the **Delhi seed dataset** you build in Phase 0. You barely depend on anyone.
- Your UI panels plug into Sejal's app shell — build them as **independent components**; integrate at the stage-end Window.
- **You are the critical path for Stage 1** (your 2 models gate the demo) → start them early.

---

## Phase 0 — Foundation (do first)
- [ ] **F5 — H3 utilities** + ward↔H3 mapping + `core/config/cities/delhi.yml`. 🟡
- [ ] **F6 — Delhi seed dataset** loaded to Supabase (a few days of CAAQMS + history) so the whole team has data Day 1. 🟡

---

## STAGE 1 — PS5 core (must-ship)
- [ ] **Connectors** → `measurements`: CAAQMS/OpenAQ (hourly + OpenAQ/historical backfill) + **Earth Engine** satellite (Sentinel-5P NO₂/SO₂/CO/AOD, MODIS/VIIRS AOD+fire) + **Open-Meteo** weather + seasonal/event calendars (stubble, Diwali, inversion). 🟡 *(indep)*
- [ ] **Dispersion engine** — Gaussian plume + wind-field advection of satellite NO₂/AOD → physics features (feeds both your models). 🔴 *(indep)*
- [ ] **⭐ Agent 1 — Attribution [MAIN]** — chemical-signature priors + satellite + land-use + dispersion → gradient-boosting apportionment + **confidence + SHAP** → `attribution` table. 🔴 *(indep; own data + seed)*
- [ ] **⭐ Agent 2 — Forecast [MAIN]** — LightGBM (quantile) 24/48/72h on H3; **persistence + climatology baselines stored side-by-side** → `forecasts`; **backtest → skill score `1 − RMSE_model/RMSE_persistence` (THE headline number).** 🔴 *(dep: seed)*
- [ ] **UI panels** — **Blame Map** (Deck.gl `H3HexagonLayer` by dominant source + SHAP tooltips + satellite overlay) + **Forecast time-slider** (24–72h + spike alerts). 🟡 *(plug into Sejal's shell; build as components)*

**Your Stage-1 "done when":** attribution renders with confidence on the blame map · forecast beats persistence with a reported number · both write to the schema · validated in Abhinav's `evaluate.ipynb`.

---

## STAGE 2 — Enhancements (only after Stage-1 DoD)
> Intentionally light — your Stage 1 already carried the two hero models.
- [ ] **GNN/TFT forecast upgrade** over LightGBM — adopt **only if** it beats the baseline more. 🔴 *(Colab/Kaggle GPU)*
- [ ] **Forecast + dispersion hooks for E3** — expose the counterfactual interface Abhinav's what-if reads (via DB/API). 🟢
- [ ] **Attribution v2 polish** — calibrate confidence + refine SHAP for the demo. 🟡

**Your Stage-2 "done when":** GNN tried & reported honestly (kept only if better); E3 hooks ready for Abhinav.

---

## Your dependencies (all mockable → no mid-stage blocking)
| You need | From | Until then |
|---|---|---|
| App shell to host your panels | Sejal (F4) | build panels as standalone components |
| (nothing else critical) | — | you own your data + models end-to-end |

## Your risks to own
- **Forecast skill < 25%** → strong met + dispersion features; **report the honest skill score + also beat climatology**; GNN only if it genuinely helps. *Don't fake the number.*
- **Attribution hard to validate** → calibrate to SAFAR/TERI on validation wards; show confidence; honest ±15–20%.

## Quick stack ref
Python · LightGBM → PyTorch (Colab/Kaggle GPU) · Earth Engine · H3 · Gaussian-plume dispersion · writes to Supabase (Postgres/PostGIS). **₹0.**
