-- Outdoor-work anchors per vulnerability zone (markets, transport hubs,
-- active construction from OSM) — feeds the outdoor_worker advisory segment.
alter table vulnerability add column if not exists outdoor_sites int not null default 0;
