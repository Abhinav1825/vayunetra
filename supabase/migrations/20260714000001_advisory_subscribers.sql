-- Telegram two-way subscription for Agent 4 advisories.
create table if not exists advisory_subscribers (
  chat_id     text primary key,
  city_id     text references cities(city_id),
  language    text default 'en',
  active      boolean default true,
  created_at  timestamptz default now(),
  updated_at  timestamptz default now()
);

create index if not exists idx_advisory_subscribers_city on advisory_subscribers(city_id, active);
