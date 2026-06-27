"""Agent 1 Attribution runner.  ARCHITECTURE.md §9.1.

Builds each cell's latest pollutant signature -> source shares -> writes the `attribution`
table (one row per cell × source_category, the long format the blame map reads).

  python -m ml.attribution.attribute --city delhi            # compute + print
  python -m ml.attribution.attribute --city delhi --write     # also write to Supabase
"""
from __future__ import annotations

import argparse
from datetime import timedelta

import pandas as pd

from core.supa import client, load_measurements

from .signatures import signature_shares

POLLUTANTS = ["pm25", "pm10", "no2", "so2", "co", "o3", "fire"]
METHOD = "signature-v1"


def latest_pollutants(long_df: pd.DataFrame) -> tuple[dict[str, dict], pd.Timestamp]:
    """Per-cell dict of the most recent value for each pollutant + the overall window end."""
    df = long_df[long_df["variable"].isin(POLLUTANTS)].copy()
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    latest = df.sort_values("ts").groupby(["h3_cell", "variable"]).tail(1)
    per_cell = {
        cell: dict(zip(g["variable"], g["value"]))
        for cell, g in latest.groupby("h3_cell")
    }
    return per_cell, df["ts"].max()


def build_rows(city_id: str, per_cell: dict[str, dict], window_end: pd.Timestamp) -> list[dict]:
    lo = (window_end - timedelta(hours=1)).isoformat()
    ts_window = f"[{lo},{window_end.isoformat()})"   # PostgREST tstzrange literal
    rows: list[dict] = []
    for cell, vals in per_cell.items():
        shares, confidence, evidence = signature_shares(vals)
        for category, share in shares.items():
            rows.append({
                "city_id": city_id, "h3_cell": cell, "ts_window": ts_window,
                "source_category": category, "share": share, "confidence": confidence,
                "method_version": METHOD, "evidence": evidence,
            })
    return rows


def run(city_id: str, write: bool = False) -> None:
    long_df = pd.DataFrame(load_measurements(city_id))
    per_cell, window_end = latest_pollutants(long_df)
    rows = build_rows(city_id, per_cell, window_end)
    print(f"{city_id}: {len(per_cell)} cells -> {len(rows)} attribution rows")
    for cell, vals in list(per_cell.items())[:2]:
        shares, conf, _ = signature_shares(vals)
        dominant = max(shares, key=shares.get)
        print(f"  {cell}: dominant={dominant} ({shares[dominant]:.0%}) conf={conf}")
    if write:
        client().table("attribution").delete().eq("city_id", city_id).execute()
        client().table("attribution").insert(rows).execute()
        print(f"wrote {len(rows)} attribution rows")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="delhi")
    ap.add_argument("--write", action="store_true", help="write to Supabase")
    args = ap.parse_args()
    run(args.city, write=args.write)


if __name__ == "__main__":
    main()
