-- =====================================================================
-- VayuNetra — E2 dense-coverage field (Sejal, Stage 2).
-- Owner: Sejal. The downscaling models (ml/coverage) write a full-city,
-- per-H3-cell PM2.5 field with uncertainty; the API reads it for the
-- "stations ↔ dense 1 km" map toggle. Batch job (GitHub Actions) writes;
-- the dashboard reads. Anonymous SELECT (public-interest data, mirrors
-- 20260704000001_public_read_dashboard.sql).
-- Apply:  supabase db push   (or paste into the Supabase SQL Editor)
-- =====================================================================

create table if not exists coverage_field (
  id             bigserial primary key,
  city_id        text references cities(city_id),
  h3_cell        text,
  pm25           double precision,        -- dense 1 km estimate (downscaled)
  pm25_stations  double precision,        -- sparse stations-only baseline (IDW)
  uncertainty    double precision,        -- MC-dropout std, µg/m³
  model_version  text,
  generated_at   timestamptz default now()
);
create index if not exists idx_coverage_city_cell on coverage_field(city_id, h3_cell);

alter table coverage_field enable row level security;

do $$ begin
  create policy "public read coverage_field" on coverage_field
    for select using (true);
exception when duplicate_object then null; end $$;
