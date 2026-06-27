"""OpenAQ ground-AQI connector (v3).  Owner: Omkar.  Spec: ARCHITECTURE.md §7.1; PRD §11.

Pulls real station PM2.5/PM10/NO2/SO2/CO/O3 (hourly history) near a city, maps each
station to its H3 cell, and writes canonical `measurements`. This is what turns the
forecast skill score into a *real* number (it replaces the synthetic seed target).

Needs a free key:  OPENAQ_API_KEY in .env  (sign up at https://openaq.org).

  python -m connectors.openaq --city delhi --days 14            # fetch + summary
  python -m connectors.openaq --city delhi --days 14 --push     # insert into Supabase
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import requests

import core.env  # noqa: F401  (loads .env)
from core.spatial.h3_utils import latlng_to_cell

BASE = "https://api.openaq.org/v3"
CITIES_DIR = Path(__file__).resolve().parent.parent / "core" / "config" / "cities"

# OpenAQ parameter name -> our canonical variable
PARAM_MAP = {"pm25": "pm25", "pm10": "pm10", "no2": "no2", "so2": "so2", "co": "co", "o3": "o3"}


def load_city(city_id: str) -> dict:
    import yaml

    return yaml.safe_load((CITIES_DIR / f"{city_id}.yml").read_text())


def rows_from_records(city_id: str, records: list[dict], h3_res: int = 8) -> list[dict]:
    """Normalised records -> canonical measurement rows (pure; unit-tested).

    Each record: {lat, lng, variable, value, unit, ts, station_id}.
    Records whose variable isn't one of our pollutants are skipped.
    """
    rows: list[dict] = []
    for r in records:
        if r.get("variable") not in PARAM_MAP.values():
            continue
        if r.get("value") is None or r.get("lat") is None or r.get("lng") is None:
            continue
        rows.append({
            "city_id": city_id,
            "h3_cell": latlng_to_cell(float(r["lat"]), float(r["lng"]), h3_res),
            "station_id": r.get("station_id"),
            "ts": r["ts"],
            "variable": r["variable"],
            "value": float(r["value"]),
            "unit": r.get("unit"),
            "source": "openaq",
            "confidence": 1.0,
        })
    return rows


# --- OpenAQ v3 HTTP (network; verify on first live run) -------------------
def _get(path: str, params: dict) -> dict:
    key = os.environ.get("OPENAQ_API_KEY")
    if not key:
        raise RuntimeError("OPENAQ_API_KEY missing in .env — sign up at https://openaq.org")
    resp = requests.get(f"{BASE}{path}", params=params, headers={"X-API-Key": key}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def find_sensors(lat: float, lng: float, radius_m: int = 25000) -> list[dict]:
    """Sensors for our pollutants at stations within `radius_m` of the city centre."""
    data = _get("/locations", {"coordinates": f"{lat},{lng}", "radius": radius_m, "limit": 100})
    sensors: list[dict] = []
    for loc in data.get("results", []):
        coords = loc.get("coordinates") or {}
        for s in loc.get("sensors", []):
            pname = (s.get("parameter") or {}).get("name")
            if pname in PARAM_MAP:
                sensors.append({
                    "sensor_id": s["id"],
                    "variable": PARAM_MAP[pname],
                    "unit": (s.get("parameter") or {}).get("units"),
                    "lat": coords.get("latitude"),
                    "lng": coords.get("longitude"),
                    "station_id": str(loc.get("id")),
                })
    return sensors


def fetch_sensor_hourly(sensor: dict, datetime_from: str) -> list[dict]:
    """Hourly history for one sensor since `datetime_from` (ISO) -> normalised records."""
    records: list[dict] = []
    page = 1
    while True:
        data = _get(
            f"/sensors/{sensor['sensor_id']}/measurements/hourly",
            {"datetime_from": datetime_from, "limit": 1000, "page": page},
        )
        results = data.get("results", [])
        for m in results:
            period = (m.get("period") or {}).get("datetimeFrom") or {}
            records.append({
                "lat": sensor["lat"], "lng": sensor["lng"],
                "variable": sensor["variable"],
                "value": m.get("value"),
                "unit": sensor["unit"],
                "ts": period.get("utc"),
                "station_id": sensor["station_id"],
            })
        if len(results) < 1000:
            break
        page += 1
    return records


def fetch_city(city_id: str, days: int = 14) -> list[dict]:
    from datetime import datetime, timedelta, timezone

    cfg = load_city(city_id)
    lng, lat = cfg["center"]
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    records: list[dict] = []
    for sensor in find_sensors(lat, lng):
        records.extend(fetch_sensor_hourly(sensor, since))
    return rows_from_records(city_id, records, cfg.get("h3_res", 8))


def push_to_supabase(rows: list[dict]) -> None:
    from supabase import create_client

    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    for i in range(0, len(rows), 500):
        client.table("measurements").insert(rows[i : i + 500]).execute()
    print(f"pushed {len(rows)} OpenAQ measurements to Supabase")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="delhi")
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--push", action="store_true")
    args = ap.parse_args()

    rows = fetch_city(args.city, args.days)
    cells = {r["h3_cell"] for r in rows}
    variables = sorted({r["variable"] for r in rows})
    print(f"{args.city}: {len(rows)} rows · {len(cells)} cells · vars {variables}")
    if args.push:
        push_to_supabase(rows)


if __name__ == "__main__":
    main()
