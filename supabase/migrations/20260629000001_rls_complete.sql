-- =====================================================================
-- VayuNetra — RLS policies for remaining tables.  Owner: Abhinav.
-- Completes ARCHITECTURE.md §16 (security/auth/roles).
-- Roles: admin | officer | inspector | citizen (from profiles table).
-- Apply:  supabase db push   (runs after 20260627000002_roles_rls.sql)
-- =====================================================================

-- Helper functions already defined in migration 0002:
--   current_role_name() → text
--   current_city()      → text

-- ---------------------------------------------------------------------
-- emission_sources — public read; admin-only write (or service-role)
-- ---------------------------------------------------------------------
alter table emission_sources enable row level security;

do $$ begin
  create policy "public read emission_sources" on emission_sources
    for select using (true);
exception when duplicate_object then null; end $$;

do $$ begin
  create policy "admin write emission_sources" on emission_sources
    for insert with check (current_role_name() = 'admin');
exception when duplicate_object then null; end $$;

do $$ begin
  create policy "admin update emission_sources" on emission_sources
    for update using (current_role_name() = 'admin');
exception when duplicate_object then null; end $$;

-- ---------------------------------------------------------------------
-- kb_chunks — service-role pipeline writes; officer+ reads
-- ---------------------------------------------------------------------
alter table kb_chunks enable row level security;

do $$ begin
  create policy "officer read kb_chunks" on kb_chunks
    for select using (current_role_name() in ('admin', 'officer', 'inspector'));
exception when duplicate_object then null; end $$;

-- Note: inserts/updates done by service-role key (bypasses RLS), no insert policy needed.

-- ---------------------------------------------------------------------
-- action_traces — officer+ read; service-role writes (no user insert)
-- ---------------------------------------------------------------------
alter table action_traces enable row level security;

do $$ begin
  create policy "officer read action_traces" on action_traces
    for select using (
      current_role_name() in ('admin', 'officer', 'inspector')
      and (current_role_name() = 'admin' or city_id = current_city())
    );
exception when duplicate_object then null; end $$;

-- ---------------------------------------------------------------------
-- cities admin-only INSERT (onboarding via POST /admin/cities)
-- Service-role key bypasses RLS for all pipeline operations.
-- ---------------------------------------------------------------------
do $$ begin
  create policy "admin insert cities" on cities
    for insert with check (current_role_name() = 'admin');
exception when duplicate_object then null; end $$;

do $$ begin
  create policy "admin update cities" on cities
    for update using (current_role_name() = 'admin');
exception when duplicate_object then null; end $$;

-- ---------------------------------------------------------------------
-- profiles — users can read/update their own profile only
-- ---------------------------------------------------------------------
alter table profiles enable row level security;

do $$ begin
  create policy "own profile select" on profiles
    for select using (user_id = auth.uid());
exception when duplicate_object then null; end $$;

do $$ begin
  create policy "own profile update" on profiles
    for update using (user_id = auth.uid())
    with check (user_id = auth.uid() and role = 'citizen');  -- citizens can't self-promote
exception when duplicate_object then null; end $$;

do $$ begin
  create policy "admin manage profiles" on profiles
    for all using (current_role_name() = 'admin');
exception when duplicate_object then null; end $$;

-- Note: profile insert is handled by a trigger on auth.users (see below).
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer as $$
begin
  insert into public.profiles (user_id, role)
  values (new.id, 'citizen')
  on conflict (user_id) do nothing;
  return new;
end;
$$;

-- Create trigger only if it doesn't exist
do $$ begin
  create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();
exception when duplicate_object then null; end $$;
