# connectors/ — city-agnostic data ingestion

City-agnostic connectors that map each raw source → the **canonical measurement**
(`core/schemas/canonical.py`) → `measurements`. A city is just a config (`core/config/cities/*.yml`).
Spec: ARCHITECTURE.md §7.1, PRD §11.

| Connector | Owner | Notes |
|---|---|---|
| `caaqms`, `openaq` | **Omkar** | ground AQI, hourly + backfill |
| `earth_engine` (s5p, modis/viirs, s2) | **Omkar** | satellite features (daily precompute) |
| `open_meteo` | **Omkar** | weather + AQ forecast (no key) |
| `seasonal_calendars` | **Omkar** | stubble / Diwali / winter-inversion windows (forecast feature) |
| `osm`, `worldpop`, `registry` | **Sejal** | roads/land-use/industrial/hospitals + population → `emission_sources` |
| `mobility` (GTFS + traffic proxy) | **Sejal** | time-of-day proxy from OSM roads → mobility feature |

Each connector is independent and writes via the schema — no cross-person calls.
