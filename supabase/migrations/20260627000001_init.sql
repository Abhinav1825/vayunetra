-- =====================================================================
-- VayuNetra — initial schema (the DATA CONTRACT).  Source: ARCHITECTURE.md §7.2
-- Every model/agent WRITES rows here; every API/UI READS them. No direct calls.
-- Apply:  psql "$SUPABASE_DB_URL" -f infra/supabase/migrations/0001_init.sql
--    or:  supabase db push
-- =====================================================================

create extension if not exists postgis;
create extension if not exists vector;

-- ---------------------------------------------------------------------
-- Cities = config-driven onboarding (NO per-city code)
-- ---------------------------------------------------------------------
create table if not exists cities (
  city_id           text primary key,
  name              text not null,
  state             text,
  bbox              geometry(Polygon, 4326),
  center            geometry(Point, 4326),
  languages         text[],                 -- e.g. {hi,en,kn,mr}
  caaqms_station_ids text[],
  ward_geojson_ref  text,
  active            boolean default true
);

-- ---------------------------------------------------------------------
-- Universal measurements (ground + satellite + weather + mobility)
-- ---------------------------------------------------------------------
create table if not exists measurements (
  id           bigserial primary key,
  city_id      text references cities(city_id),
  h3_cell      text,                          -- res 8
  station_id   text,
  ts           timestamptz,
  variable     text,                          -- pm25,pm10,no2,so2,co,o3,aod,fire,wind_u,wind_v,blh,traffic,...
  value        double precision,
  unit         text,
  source       text,                          -- caaqms,openaq,s5p,modis,s2,openmeteo,osm_gtfs
  confidence   double precision default 1.0,
  ingested_at  timestamptz default now()
);
create index if not exists idx_measurements_city_var_ts on measurements(city_id, variable, ts);
create index if not exists idx_measurements_cell_ts      on measurements(h3_cell, ts);

-- ---------------------------------------------------------------------
-- Source attribution (Agent 1 output) — the "blame map"
-- ---------------------------------------------------------------------
create table if not exists attribution (
  id              bigserial primary key,
  city_id         text references cities(city_id),
  h3_cell         text,
  ts_window       tstzrange,
  source_category text,        -- traffic,construction_dust,industrial,biomass_burning,transported,other
  share           double precision,           -- 0..1, sums to 1 per cell/window
  confidence      double precision,
  method_version  text,
  evidence        jsonb                        -- which signals drove it (explainability / SHAP)
);
create index if not exists idx_attribution_city_cell on attribution(city_id, h3_cell);

-- ---------------------------------------------------------------------
-- Forecasts (Agent 2 output) — incl. baseline for honest comparison
-- ---------------------------------------------------------------------
create table if not exists forecasts (
  id                bigserial primary key,
  city_id           text references cities(city_id),
  h3_cell           text,
  issued_at         timestamptz,
  horizon_h         int,                       -- 24,48,72
  target_var        text default 'aqi',
  value             double precision,
  pi_low            double precision,
  pi_high           double precision,
  persistence_value double precision,          -- baseline shown side-by-side
  model_version     text
);
create index if not exists idx_forecasts_city_cell_issued on forecasts(city_id, h3_cell, issued_at);

-- ---------------------------------------------------------------------
-- Emission source registry (Agent 3 inputs; E1 CV detections land here too)
-- ---------------------------------------------------------------------
create table if not exists emission_sources (
  id                   bigserial primary key,
  city_id              text references cities(city_id),
  geom                 geometry(Geometry, 4326),
  type                 text,                    -- industry,construction,waste_burn,diesel_corridor
  name                 text,
  registry_ref         text,
  source_origin        text default 'registry', -- registry | cv_detected (E1)
  detection_confidence double precision,        -- for CV-detected sources
  attributes           jsonb
);
create index if not exists idx_emission_sources_city on emission_sources(city_id);

-- ---------------------------------------------------------------------
-- Enforcement recommendations (Agent 3 output)
-- ---------------------------------------------------------------------
create table if not exists enforcement_recs (
  id             bigserial primary key,
  city_id        text references cities(city_id),
  h3_cell        text,
  ts             timestamptz,
  source_id      bigint references emission_sources(id),
  priority_score double precision,
  contribution   double precision,
  pop_exposed    int,
  rationale      text,
  evidence       jsonb,
  rag_citations  jsonb,
  rubric_score   jsonb,                          -- §14 CPCB/GRAP rubric proxy
  status         text default 'proposed'         -- proposed | approved | dispatched | dismissed
);
create index if not exists idx_enforcement_city_ts on enforcement_recs(city_id, ts);

-- ---------------------------------------------------------------------
-- Citizen advisories (Agent 4 output)
-- ---------------------------------------------------------------------
create table if not exists advisories (
  id               bigserial primary key,
  city_id          text references cities(city_id),
  ward_id          text,
  h3_cell          text,
  issued_at        timestamptz,
  horizon_h        int,
  risk_tier        text,
  audience_segment text,        -- general,outdoor_worker,elderly,school,respiratory
  language         text,        -- hi,en,kn,mr
  channel          text,        -- pwa,telegram,ivr,display
  message          text
);
create index if not exists idx_advisories_city_ward on advisories(city_id, ward_id);

-- ---------------------------------------------------------------------
-- RAG knowledge base (pgvector) — text + (E6) multimodal image-patch embeddings
-- !!! EMBEDDING DIM: bge-small (local default) = 384.  Gemini / bge-base = 768.
-- !!! This column MUST match EMBEDDING_DIM in .env.  Default = 384 (bge-small).
-- !!! If you switch to Gemini embeddings, change vector(384) -> vector(768) and re-embed.
-- ---------------------------------------------------------------------
create table if not exists kb_chunks (
  id         bigserial primary key,
  doc_id     text,
  title      text,
  source_url text,
  modality   text default 'text',     -- text | image (E6 Sentinel-2 patch)
  chunk_text text,
  image_ref  text,                     -- -> Storage/R2 patch when modality='image'
  embedding  vector(384),
  metadata   jsonb
);
create index if not exists idx_kb_chunks_embedding on kb_chunks using ivfflat (embedding vector_cosine_ops);

-- ---------------------------------------------------------------------
-- Latency telemetry (proves the North-Star metric)
-- ---------------------------------------------------------------------
create table if not exists action_traces (
  id              bigserial primary key,
  city_id         text references cities(city_id),
  signal_ts       timestamptz,
  attribution_ts  timestamptz,
  forecast_ts     timestamptz,
  enforcement_ts  timestamptz,
  advisory_ts     timestamptz,
  total_latency_ms int,
  trace           jsonb
);
create index if not exists idx_action_traces_city on action_traces(city_id, signal_ts);
