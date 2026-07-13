# VayuNetra City Onboarding Guide

VayuNetra is designed for **zero-code multi-city expansion**. You do not need to redeploy the backend or rewrite code to onboard a new city.

## Onboarding a 4th City (Live Demo)

To onboard a new city live on stage (e.g., adding "Chennai"), simply send a `POST` request to the `/admin/cities` endpoint.

### Example using cURL
```bash
curl -X POST "https://api.vayunetra.app/admin/cities" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <ADMIN_JWT_TOKEN>" \
     -d '{
           "city_id": "chennai",
           "name": "Chennai",
           "state": "Tamil Nadu",
           "languages": ["en", "ta"],
           "center": [80.2707, 13.0827],
           "bbox": [80.1, 12.9, 80.4, 13.2]
         }'
```

### What happens next?
1. The API upserts the city into the Supabase `cities` table with `active = True`.
2. The UI dropdown immediately populates with the new city (served via `GET /cities`).
3. The cron jobs (Airflow/GitHub Actions) will pick up the new active city on their next cycle and begin ingesting OpenAQ CAAQMS data, computing forecasts, and generating attribution matrices.
4. The Agent 0 Orchestrator will accept queries for `"chennai"`.

*Note: In `DEMO_MODE=true`, the API simply acknowledges the request so you can demonstrate the workflow without side-effects.*
