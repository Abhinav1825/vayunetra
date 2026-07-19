-- Before/after effect measurement, armed automatically at first real dispatch.
-- One row per dispatched enforcement rec: PM2.5 baseline frozen at dispatch,
-- effect computed on read once the post-window has data. Honest empty state.
create table if not exists intervention_tracking (
  id bigint generated always as identity primary key,
  rec_id bigint not null,
  city_id text not null,
  h3_cell text not null,
  dispatched_at timestamptz not null default now(),
  baseline_pm25 double precision,
  baseline_days int not null default 7,
  created_at timestamptz not null default now(),
  unique (rec_id)
);
alter table intervention_tracking enable row level security;
do $$ begin
  create policy "public read" on intervention_tracking for select using (true);
exception when duplicate_object then null; end $$;
