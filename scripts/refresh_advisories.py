"""Regenerate citizen advisories from the CURRENT forecasts.

Surgical version of run_sejal_stage1 --push: touches ONLY the advisories
table (the full script would also re-insert its synthetic registry rows next
to the OSM-ingested emission_sources). Cron-safe and idempotent.

Run:
    python scripts/refresh_advisories.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import core.env  # noqa: F401


def main() -> None:
    from connectors.static_layers import build_static_layers
    from scripts.run_sejal_stage1 import _cities, _replace_advisories

    cities = _cities()
    layers = {c["city_id"]: build_static_layers(c["city_id"]) for c in cities}
    total = _replace_advisories(cities, layers)
    print(f"advisories refreshed: {total} rows across {len(cities)} cities")


if __name__ == "__main__":
    main()
