"""Shared Supabase access helpers."""
from __future__ import annotations

import os

import core.env  # noqa: F401  (loads .env)


def service_client():
    """Supabase client with service-role privileges for trusted server jobs."""
    from supabase import create_client

    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])


def anon_client():
    """Supabase client that honors caller JWT/RLS when auth(token) is applied."""
    from supabase import create_client

    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])


def client():
    """Backward-compatible service-role client for existing pipelines."""
    return service_client()


def load_measurements(city_id: str) -> list[dict]:
    """Page through all measurements for a city (PostgREST caps at 1000 rows/request)."""
    c = client()
    rows: list[dict] = []
    start, page = 0, 1000
    while True:
        batch = (
            c.table("measurements")
            .select("city_id,h3_cell,ts,variable,value")
            .eq("city_id", city_id)
            .range(start, start + page - 1)
            .execute()
            .data
        )
        rows.extend(batch)
        if len(batch) < page:
            break
        start += page
    return rows
