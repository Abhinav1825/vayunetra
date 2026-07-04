-- =====================================================================
-- VayuNetra — public (anon) read for the deployed dashboard.
-- Owner: Omkar (deploy). Extends 20260629000001_rls_complete.sql.
--
-- The Vercel frontend has no login; it calls the API with the Supabase
-- anon key. Attribution and enforcement notices are public-interest air-
-- quality data, so we grant anonymous SELECT. Writes stay admin/officer-only
-- (governed by the existing policies + service-role pipeline).
-- Apply:  supabase db push   (or paste into the Supabase SQL Editor)
-- =====================================================================

alter table attribution enable row level security;

do $$ begin
  create policy "public read attribution" on attribution
    for select using (true);
exception when duplicate_object then null; end $$;

alter table enforcement_recs enable row level security;

do $$ begin
  create policy "public read enforcement_recs" on enforcement_recs
    for select using (true);
exception when duplicate_object then null; end $$;
