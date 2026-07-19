"""Construction-permit registry connector — the integration point, ready.

The PS names "construction permits" as an attribution input. No Indian city
publishes a machine-readable permit registry today (DPCC's dust-control portal
is a web form; MCD/BBMP/MCGM building permissions are not open data), so this
connector ships EMPTY by design: the moment a municipality provides a CSV
export, one command fuses it into the same `emission_sources` registry the
attribution and enforcement agents already read.

Expected CSV schema (data/permits/{city}.csv):

    permit_id,site_name,lat,lon,valid_from,valid_to,area_sqm,dust_plan
    DPCC-2026-0142,Metro Phase-4 C6,28.6139,77.2090,2026-01-15,2027-06-30,12000,true

  python -m connectors.permits --city delhi           # parse + summary
  python -m connectors.permits --city delhi --push    # upsert into emission_sources
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import core.env  # noqa: F401

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "permits"


def parse_permits(path: Path) -> list[dict]:
    """CSV -> emission_sources-shaped rows (pure; tested). Bad rows skipped."""
    rows: list[dict] = []
    with path.open(newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            try:
                lat, lon = float(raw["lat"]), float(raw["lon"])
            except (KeyError, TypeError, ValueError):
                continue
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                continue
            permit_id = (raw.get("permit_id") or "").strip()
            if not permit_id:
                continue
            rows.append({
                "name": (raw.get("site_name") or permit_id).strip(),
                "type": "construction",
                "source_origin": "permit_registry",
                "registry_ref": permit_id,
                "detection_confidence": 1.0,  # registered = ground truth, not detected
                "geom": {"type": "Point", "coordinates": [lon, lat]},
                "attributes": {
                    "valid_from": raw.get("valid_from"),
                    "valid_to": raw.get("valid_to"),
                    "area_sqm": raw.get("area_sqm"),
                    "dust_plan": str(raw.get("dust_plan", "")).lower() in ("true", "1", "yes"),
                },
            })
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="delhi")
    ap.add_argument("--push", action="store_true")
    args = ap.parse_args()

    path = DATA_DIR / f"{args.city}.csv"
    if not path.exists():
        print(f"No permit registry at {path} — no Indian city publishes one as open data yet.\n"
              "The moment one does: drop the CSV there and re-run with --push.")
        return
    rows = parse_permits(path)
    print(f"{args.city}: {len(rows)} valid permit rows parsed")
    if args.push and rows:
        from core.supa import client

        db = client()
        for r in rows:
            r["city_id"] = args.city
        for i in range(0, len(rows), 200):
            db.table("emission_sources").upsert(rows[i : i + 200], on_conflict="registry_ref").execute()
        print(f"{args.city}: upserted {len(rows)} permit-registered sources")


if __name__ == "__main__":
    main()
