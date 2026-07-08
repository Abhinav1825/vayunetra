"""Agent 1 Attribution runner.  ARCHITECTURE.md §9.1; PLAN §2A/§3A.

Builds each cell's source shares -> writes the `attribution` table (one row per
cell × source_category, the long format the blame map reads).

Primary method: hybrid GBM+SHAP apportionment blended with chemical-signature
priors (ml.attribution.shap_attribution). Falls back to pure signature priors
when a city's history is too thin to train on.

  python -m ml.attribution.attribute --city delhi                 # compute + print
  python -m ml.attribution.attribute --city delhi --write         # also write to Supabase
  python -m ml.attribution.attribute --city delhi --signature-only  # skip the GBM
"""
from __future__ import annotations

import argparse
from datetime import timedelta

import pandas as pd

from core.supa import client, load_measurements

from .signatures import calibrate_references, signature_shares

POLLUTANTS = ["pm25", "pm10", "no2", "so2", "co", "o3", "fire", "no2_sat"]
METHOD = "signature-v1"
METHOD_HYBRID = "hybrid-gbm-shap-v2"


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


def build_rows(
    city_id: str, per_cell: dict[str, dict], window_end: pd.Timestamp, refs: dict | None = None
) -> list[dict]:
    lo = (window_end - timedelta(hours=1)).isoformat()
    ts_window = f"[{lo},{window_end.isoformat()})"   # PostgREST tstzrange literal
    rows: list[dict] = []
    for cell, vals in per_cell.items():
        shares, confidence, evidence = signature_shares(vals, refs)
        for category, share in shares.items():
            rows.append({
                "city_id": city_id, "h3_cell": cell, "ts_window": ts_window,
                "source_category": category, "share": share, "confidence": confidence,
                "method_version": METHOD, "evidence": evidence,
            })
    return rows


def _apply_hybrid(
    rows: list[dict], long_df: pd.DataFrame, per_cell: dict[str, dict], refs: dict
) -> tuple[list[dict], str]:
    """Upgrade signature rows to hybrid GBM+SHAP shares where trainable."""
    from .shap_attribution import apportion_cells, build_wide

    sig_by_cell = {cell: signature_shares(vals, refs)[0] for cell, vals in per_cell.items()}
    wide = build_wide(long_df)
    hybrid, r2 = apportion_cells(wide, sig_by_cell)

    upgraded: list[dict] = []
    for row in rows:
        cell = row["h3_cell"]
        ap = hybrid.get(cell)
        if ap is None:
            upgraded.append(row)  # cell too sparse -> keep the signature row
            continue
        upgraded.append({
            **row,
            "share": ap.shares.get(row["source_category"], 0.0),
            "confidence": ap.confidence,
            "method_version": METHOD_HYBRID,
            "evidence": {**row["evidence"], "shap_drivers": ap.shap_drivers, "model_r2": round(r2, 3)},
        })
    n_upgraded = len({r["h3_cell"] for r in upgraded if r["method_version"] == METHOD_HYBRID})
    print(f"  hybrid GBM+SHAP: upgraded {n_upgraded} cells (holdout R2={r2:.2f})")
    return upgraded, METHOD_HYBRID


def run(city_id: str, write: bool = False, signature_only: bool = False) -> None:
    long_df = pd.DataFrame(load_measurements(city_id))
    # data-driven marker scales (p90) so blame tracks current conditions, not a fixed season
    pdf = long_df[long_df["variable"].isin(POLLUTANTS)]
    refs = calibrate_references({var: g["value"].tolist() for var, g in pdf.groupby("variable")})
    per_cell, window_end = latest_pollutants(long_df)
    rows = build_rows(city_id, per_cell, window_end, refs)
    method = METHOD

    if not signature_only:
        try:
            rows, method = _apply_hybrid(rows, long_df, per_cell, refs)
        except Exception as e:  # noqa: BLE001 — thin data / SHAP issues -> honest fallback
            print(f"  hybrid unavailable ({e}); using signature priors")

    print(f"{city_id}: {len(per_cell)} cells -> {len(rows)} attribution rows (method={method})")
    by_cell: dict[str, list[dict]] = {}
    for r in rows:
        by_cell.setdefault(r["h3_cell"], []).append(r)
    for cell, cell_rows in list(by_cell.items())[:3]:
        top = max(cell_rows, key=lambda r: r["share"])
        print(f"  {cell}: dominant={top['source_category']} ({top['share']:.0%}) conf={top['confidence']}")

    if write:
        client().table("attribution").delete().eq("city_id", city_id).execute()
        client().table("attribution").insert(rows).execute()
        print(f"wrote {len(rows)} attribution rows")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="delhi")
    ap.add_argument("--write", action="store_true", help="write to Supabase")
    ap.add_argument("--signature-only", action="store_true", help="skip the GBM+SHAP upgrade")
    args = ap.parse_args()
    run(args.city, write=args.write, signature_only=args.signature_only)


if __name__ == "__main__":
    main()
