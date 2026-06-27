"""Shared Supabase access helpers (service-role).  Used by ML training/serving scripts."""
from __future__ import annotations

import os

import core.env  # noqa: F401  (loads .env)


def client():
    from supabase import create_client

    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])


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
