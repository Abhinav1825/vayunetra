# VayuNetra — API Contract (F3)

> **The app contract.** Frontends and agents code against *this*, not against each other.
> Source: [ARCHITECTURE.md](ARCHITECTURE.md) §11. Owners: **Abhinav** (serve) + **Sejal** (consume).
> Base URL (local): `http://localhost:8000` · Auth: Supabase JWT (Bearer) · All responses use the envelope below.

## Response envelope (every endpoint)

```jsonc
{
  "success": true,            // boolean
  "data": { },                // payload, or null on error
  "error": null,              // { "code": "...", "message": "..." } or null
  "meta": { "total": 0, "page": 1, "limit": 50 }  // pagination/extra; optional
}
```

## Roles
`admin` ⊃ `officer` ⊃ `inspector` ⊃ `citizen` (all). "officer+" = officer, inspector, admin.

## Endpoints

| Method | Path | Purpose | Role | Owner |
|---|---|---|---|---|
| GET | `/health` | liveness + `DEMO_MODE` flag | all | Abhinav |
| GET | `/cities` | list onboarded cities | all | Abhinav |
| GET | `/aqi/current?city&bbox` | live AQI per H3 cell | all | Abhinav |
| GET | `/attribution?city&cell\|ward&ts` | source split + confidence (blame map) | officer+ | Abhinav |
| GET | `/forecast?city&cell&horizon` | forecast + intervals + persistence | all | Abhinav |
| GET | `/enforcement?city&date` | ranked enforcement recommendations | officer+ | Abhinav |
| POST | `/enforcement/{id}/dossier` | cited evidence packet + satellite patch (E6) | officer+ | Abhinav |
| GET | `/advisory?city&ward&lang` | localized citizen advisory | all | Abhinav |
| POST | `/agent/query` | conversational orchestrator (NL → action) | officer+ | Abhinav |
| POST | `/simulate` | what-if intervention → ΔAQI + people/₹/CO₂e (E3,E7) | officer+ | Abhinav(engine)+Sejal(UI) |
| POST | `/optimize` | best intervention bundle under budget → top-3 (E5) | officer+ | Abhinav(engine)+Sejal(UI) |
| POST | `/admin/cities` | onboard a city via config (scalability demo) | admin | Abhinav |
| WS | `/live` | push attribution/forecast/alert updates | all | Abhinav |

## Representative payloads (shape only — fill from real data / fixtures)

**GET /cities** → `data: City[]`
```jsonc
{ "city_id": "delhi", "name": "Delhi", "state": "DL",
  "center": [77.21, 28.61], "bbox": [76.84,28.40,77.35,28.88],
  "languages": ["hi","en"], "active": true }
```

**GET /attribution** → `data: AttributionCell[]`
```jsonc
{ "h3_cell": "883da1...", "ts_window": ["2026-06-27T08:00Z","2026-06-27T09:00Z"],
  "shares": { "construction_dust": 0.68, "traffic": 0.22, "transported": 0.10 },
  "confidence": 0.83, "evidence": { "top_features": ["no2","aod","pm10_pm25_ratio"] } }
```

**GET /forecast** → `data: ForecastPoint[]`
```jsonc
{ "h3_cell": "883da1...", "issued_at": "2026-06-27T06:00Z", "horizon_h": 24,
  "target_var": "aqi", "value": 312, "pi_low": 280, "pi_high": 345,
  "persistence_value": 295, "model_version": "lgbm-v1" }
```

**POST /simulate** (body `{ city, interventions:[{source_id, action, magnitude}] }`) → `data`
```jsonc
{ "delta_aqi_by_cell": { "883da1...": -42 },
  "people_protected": 18000, "pm25_tonnes_avoided": 2.3,
  "health_cost_avoided_inr": 6000000, "co2e_tonnes": 9 }
```

> **Conventions:** snake_case keys · ISO-8601 UTC timestamps · GeoJSON `[lng, lat]` order ·
> errors return `success:false` + populated `error` + HTTP 4xx/5xx. When `DEMO_MODE=true`,
> every endpoint serves `demo/fixtures/*` so the UI works with zero live dependencies.
