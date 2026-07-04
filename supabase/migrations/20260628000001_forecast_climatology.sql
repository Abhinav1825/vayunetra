-- Add the climatology baseline alongside persistence on each forecast (ARCHITECTURE.md §9.2).
-- Apply with:  npx supabase db push   (the forecast writer stores it once this column exists;
-- until then it gracefully writes forecasts without it).
alter table forecasts add column if not exists climatology_value double precision;
