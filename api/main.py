"""VayuNetra API — FastAPI skeleton (F3 / read-API).

Runnable on day 1: every endpoint returns the standard envelope, served from
``demo/fixtures/*`` when DEMO_MODE=true so the frontend works with zero live deps.
Owner: Abhinav. Fill the TODOs with real Supabase reads + agent calls.

Run:  uvicorn api.main:app --reload  (from repo root)
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import core.env  # noqa: F401  (loads .env)
from core.schemas import err, ok

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
FIXTURES = Path(__file__).resolve().parent.parent / "demo" / "fixtures"

app = FastAPI(title="VayuNetra API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO Abhinav: lock to the Vercel origin in prod
    allow_methods=["*"],
    allow_headers=["*"],
)


def fixture(name: str, default: Any = None) -> Any:
    """Load demo/fixtures/<name>.json, or return default if missing."""
    p = FIXTURES / f"{name}.json"
    if p.exists():
        return json.loads(p.read_text())
    return default if default is not None else []


def _db():
    """Supabase client for live reads (DEMO_MODE=false). Service-role, server-side only.

    TODO Abhinav: replace service-role with JWT + RLS-scoped reads for prod auth.
    """
    from core.supa import client

    return client()


@app.get("/health")
def health() -> dict:
    return ok({"status": "ok", "demo_mode": DEMO_MODE})


@app.get("/cities")
def cities() -> dict:
    return ok(fixture("cities"))


@app.get("/aqi/current")
def aqi_current(city: str, bbox: str | None = None) -> dict:
    if DEMO_MODE:
        return ok(fixture("aqi_current"))
    rows = (
        _db().table("measurements")
        .select("h3_cell,ts,value").eq("city_id", city).eq("variable", "pm25")
        .order("ts", desc=True).limit(5000).execute().data
    )
    latest: dict[str, dict] = {}
    for r in rows:                       # rows are newest-first -> first per cell is latest
        latest.setdefault(r["h3_cell"], {"h3_cell": r["h3_cell"], "pm25": r["value"], "ts": r["ts"]})
    return ok(list(latest.values()))


@app.get("/attribution")
def attribution(city: str, cell: str | None = None, ward: str | None = None, ts: str | None = None) -> dict:
    if DEMO_MODE:
        return ok(fixture("attribution"))
    q = (
        _db().table("attribution")
        .select("h3_cell,source_category,share,confidence,evidence,ts_window")
        .eq("city_id", city)
    )
    if cell:
        q = q.eq("h3_cell", cell)
    cells: dict[str, dict] = {}
    for r in q.execute().data:           # long rows -> per-cell shares vector (blame map shape)
        c = cells.setdefault(r["h3_cell"], {
            "h3_cell": r["h3_cell"], "ts_window": r.get("ts_window"),
            "shares": {}, "confidence": r.get("confidence"), "evidence": r.get("evidence"),
        })
        c["shares"][r["source_category"]] = r["share"]
    return ok(list(cells.values()))


@app.get("/forecast")
def forecast(city: str, cell: str | None = None, horizon: int = 24) -> dict:
    if DEMO_MODE:
        return ok(fixture("forecast"))
    q = (
        _db().table("forecasts")
        .select("h3_cell,issued_at,horizon_h,target_var,value,pi_low,pi_high,persistence_value,model_version")
        .eq("city_id", city)
    )
    if cell:
        q = q.eq("h3_cell", cell)
    if horizon:
        q = q.eq("horizon_h", int(horizon))
    return ok(q.execute().data)


@app.get("/enforcement")
def enforcement(city: str, date: str | None = None) -> dict:
    return ok(fixture("enforcement"))


@app.post("/enforcement/{rec_id}/dossier")
def enforcement_dossier(rec_id: int) -> dict:
    # TODO Abhinav: A3 RAG-cited dossier (+ E6 satellite patch via Sejal)
    return ok(fixture("dossier", default={"rec_id": rec_id, "citations": [], "satellite_patch": None}))


@app.get("/advisory")
def advisory(city: str, ward: str | None = None, lang: str = "en") -> dict:
    return ok(fixture("advisory"))


@app.post("/agent/query")
def agent_query(body: dict) -> dict:
    # TODO Abhinav: route to LangGraph orchestrator (Agent 0)
    return ok({"answer": "orchestrator stub", "trace": []})


@app.post("/simulate")
def simulate(body: dict) -> dict:
    # TODO Abhinav (engine, E3) — counterfactual over Omkar's forecast/dispersion
    return ok(fixture("simulate", default={"delta_aqi_by_cell": {}, "people_protected": 0}))


@app.post("/optimize")
def optimize(body: dict) -> dict:
    # TODO Abhinav (engine, E5) — top-3 packages under an inspector budget
    return ok(fixture("optimize", default={"packages": []}))


@app.post("/admin/cities")
def admin_onboard_city(body: dict) -> dict:
    # TODO Abhinav: insert city row + ward<->h3 map; pipelines auto-pick it up
    if not body.get("city_id"):
        return err("bad_request", "city_id is required")
    return ok({"onboarded": body.get("city_id")})


# WS /live — TODO Abhinav: WebSocket push of attribution/forecast/alert updates.
