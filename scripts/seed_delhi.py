"""Delhi seed generator (F6 helper).  Owner: Omkar.

Generates synthetic-but-plausible Delhi measurements so the WHOLE team has queryable
data on day 1 — even before the real CAAQMS connector lands. Writes a fixture by default;
``--push`` inserts into Supabase. Replace with real CPCB pulls once connectors exist.

  python scripts/seed_delhi.py            # -> demo/fixtures/measurements.json
  python scripts/seed_delhi.py --push     # also insert into Supabase (needs SUPABASE_* env)
"""
from __future__ import annotations

import argparse
import json
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:  # load .env so --push picks up SUPABASE_* without manual export
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

# Sample H3 res-8 cells across Delhi (placeholders; regenerate from delhi.yml bbox + h3 later)
DELHI_CELLS = ["883da1a3a1fffff", "883da1a3a3fffff", "883da1a3a5fffff", "883da1a3a7fffff"]

# variable -> (low, high) plausible range
VARS = {
    "pm25": (40, 220), "pm10": (80, 400), "no2": (10, 90),
    "so2": (3, 30), "co": (0.4, 2.5), "o3": (10, 80),
}


def generate(days: int = 3) -> list[dict]:
    rows: list[dict] = []
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    for h in range(days * 24):
        ts = now - timedelta(hours=h)
        # crude diurnal cycle: morning + evening peaks
        diurnal = 1 + 0.4 * math.sin((ts.hour / 24) * 2 * math.pi)
        for cell in DELHI_CELLS:
            for var, (lo, hi) in VARS.items():
                value = random.uniform(lo, hi) * diurnal
                rows.append({
                    "city_id": "delhi",
                    "h3_cell": cell,
                    "station_id": None,
                    "ts": ts.isoformat(),
                    "variable": var,
                    "value": round(value, 2),
                    "unit": "mg/m3" if var == "co" else "ug/m3",
                    "source": "caaqms",
                    "confidence": 1.0,
                })
    return rows


def push_to_supabase(rows: list[dict]) -> None:
    import os

    from supabase import create_client

    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    for i in range(0, len(rows), 500):
        client.table("measurements").insert(rows[i : i + 500]).execute()
    print(f"pushed {len(rows)} rows to Supabase")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--push", action="store_true", help="insert into Supabase too")
    args = ap.parse_args()

    rows = generate(args.days)
    out = Path(__file__).resolve().parent.parent / "demo" / "fixtures" / "measurements.json"
    out.write_text(json.dumps(rows, indent=2))
    print(f"wrote {len(rows)} rows -> {out}")
    if args.push:
        push_to_supabase(rows)


if __name__ == "__main__":
    main()
