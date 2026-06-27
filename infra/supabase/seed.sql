-- =====================================================================
-- VayuNetra — city seed (the 3 showcase cities, WITH PostGIS geometry).
-- Run AFTER 0001_init.sql + 0002_roles_rls.sql.
--   psql "$SUPABASE_DB_URL" -f infra/supabase/seed.sql
--   (or paste into the Supabase SQL Editor)
-- Idempotent: ON CONFLICT DO NOTHING — safe to re-run, won't clobber.
-- =====================================================================

insert into cities (city_id, name, state, bbox, center, languages, active) values
  ('delhi', 'Delhi', 'DL',
   ST_MakeEnvelope(76.84, 28.40, 77.35, 28.88, 4326),
   ST_SetSRID(ST_MakePoint(77.21, 28.61), 4326),
   '{hi,en}', true),
  ('bengaluru', 'Bengaluru', 'KA',
   ST_MakeEnvelope(77.45, 12.83, 77.75, 13.14, 4326),
   ST_SetSRID(ST_MakePoint(77.59, 12.97), 4326),
   '{kn,en}', true),
  ('mumbai', 'Mumbai', 'MH',
   ST_MakeEnvelope(72.77, 18.89, 72.99, 19.27, 4326),
   ST_SetSRID(ST_MakePoint(72.87, 19.07), 4326),
   '{mr,en,hi}', true)
on conflict (city_id) do nothing;
