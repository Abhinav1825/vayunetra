"""Seed a minimal live emission-source registry so enforcement can score real rows.

This is the shortest path to making `enforcement_recs` nonzero in the live DB.

Usage:
    python scripts/seed_emission_sources.py
    python scripts/seed_emission_sources.py --cities delhi bengaluru mumbai
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import core.env  # noqa: F401
from core.supa import client


DEFAULT_SOURCES = [
    {
        "name": "Sarai Kale Khan Construction Site",
        "type": "construction",
        "source_origin": "registry",
        "detection_confidence": 1.0,
        "attributes": {"permit": "DMRC-2025-4421", "area_sqm": 45000, "pop_exposed_estimate": 18400},
    },
    {
        "name": "Mayapuri Industrial Cluster",
        "type": "industry",
        "source_origin": "registry",
        "detection_confidence": 1.0,
        "attributes": {"consent_id": "DPCC-2024-IND-1102", "sector": "metal_recycling", "pop_exposed_estimate": 9200},
    },
    {
        "name": "Timarpur Waste Burning Site",
        "type": "waste_burn",
        "source_origin": "registry",
        "detection_confidence": 0.85,
        "attributes": {"ward": "Timarpur Ward 12", "pop_exposed_estimate": 6500},
    },
]


def seed_city(city_id: str) -> int:
    db = client()
    rows = []
    for source in DEFAULT_SOURCES:
        rows.append({
            "city_id": city_id,
            "name": source["name"],
            "type": source["type"],
            "source_origin": source["source_origin"],
            "detection_confidence": source["detection_confidence"],
            "attributes": source["attributes"],
            "geom": None,
        })

    db.table("emission_sources").delete().eq("city_id", city_id).execute()
    db.table("emission_sources").insert(rows).execute()
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed live emission_sources rows")
    parser.add_argument("--cities", nargs="+", default=["delhi", "bengaluru", "mumbai"])
    args = parser.parse_args()

    for city_id in args.cities:
        count = seed_city(city_id)
        print(f"{city_id}: seeded {count} emission_sources rows")


if __name__ == "__main__":
    main()