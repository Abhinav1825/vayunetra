"""Canonical data contracts shared across connectors, agents, ML, and the API.

These Pydantic models mirror the SQL tables in
``supabase/migrations/20260627000001_init.sql`` and the API envelope in
``docs/API_CONTRACT.md``. Keep the three in sync — they are the project's seams.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# --- enums (closed vocabularies; keep aligned with the SQL CHECKs) ----------
class Variable(str, Enum):
    pm25 = "pm25"
    pm10 = "pm10"
    no2 = "no2"
    so2 = "so2"
    co = "co"
    o3 = "o3"
    aod = "aod"
    fire = "fire"
    wind_u = "wind_u"
    wind_v = "wind_v"
    blh = "blh"
    temp = "temp"
    rh = "rh"
    precip = "precip"
    traffic = "traffic"


class Source(str, Enum):
    caaqms = "caaqms"
    openaq = "openaq"
    s5p = "s5p"
    modis = "modis"
    s2 = "s2"
    openmeteo = "openmeteo"
    osm_gtfs = "osm_gtfs"


class SourceCategory(str, Enum):
    traffic = "traffic"
    construction_dust = "construction_dust"
    industrial = "industrial"
    biomass_burning = "biomass_burning"
    transported = "transported"
    other = "other"


# --- the universal record (every connector normalises to this) --------------
class CanonicalMeasurement(BaseModel):
    city_id: str
    h3_cell: str                     # res 8
    station_id: Optional[str] = None
    ts: datetime
    variable: Variable
    value: float
    unit: str
    source: Source
    confidence: float = 1.0


# --- API envelope (see docs/API_CONTRACT.md) --------------------------------
class Meta(BaseModel):
    total: Optional[int] = None
    page: Optional[int] = None
    limit: Optional[int] = None


class ApiError(BaseModel):
    code: str
    message: str


class Envelope(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    error: Optional[ApiError] = None
    meta: Optional[Meta] = None


def ok(data: Any = None, meta: Optional[Meta] = None) -> dict:
    """Success envelope as a plain dict (FastAPI-serialisable)."""
    return Envelope(success=True, data=data, meta=meta).model_dump(exclude_none=True)


def err(code: str, message: str) -> dict:
    """Error envelope as a plain dict."""
    return Envelope(success=False, error=ApiError(code=code, message=message)).model_dump(
        exclude_none=True
    )
