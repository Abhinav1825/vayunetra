-- Hot-path indexes + data-integrity constraints.
-- Every CHECK set is a verified SUPERSET of the live distinct values (checked
-- against the DB before writing this), so applying it to existing data is safe.
-- NOT NULL columns were verified to contain zero nulls at write time.

-- ---------------------------------------------------------------------------
-- 1. Indexes on columns the API filters/sorts on every request
-- ---------------------------------------------------------------------------
-- /forecast filters city_id + horizon_h (was unindexed; only city+cell+issued existed)
create index if not exists idx_forecasts_city_horizon
  on forecasts (city_id, horizon_h, issued_at desc);

-- /enforcement sorts by priority_score desc and filters status
create index if not exists idx_enforcement_city_priority
  on enforcement_recs (city_id, priority_score desc);
create index if not exists idx_enforcement_city_status
  on enforcement_recs (city_id, status);

-- source_origin distinguishes registry vs cv_detected (E1) — filtered on refresh
create index if not exists idx_emission_sources_origin
  on emission_sources (city_id, source_origin);

-- RAG separates text vs image (E6) retrieval paths
create index if not exists idx_kb_chunks_modality
  on kb_chunks (modality);

-- ---------------------------------------------------------------------------
-- 2. Widen pop_exposed (int overflows above ~2.1B; metro aggregates can exceed)
-- ---------------------------------------------------------------------------
alter table enforcement_recs alter column pop_exposed type bigint;

-- ---------------------------------------------------------------------------
-- 3. NOT NULL on columns the Pydantic contract already treats as required
--    (verified: zero existing nulls in every column below)
-- ---------------------------------------------------------------------------
alter table measurements    alter column city_id         set not null;
alter table measurements    alter column h3_cell         set not null;
alter table measurements    alter column ts              set not null;
alter table measurements    alter column variable        set not null;
alter table measurements    alter column value           set not null;
alter table attribution     alter column city_id         set not null;
alter table attribution     alter column h3_cell         set not null;
alter table attribution     alter column source_category set not null;
alter table attribution     alter column share           set not null;
alter table enforcement_recs alter column city_id        set not null;
alter table enforcement_recs alter column status         set not null;
alter table emission_sources alter column city_id        set not null;
alter table emission_sources alter column type           set not null;
alter table kb_chunks        alter column modality        set not null;

-- ---------------------------------------------------------------------------
-- 4. CHECK constraints for enum-like text columns (superset of live values)
--    Wrapped so re-running the migration is idempotent.
-- ---------------------------------------------------------------------------
do $$ begin
  alter table measurements add constraint chk_measurements_variable check (
    variable in ('pm25','pm10','no2','so2','co','o3','aod','no2_sat','fire',
                 'wind_u','wind_v','blh','temp','rh','precip','traffic','population')
  );
exception when duplicate_object then null; end $$;

do $$ begin
  alter table attribution add constraint chk_attribution_category check (
    source_category in ('traffic','construction_dust','industrial',
                        'biomass_burning','transported','other')
  );
exception when duplicate_object then null; end $$;

do $$ begin
  alter table enforcement_recs add constraint chk_enforcement_status check (
    status in ('proposed','approved','dispatched','dismissed')
  );
exception when duplicate_object then null; end $$;

do $$ begin
  alter table emission_sources add constraint chk_emission_type check (
    type in ('construction','industry','waste_burn','diesel_corridor')
  );
exception when duplicate_object then null; end $$;

do $$ begin
  alter table kb_chunks add constraint chk_kb_modality check (
    modality in ('text','image')
  );
exception when duplicate_object then null; end $$;
