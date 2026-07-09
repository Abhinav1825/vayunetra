# Stage 2 Demo Video Runbook (Sejal lane)

## Output

Target file: `docs/VayuNetra_Stage2_Demo.mp4`

This environment has no screen recorder/encoder, so the MP4 is recorded from the running app. This runbook adds the Stage-2 features to the Stage-1 flow ([STAGE1_DEMO_VIDEO_RUNBOOK.md](STAGE1_DEMO_VIDEO_RUNBOOK.md)); record as one continuous take. Everything works in `DEMO_MODE` (offline) — no live keys needed.

## Setup

1. API: `python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8010`
2. Web: `cd web` · `$env:VITE_API_BASE_URL="http://127.0.0.1:8010"` · `npm run dev`
3. Open `http://localhost:5173` (Delhi).

## Shot List (Stage-2 additions)

1. **Explainability** — click a hexagon; in the Cell Story panel show the **SHAP drivers (µg/m³)** and model R² beside the blame shares.
2. **Detected sources** — in *Map Layers*, toggle **Detected sources**; hover a marker to show name · confidence · origin.
3. **Dense coverage (E2)** — switch the map mode to **PM2.5**, then flip **Stations only ↔ Dense 1km**; call out the legend note: *"~8 stations → ~800 cells · +55% skill vs interpolation."*
4. **What-if (E3+E7)** — open the **What-if** tab; choose *Crop-residue / waste burn ban*, +24h, **Run simulation**; read the ΔAQI and the **impact cards** (people protected, ₹ health cost avoided, CO₂e); expand **sources** to show every figure is cited.
5. **City ROI (E7)** — open the **ROI** tab; show the annual burden (deaths/yr, ₹/yr) and the NCAP-cut savings — "the funding case"; expand sources.
6. **Multi-city burden** — open **Compare**; point out the per-city **deaths/yr + ₹/yr** line and the *highest burden* tag.

## Voiceover

"Stage 2 answers two questions. First — what is it worth? Every intervention now returns cited health and carbon numbers: people protected, rupees of health cost avoided, and tonnes of CO₂e — each figure traceable to a WHO, CPCB, or emission-factor source, never an invented constant. The City ROI view turns that into the funding case: tens of thousands of premature deaths a year, and what an NCAP-scale cut would avert. Second — where you have no station? The dense-coverage model turns forty ground stations into a full-city one-kilometre map, and it beats plain interpolation by fifty-five percent on held-out data. Toggle stations-to-dense and the blind spots fill in. And it stays honest — SHAP explains every blame call, and any number we cannot defensibly compute is shown as null, not faked."

## Honesty callouts (say at least one on camera)

- CO₂e is `null` for construction-dust interventions — dust control has no direct carbon co-benefit.
- Dense-coverage skill is measured on **held-out** data vs interpolation; real held-out-**station** RMSE trains on Kaggle.
- VSL is uncertain; the ₹ figure is shown with its caveat as order-of-magnitude.

## Deferred (mention as roadmap, do not demo)

E6 satellite-patch evidence, the E5 optimiser, and the fairness-audit endpoint are Abhinav's lane — slots reserved in schema/API/UI for the integration window.
