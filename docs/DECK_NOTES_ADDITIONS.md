# Deck additions — ready-to-paste lines (from the research-notes review)

## Positioning slide: "Where we sit in India's air-quality stack"
- CPCB/CAAQMS **measure** → SAFAR **forecasts** → **VayuNetra OPERATES**
  (blame this cell now → 72h forecast → cited notice → citizen call, in minutes)
  → PAVITRA/InMAP (IIT-B · Berkeley · UW · CSTEP) **plans policy** on annual timescales.
- Roadmap line: "InMAP-PAVITRA source–receptor matrices are our upgrade path to
  policy-grade counterfactuals — their science is our roadmap, not our competitor."

## Validation slide (the honesty story)
- Attribution vs published inventories: **0.92 cosine vs SAFAR-Delhi (2018)**,
  0.88 vs CSTEP-Bengaluru (2022), 0.79 vs NEERI/Urban-Emissions Mumbai —
  "where we disagree, it's because our model correctly knows it's July, not
  stubble season" (live biomass ≈ 0 vs annual-average inventories).
- Forecast: beats persistence in all 3 cities; deep-learning upgrade evaluated on a
  GPU and **rejected honestly** (kept the winner). Prediction intervals audited →
  under-coverage found → fixed with Conformalized Quantile Regression (75–80%).
- Blame validated physically: traffic SHAP **2.30× higher in IST rush hours**
  with weather controlled.

## Data-credibility bullets (new since the notes)
- Population: **GPW v4.11 (CIESIN/SEDAC, NASA)** per H3 cell via Earth Engine —
  "people protected" and exposure are real counts, not a 40k/cell heuristic.
- Emissions: tonnes-avoided grounded in **SAFAR/CSTEP/Urban-Emissions city
  inventories** (EDGAR-consistent frame), citation carried in every /simulate response.
- Health: WHO HRAPIE CRFs **as operationalised in WHO AirQ+**; national context
  anchored to **Balakrishnan et al., Lancet Planetary Health 2019** (the same
  1.67M-deaths figure the problem statement quotes).
- Interventions: magnitudes from **Delhi odd-even trials (~4–7% ambient PM2.5)**
  and **CAQM GRAP Stage III/IV schedules** — nothing invented.
- **Heat × pollution compound alerts** (IMD heatwave criteria × CPCB bands):
  cross-signal risk no plain-AQI dashboard shows.

## Rural + urban / policy framing (one-liner each)
- "NCAP plans nationally; CAQM regulates the NCR; VayuNetra gives both the
  operational layer — per-cell blame, forecasts and cited enforcement."
- PMUY/household angle (rural): ambient monitoring is our scope; the advisory
  channel (IVR in local languages) is exactly the reach PMUY-style programmes
  need — roadmap: indoor-air advisories keyed to LPG-adoption data.
- Heatwaves × pollution: compound-risk alerts ship today; heat-mortality
  interaction modelling is the E7 roadmap.
