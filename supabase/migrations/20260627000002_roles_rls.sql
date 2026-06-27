-- =====================================================================
-- VayuNetra — roles + Row-Level Security scaffold.  Source: ARCHITECTURE.md §16
-- Roles: admin | officer | inspector | citizen.
-- This is a STARTING scaffold — Abhinav owns the full auth/RLS policy set.
-- =====================================================================

-- Per-user profile mapping auth.users -> role + city (Supabase Auth provides auth.users)
create table if not exists profiles (
  user_id  uuid primary key references auth.users(id) on delete cascade,
  role     text not null default 'citizen' check (role in ('admin','officer','inspector','citizen')),
  city_id  text references cities(city_id),
  created_at timestamptz default now()
);

-- Helper: current user's role / city (used by policies)
create or replace function current_role_name() returns text
  language sql stable as $$ select role from profiles where user_id = auth.uid() $$;
create or replace function current_city() returns text
  language sql stable as $$ select city_id from profiles where user_id = auth.uid() $$;

-- Public, read-only for everyone (citizens included)
alter table cities      enable row level security;
alter table advisories  enable row level security;
alter table measurements enable row level security;
alter table forecasts   enable row level security;

do $$ begin
  create policy "public read cities"       on cities      for select using (true);
  create policy "public read advisories"   on advisories  for select using (true);
  create policy "public read measurements" on measurements for select using (true);
  create policy "public read forecasts"    on forecasts   for select using (true);
exception when duplicate_object then null; end $$;

-- Officer+ only: attribution + enforcement, scoped to their city
alter table attribution      enable row level security;
alter table enforcement_recs enable row level security;

do $$ begin
  create policy "officer read attribution" on attribution
    for select using (current_role_name() in ('admin','officer','inspector')
                      and (current_role_name() = 'admin' or city_id = current_city()));
  create policy "officer read enforcement" on enforcement_recs
    for select using (current_role_name() in ('admin','officer','inspector')
                      and (current_role_name() = 'admin' or city_id = current_city()));
exception when duplicate_object then null; end $$;

-- TODO (Abhinav): write policies for emission_sources, kb_chunks, action_traces;
-- admin-only INSERT on cities (onboarding via POST /admin/cities); service-role bypasses RLS for pipelines.
