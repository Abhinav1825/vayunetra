"""VayuNetra API — FastAPI read-API + agent endpoints.  Owner: Abhinav.

Every endpoint returns the standard {success, data, error, meta} envelope.
In DEMO_MODE (default), all responses are served from demo/fixtures/* so the
frontend works with zero live dependencies.

Run:
    uvicorn api.main:app --reload          # from repo root
    DEMO_MODE=false uvicorn api.main:app   # live Supabase reads
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import core.env  # noqa: F401  (loads .env)
from core.schemas import err, ok

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
FIXTURES = Path(__file__).resolve().parent.parent / "demo" / "fixtures"

app = FastAPI(
    title="VayuNetra API",
    version="1.0.0",
    description=(
        "AI-powered urban air quality intelligence platform. "
        "Multi-agent system: Attribution · Forecast · Enforcement · Advisory · Multi-City."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO Abhinav: lock to Vercel origin in prod
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fixture(name: str, default: Any = None) -> Any:
    """Load demo/fixtures/<name>.json, or return default if missing."""
    p = FIXTURES / f"{name}.json"
    if p.exists():
        return json.loads(p.read_text())
    return default if default is not None else []


def fixture_rows(name: str, city: str | None = None, default: Any = None) -> Any:
    """Load a fixture and filter list rows by city_id when available."""
    rows = fixture(name, default)
    if city and isinstance(rows, list):
        city_rows = [r for r in rows if r.get("city_id") == city]
        return city_rows if city_rows else rows
    return rows


def _db():
    """Supabase client for live reads (DEMO_MODE=false). Service-role, server-side only."""
    from core.supa import client
    return client()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health", tags=["system"])
def health() -> dict:
    """Liveness check — also shows DEMO_MODE status."""
    return ok({"status": "ok", "demo_mode": DEMO_MODE, "version": "1.0.0"})


# ---------------------------------------------------------------------------
# Cities
# ---------------------------------------------------------------------------

@app.get("/cities", tags=["data"])
def cities() -> dict:
    """List all active cities."""
    if DEMO_MODE:
        return ok(fixture("cities"))
    rows = _db().table("cities").select("*").eq("active", True).execute().data
    return ok(rows)


# ---------------------------------------------------------------------------
# AQI
# ---------------------------------------------------------------------------

@app.get("/aqi/current", tags=["data"])
def aqi_current(
    city: str = Query(..., description="City ID, e.g. 'delhi'"),
    bbox: Optional[str] = Query(None, description="Bounding box: lon_min,lat_min,lon_max,lat_max"),
) -> dict:
    """Latest per-cell AQI measurements for a city."""
    if DEMO_MODE:
        return ok(fixture_rows("aqi_current", city))
    rows = (
        _db().table("measurements")
        .select("h3_cell,ts,value,variable,confidence")
        .eq("city_id", city)
        .eq("variable", "pm25")
        .order("ts", desc=True)
        .limit(5000)
        .execute()
        .data
    )
    latest: dict[str, dict] = {}
    for r in rows:
        latest.setdefault(r["h3_cell"], {
            "h3_cell": r["h3_cell"],
            "pm25": r["value"],
            "ts": r["ts"],
            "confidence": r.get("confidence", 1.0),
        })
    return ok(list(latest.values()))


# ---------------------------------------------------------------------------
# Attribution
# ---------------------------------------------------------------------------

@app.get("/attribution", tags=["data"])
def attribution(
    city: str = Query(..., description="City ID"),
    cell: Optional[str] = Query(None, description="H3 cell ID"),
    ward: Optional[str] = Query(None, description="Ward name/ID"),
    ts: Optional[str] = Query(None, description="Timestamp ISO string"),
) -> dict:
    """Per-cell source attribution (the blame map)."""
    if DEMO_MODE:
        data = fixture_rows("attribution", city)
        if cell:
            data = [r for r in data if r.get("h3_cell") == cell]
        return ok(data)

    q = (
        _db().table("attribution")
        .select("h3_cell,source_category,share,confidence,evidence,ts_window")
        .eq("city_id", city)
    )
    if cell:
        q = q.eq("h3_cell", cell)
    rows = q.execute().data

    # Reshape: one record per cell with source_shares dict
    cells: dict[str, dict] = {}
    for r in rows:
        c = cells.setdefault(r["h3_cell"], {
            "h3_cell": r["h3_cell"],
            "ts_window": r.get("ts_window"),
            "shares": {},
            "confidence": r.get("confidence"),
            "evidence": r.get("evidence"),
        })
        c["shares"][r["source_category"]] = r["share"]
    return ok(list(cells.values()))


# ---------------------------------------------------------------------------
# Forecast
# ---------------------------------------------------------------------------

@app.get("/forecast", tags=["data"])
def forecast(
    city: str = Query(..., description="City ID"),
    cell: Optional[str] = Query(None, description="H3 cell ID"),
    horizon: int = Query(24, description="Forecast horizon in hours (24/48/72)"),
) -> dict:
    """AQI forecasts with persistence baseline for comparison."""
    if DEMO_MODE:
        data = fixture_rows("forecast", city)
        if cell:
            data = [r for r in data if r.get("h3_cell") == cell]
        if horizon:
            data = [r for r in data if r.get("horizon_h") == horizon]
        return ok(data)

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


# ---------------------------------------------------------------------------
# Enforcement
# ---------------------------------------------------------------------------

@app.get("/enforcement", tags=["enforcement"])
def enforcement_list(
    city: str = Query(..., description="City ID"),
    date: Optional[str] = Query(None, description="Date filter YYYY-MM-DD"),
    status: Optional[str] = Query(None, description="Status filter: proposed|approved|dispatched"),
    limit: int = Query(50, description="Max results"),
) -> dict:
    """Ranked enforcement worklist for the city."""
    if DEMO_MODE:
        data = fixture_rows("enforcement", city)
        if status:
            data = [r for r in data if r.get("status") == status]
        return ok(data[:limit])

    q = (
        _db().table("enforcement_recs")
        .select(
            "id,city_id,h3_cell,ts,source_id,priority_score,contribution,pop_exposed,"
            "rationale,rag_citations,rubric_score,status"
        )
        .eq("city_id", city)
        .order("priority_score", desc=True)
        .limit(limit)
    )
    if date:
        q = q.gte("ts", f"{date}T00:00:00Z").lte("ts", f"{date}T23:59:59Z")
    if status:
        q = q.eq("status", status)
    return ok(q.execute().data)


@app.get("/enforcement/{rec_id}/dossier", tags=["enforcement"])
def enforcement_dossier(rec_id: int) -> dict:
    """Full evidence dossier for an enforcement recommendation, with RAG citations.

    Includes: rationale, regulatory citations, rubric score, suggested notice text,
    and (Stage 2, Sejal E6) satellite patch.
    """
    if DEMO_MODE:
        return ok(fixture("dossier", default={"rec_id": rec_id, "citations": [], "satellite_patch": None}))
    from agents.enforcement import build_dossier
    try:
        dossier = build_dossier(rec_id)
        return ok(dossier)
    except Exception as e:
        return err("dossier_error", str(e))


@app.post("/enforcement/{rec_id}/status", tags=["enforcement"])
def enforcement_update_status(rec_id: int, body: dict) -> dict:
    """Update enforcement rec status (approved / dispatched / dismissed)."""
    new_status = body.get("status")
    valid_statuses = {"proposed", "approved", "dispatched", "dismissed"}
    if new_status not in valid_statuses:
        return err("bad_request", f"status must be one of {valid_statuses}")

    if DEMO_MODE:
        return ok({"rec_id": rec_id, "status": new_status, "demo": True})

    _db().table("enforcement_recs").update({"status": new_status}).eq("id", rec_id).execute()
    return ok({"rec_id": rec_id, "status": new_status})


# ---------------------------------------------------------------------------
# Advisory
# ---------------------------------------------------------------------------

@app.get("/advisory", tags=["advisory"])
def advisory(
    city: str = Query(..., description="City ID"),
    ward: Optional[str] = Query(None, description="Ward name/ID"),
    lang: str = Query("en", description="Language code: en|hi|kn|mr"),
) -> dict:
    """Ward-level citizen health advisories in specified language."""
    if DEMO_MODE:
        data = fixture_rows("advisory", city)
        if ward:
            data = [r for r in data if r.get("ward_id") == ward]
        if lang:
            data = [r for r in data if not r.get("language") or r.get("language") == lang]
        return ok(data)

    q = (
        _db().table("advisories")
        .select("*")
        .eq("city_id", city)
        .order("issued_at", desc=True)
        .limit(100)
    )
    if ward:
        q = q.eq("ward_id", ward)
    if lang:
        q = q.eq("language", lang)
    return ok(q.execute().data)


# ---------------------------------------------------------------------------
# Sejal Stage-1 static layers, mobility, comparison, and latency widgets
# ---------------------------------------------------------------------------

@app.get("/static-layers", tags=["data"])
def static_layers(city: str = Query(..., description="City ID")) -> dict:
    """OSM/WorldPop-style static layers: emission sources, roads, vulnerability."""
    if DEMO_MODE:
        data = fixture_rows("static_layers", city)
        return ok(data[0] if isinstance(data, list) and data else data)
    sources = _db().table("emission_sources").select("*").eq("city_id", city).execute().data
    return ok({"city_id": city, "emission_sources": sources, "vulnerability": [], "roads": []})


@app.get("/mobility", tags=["data"])
def mobility(city: str = Query(..., description="City ID")) -> dict:
    """Traffic proxy rows generated from OSM roads + time-of-day/day-of-week multipliers."""
    if DEMO_MODE:
        return ok(fixture_rows("mobility", city))
    rows = (
        _db().table("measurements")
        .select("city_id,h3_cell,station_id,ts,variable,value,unit,source,confidence")
        .eq("city_id", city)
        .eq("variable", "traffic")
        .order("ts", desc=True)
        .limit(1000)
        .execute()
        .data
    )
    return ok(rows)


@app.get("/comparison", tags=["data"])
def comparison() -> dict:
    """Agent 5 multi-city comparison: trends, signatures, and playbook recommendations."""
    return ok(fixture("comparison", default={"summary": {}, "cities": []}))


@app.get("/latency", tags=["system"])
def latency_widget(city: Optional[str] = Query(None, description="City ID")) -> dict:
    """Latest signal-to-action telemetry for the top-bar latency widget."""
    if DEMO_MODE:
        rows = fixture_rows("latency", city)
        if city and isinstance(rows, list):
            return ok(rows[0] if rows else {})
        return ok(rows)
    q = _db().table("action_traces").select("*").order("signal_ts", desc=True).limit(20)
    if city:
        q = q.eq("city_id", city)
    rows = q.execute().data
    return ok(rows[0] if city and rows else rows)


# ---------------------------------------------------------------------------
# Agent query (orchestrator entry point)
# ---------------------------------------------------------------------------

class AgentQueryBody(BaseModel):
    city: str = "delhi"
    query: str = ""
    focus_cells: Optional[list[str]] = None


@app.post("/agent/query", tags=["agent"])
def agent_query(body: AgentQueryBody) -> dict:
    """Route a natural-language or programmatic query to the LangGraph orchestrator.

    Returns: answer, trace (per-node timing), enforcement recs, advisories, citations.
    """
    t0 = time.time()
    try:
        from agents.graph import run_query
        result = run_query(
            city_id=body.city,
            query=body.query,
            focus_cells=body.focus_cells,
        )
        elapsed_ms = int((time.time() - t0) * 1000)
        return ok({
            "answer": f"Multi-agent pipeline complete for {body.city}.",
            "city_id": body.city,
            "query": body.query,
            "enforcement": result.get("enforcement") or [],
            "advisories": result.get("advisories") or [],
            "citations": result.get("citations") or [],
            "trace": result.get("trace") or [],
            "latency_ms": result.get("latency_ms") or elapsed_ms,
        })
    except Exception as e:
        return err("agent_error", str(e))


# ---------------------------------------------------------------------------
# What-if simulator (E3 — Abhinav Stage 2; stub with demo fixture)
# ---------------------------------------------------------------------------

class SimulateBody(BaseModel):
    city: str = "delhi"
    intervention_type: str = "construction_halt"
    target_cells: Optional[list[str]] = None
    target_source_ids: Optional[list[int]] = None
    horizon_h: int = 24


@app.post("/simulate", tags=["stage2"])
def simulate(body: SimulateBody) -> dict:
    """What-if intervention simulator (E3 — Stage 2 engine, stub in Stage 1)."""
    # Stage 1: return demo fixture
    return ok(fixture("simulate", default={
        "delta_aqi_by_cell": {},
        "people_protected": 0,
        "pm25_tonnes_avoided": 0,
        "confidence": 0,
    }))


# ---------------------------------------------------------------------------
# Prescriptive optimiser (E5 — Abhinav Stage 2; stub with demo fixture)
# ---------------------------------------------------------------------------

class OptimizeBody(BaseModel):
    city: str = "delhi"
    budget_inspector_hours: int = 20
    target_cells: Optional[list[str]] = None
    horizon_h: int = 24


@app.post("/optimize", tags=["stage2"])
def optimize(body: OptimizeBody) -> dict:
    """Prescriptive intervention optimiser (E5 — Stage 2 engine, stub in Stage 1)."""
    return ok(fixture("optimize", default={"packages": []}))


# ---------------------------------------------------------------------------
# City onboarding (admin)
# ---------------------------------------------------------------------------

class CityBody(BaseModel):
    city_id: str
    name: str
    state: str = ""
    languages: list[str] = ["en"]
    center: Optional[list[float]] = None
    bbox: Optional[list[float]] = None


@app.post("/admin/cities", tags=["admin"])
def admin_onboard_city(body: CityBody) -> dict:
    """Onboard a new city (config-driven, zero code change)."""
    if not body.city_id:
        return err("bad_request", "city_id is required")
    if DEMO_MODE:
        return ok({"onboarded": body.city_id, "demo": True})

    # Upsert city row
    _db().table("cities").upsert({
        "city_id": body.city_id,
        "name": body.name,
        "state": body.state,
        "languages": body.languages,
        "active": True,
    }).execute()
    return ok({"onboarded": body.city_id})


# ---------------------------------------------------------------------------
# Live action trace telemetry
# ---------------------------------------------------------------------------

@app.get("/traces", tags=["system"])
def get_traces(
    city: str = Query(..., description="City ID"),
    limit: int = Query(20, description="Max traces"),
) -> dict:
    """Retrieve recent signal-to-action latency traces (North-Star metric)."""
    if DEMO_MODE:
        return ok([
            {
                "city_id": city,
                "signal_ts": "2026-06-27T08:00:00Z",
                "attribution_ts": "2026-06-27T08:01:12Z",
                "forecast_ts": "2026-06-27T08:02:05Z",
                "enforcement_ts": "2026-06-27T08:03:30Z",
                "advisory_ts": "2026-06-27T08:04:15Z",
                "total_latency_ms": 255000,
                "trace": {"nodes": ["orchestrator", "attribution", "forecast", "enforcement", "advisory"]},
            }
        ])
    rows = (
        _db().table("action_traces")
        .select("*")
        .eq("city_id", city)
        .order("signal_ts", desc=True)
        .limit(limit)
        .execute()
        .data
    )
    return ok(rows)


# ---------------------------------------------------------------------------
# WebSocket stub — /live
# ---------------------------------------------------------------------------

# TODO Abhinav (Stage 1): implement WebSocket push of attribution/forecast/alert updates.
# Implementation sketch:
#   @app.websocket("/live")
#   async def websocket_live(ws: WebSocket):
#       await ws.accept()
#       while True:
#           payload = await get_latest_signals(city_id)
#           await ws.send_json(ok(payload))
#           await asyncio.sleep(60)
