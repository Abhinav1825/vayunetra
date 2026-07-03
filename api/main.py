"""VayuNetra API — FastAPI read-API + agent endpoints.  Owner: Abhinav.

Every endpoint returns the standard {success, data, error, meta} envelope.
In DEMO_MODE (default), all responses are served from demo/fixtures/* so the
frontend works with zero live dependencies.

Run:
    uvicorn api.main:app --reload          # from repo root
    DEMO_MODE=false uvicorn api.main:app   # live Supabase reads
"""
from __future__ import annotations

import base64
import json
import os
import time
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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


security = HTTPBearer(auto_error=False)


def _decode_bearer_payload(token: str) -> dict:
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token format")


def _validated_token(credentials: HTTPAuthorizationCredentials | None) -> str | None:
    if DEMO_MODE:
        return None

    token = credentials.credentials if credentials else None
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    payload = _decode_bearer_payload(token)
    role = payload.get("role", "")
    if role not in ("authenticated", "service_role", "admin"):
        raise HTTPException(status_code=403, detail="Insufficient role privileges")
    return token


def get_db(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Supabase client using the caller's JWT so PostgREST enforces RLS."""
    if DEMO_MODE:
        return None

    from core.supa import anon_client
    db = anon_client()
    token = _validated_token(credentials)
    db.postgrest.auth(token)
    return db


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
def cities(db=Depends(get_db)) -> dict:
    """List all active cities."""
    if DEMO_MODE:
        return ok(fixture("cities"))
    rows = db.table("cities").select("*").eq("active", True).execute().data
    return ok(rows)


# ---------------------------------------------------------------------------
# AQI
# ---------------------------------------------------------------------------

@app.get("/aqi/current", tags=["data"])
def aqi_current(
    city: str = Query(..., description="City ID, e.g. 'delhi'"),
    bbox: Optional[str] = Query(None, description="Bounding box: lon_min,lat_min,lon_max,lat_max"),
    db=Depends(get_db)
) -> dict:
    """Latest per-cell AQI measurements for a city."""
    if DEMO_MODE:
        return ok(fixture("aqi_current"))
    rows = (
        db.table("measurements")
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
    db=Depends(get_db)
) -> dict:
    """Per-cell source attribution (the blame map)."""
    if DEMO_MODE:
        data = fixture("attribution")
        if cell:
            data = [r for r in data if r.get("h3_cell") == cell]
        return ok(data)

    q = (
        db.table("attribution")
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
    db=Depends(get_db)
) -> dict:
    """AQI forecasts with persistence baseline for comparison."""
    if DEMO_MODE:
        data = fixture("forecast")
        if cell:
            data = [r for r in data if r.get("h3_cell") == cell]
        if horizon:
            data = [r for r in data if r.get("horizon_h") == horizon]
        return ok(data)

    q = (
        db.table("forecasts")
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
    db=Depends(get_db)
) -> dict:
    """Ranked enforcement worklist for the city."""
    if DEMO_MODE:
        data = fixture("enforcement")
        if status:
            data = [r for r in data if r.get("status") == status]
        return ok(data[:limit])

    q = (
        db.table("enforcement_recs")
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
def enforcement_dossier(rec_id: int, db=Depends(get_db)) -> dict:
    """Full evidence dossier for an enforcement recommendation, with RAG citations.

    Includes: rationale, regulatory citations, rubric score, suggested notice text,
    and (Stage 2, Sejal E6) satellite patch.
    """
    from agents.enforcement import build_dossier
    try:
        dossier = build_dossier(rec_id)
        return ok(dossier)
    except Exception as e:
        return err("dossier_error", str(e))


@app.post("/enforcement/{rec_id}/status", tags=["enforcement"])
def enforcement_update_status(rec_id: int, body: dict, db=Depends(get_db)) -> dict:
    """Update enforcement rec status (approved / dispatched / dismissed)."""
    new_status = body.get("status")
    valid_statuses = {"proposed", "approved", "dispatched", "dismissed"}
    if new_status not in valid_statuses:
        return err("bad_request", f"status must be one of {valid_statuses}")

    if DEMO_MODE:
        return ok({"rec_id": rec_id, "status": new_status, "demo": True})

    db.table("enforcement_recs").update({"status": new_status}).eq("id", rec_id).execute()
    return ok({"rec_id": rec_id, "status": new_status})


# ---------------------------------------------------------------------------
# Advisory
# ---------------------------------------------------------------------------

@app.get("/advisory", tags=["advisory"])
def advisory(
    city: str = Query(..., description="City ID"),
    ward: Optional[str] = Query(None, description="Ward name/ID"),
    lang: str = Query("en", description="Language code: en|hi|kn|mr"),
    db=Depends(get_db)
) -> dict:
    """Ward-level citizen health advisories in specified language."""
    if DEMO_MODE:
        data = fixture("advisory")
        if ward:
            data = [r for r in data if r.get("ward_id") == ward]
        if lang:
            data = [r for r in data if not r.get("language") or r.get("language") == lang]
        return ok(data)

    q = (
        db.table("advisories")
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
# Agent query (orchestrator entry point)
# ---------------------------------------------------------------------------

class AgentQueryBody(BaseModel):
    city: str = "delhi"
    query: str = ""
    focus_cells: Optional[list[str]] = None


@app.post("/agent/query", tags=["agent"])
def agent_query(body: AgentQueryBody, db=Depends(get_db)) -> dict:
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
def simulate(body: SimulateBody, db=Depends(get_db)) -> dict:
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
def optimize(body: OptimizeBody, db=Depends(get_db)) -> dict:
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
def admin_onboard_city(body: CityBody, db=Depends(get_db)) -> dict:
    """Onboard a new city (config-driven, zero code change)."""
    if not body.city_id:
        return err("bad_request", "city_id is required")
    if DEMO_MODE:
        return ok({"onboarded": body.city_id, "demo": True})

    # Upsert city row
    db.table("cities").upsert({
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
    db=Depends(get_db)
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
        db.table("action_traces")
        .select("*")
        .eq("city_id", city)
        .order("signal_ts", desc=True)
        .limit(limit)
        .execute()
        .data
    )
    return ok(rows)


# ---------------------------------------------------------------------------
# WebSocket — /live
# ---------------------------------------------------------------------------

@app.websocket("/live")
async def websocket_live(ws: WebSocket, city: str = "delhi"):
    """WebSocket push of attribution/forecast/alert updates."""
    token = None
    if not DEMO_MODE:
        token = ws.query_params.get("token")
        if not token:
            auth_header = ws.headers.get("authorization", "")
            if auth_header.lower().startswith("bearer "):
                token = auth_header.split(" ", 1)[1]
        if not token:
            await ws.close(code=1008, reason="Missing authorization token")
            return
        try:
            payload = _decode_bearer_payload(token)
        except HTTPException:
            await ws.close(code=1008, reason="Invalid token format")
            return
        role = payload.get("role", "")
        if role not in ("authenticated", "service_role", "admin"):
            await ws.close(code=1008, reason="Insufficient role privileges")
            return

    await ws.accept()
    if DEMO_MODE:
        db = None
    else:
        from core.supa import anon_client
        db = anon_client()
        db.postgrest.auth(token)

    try:
        while True:
            if DEMO_MODE:
                payload = {
                    "city": city,
                    "aqi": fixture("aqi_current"),
                    "attribution": fixture("attribution"),
                    "forecast": fixture("forecast"),
                }
            else:
                try:
                    # In a real app we'd query the DB or use Supabase Realtime
                    # Here we poll latest data to push
                    measurements = db.table("measurements").select("h3_cell,ts,value").eq("city_id", city).eq("variable", "pm25").order("ts", desc=True).limit(50).execute().data
                    payload = {
                        "city": city,
                        "aqi": measurements,
                        "ts": datetime.now(timezone.utc).isoformat()
                    }
                except Exception:
                    payload = {"error": "Failed to fetch live data"}

            await ws.send_json(ok(payload))
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await ws.close()
        except Exception:
            pass
