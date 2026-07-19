# VayuNetra City Onboarding Guide

VayuNetra is designed for **zero-code multi-city expansion**. You do not need to redeploy the backend or rewrite code to onboard a new city.

## On-Stage Onboarding Choreography (Live Demo Script)

To execute the 4th city onboarding flawlessly during the demo, follow this exact script.

### 1. The Configuration (YAML)
Explain to the judges that adding a city is a simple config drop. Show them this would be the contents of `core/config/cities/chennai.yml`:
```yaml
city_id: "chennai"
name: "Chennai"
state: "Tamil Nadu"
languages: ["en", "ta"]
center: [80.2707, 13.0827]
bbox: [80.1, 12.9, 80.4, 13.2]
```

### 2. The Live cURL Execution
Run this exact payload against the live production API. Auth = the public anon
token (Bearer) **plus** the `X-Admin-Key` header — there is no separate admin JWT.

```bash
# ADMIN_KEY and SUPABASE_ANON_KEY come from .env
curl -X POST "https://vayunetra-c8i8.onrender.com/admin/cities" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
     -H "X-Admin-Key: $ADMIN_KEY" \
     -d '{
           "city_id": "chennai",
           "name": "Chennai",
           "state": "Tamil Nadu",
           "languages": ["en", "ta"],
           "center": [80.2707, 13.0827],
           "bbox": [80.1, 12.9, 80.4, 13.2]
         }'
```

> ✅ **Rehearsed against production on 2026-07-19**: wrong key → `forbidden`;
> correct key → `{"onboarded": "..."}`; city appears in `GET /cities` and the
> UI dropdown immediately. Cleanup verified too.

**3-line stage script:**
1. *Say:* "Adding a city is one API call — no code, no redeploy."
2. *Do:* run the curl → point at `{"success": true, "data": {"onboarded": "chennai"}}`.
3. *See:* refresh the app → Chennai is in the city dropdown; tonight's cron starts ingesting it.

### 3. UI Verification
1. Open the live Vercel web app (https://vayunetra-aqi.vercel.app).
2. Refresh the page.
3. Click the top-left **City Selector Dropdown**.
4. "Chennai" will now appear in the list instantly, served directly via `GET /cities`.
5. Point out that Agent 0 is now ready to accept queries for Chennai, and the midnight cron job will automatically spin up OpenAQ ingestion and model forecasting for this new boundary.

### 4. Rollback (Cleanup post-demo)
To delete the test city after the presentation, run this SQL via Supabase Dashboard (or API):
```sql
DELETE FROM cities WHERE city_id = 'chennai';
```

*Note: In `DEMO_MODE=true` on local, the API simply acknowledges the request without touching the live DB. The cURL above points to Render production for the live demo.*
