"""Run E1 CV inference on a REAL Sentinel-2 tile and write cv_detected rows.

Honest end-to-end path, runnable on any machine with the ML stack:
1. Export a genuine Sentinel-2 RGB (B4/B3/B2) median composite for a city
   sub-bbox via Earth Engine (same bands the model trained on).
2. Run the committed U-Net weights (artifacts/e1_cv_model.pth).
3. Write detections to emission_sources(source_origin='cv_detected') with
   real polygon centroids -> H3 cells. Idempotent per city.

Usage:  python scripts/run_e1_inference_live.py --city delhi --push
"""
from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import core.env  # noqa: F401

CLASS_TO_TYPE = {"construction": "construction", "kiln": "industry",
                 "burn": "waste_burn", "industry": "industry"}
POP_ESTIMATE = {"construction": 15000, "industry": 12000, "waste_burn": 9000}


def fetch_s2_tile(city_id: str, out_path: str, size_deg: float = 0.05) -> str:
    """Download a real S2 RGB GeoTIFF around the city centre via EE."""
    import ee
    import requests
    import yaml

    from connectors.earth_engine import init

    init()
    cfg = yaml.safe_load((REPO / "core/config/cities" / f"{city_id}.yml").read_text())
    lng, lat = cfg["center"]
    region = ee.Geometry.Rectangle([lng - size_deg, lat - size_deg, lng + size_deg, lat + size_deg])
    img = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate("2026-01-01", "2026-07-01")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .median()
        .select(["B4", "B3", "B2"])
        .clip(region)
        # match the training tiles exactly: the GEE export script produced
        # visualize(min:0, max:3000) 8-bit RGB, so inference's /10000 puts
        # training inputs at ~0-0.0255 — raw reflectance would be out of
        # distribution and the CNN predicts background everywhere.
        .visualize(**{"min": 0, "max": 3000})
    )
    url = img.getDownloadURL({"scale": 10, "region": region, "format": "GEO_TIFF"})
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    content = r.content
    if content[:2] == b"PK":  # zip fallback
        z = zipfile.ZipFile(io.BytesIO(content))
        name = [n for n in z.namelist() if n.endswith(".tif")][0]
        content = z.read(name)
    Path(out_path).write_bytes(content)
    print(f"{city_id}: S2 tile downloaded ({len(content)/1e6:.1f} MB)")
    return out_path


def detections_to_rows(city_id: str, gdf) -> list[dict]:
    from core.spatial.h3_utils import latlng_to_cell

    rows = []
    for i, rec in enumerate(gdf.itertuples(), 1):
        c = rec.geometry.centroid
        stype = CLASS_TO_TYPE.get(getattr(rec, "type", "construction"), "construction")
        rows.append({
            "city_id": city_id,
            "name": f"CV detection #{i} ({stype})",
            "type": stype,
            "registry_ref": f"e1_cv:{city_id}:{i}",
            "source_origin": "cv_detected",
            "detection_confidence": round(float(getattr(rec, "detection_confidence", 0.8)), 3),
            "geom": {"type": "Point", "coordinates": [round(c.x, 6), round(c.y, 6)]},
            "attributes": {
                "h3_cell": latlng_to_cell(c.y, c.x, 8),
                "pop_exposed_estimate": POP_ESTIMATE.get(stype, 9000),
                "model": "e1_cv_model.pth (U-Net resnet34, Kaggle-trained)",
            },
        })
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="delhi")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--max-patches", type=int, default=12)
    args = ap.parse_args()

    from ml.vision.inference import CVSourceDetector, HAS_TORCH

    if not HAS_TORCH:
        raise SystemExit("torch missing — refusing mock mode (fake detections). Install requirements-ml.")

    tif = f"/tmp/s2_{args.city}.tif"
    fetch_s2_tile(args.city, tif)
    det = CVSourceDetector()
    gdf = det.infer_large_tile(tif, max_patches=args.max_patches)
    print(f"{args.city}: {len(gdf)} detections from the real CNN")
    if len(gdf) == 0:
        return
    rows = detections_to_rows(args.city, gdf)
    for r in rows[:5]:
        print(f"   {r['type']:13s} conf={r['detection_confidence']} @ {r['geom']['coordinates']}")
    if args.push:
        from core.supa import client

        db = client()
        db.table("emission_sources").delete().eq("city_id", args.city).eq("source_origin", "cv_detected").execute()
        db.table("emission_sources").insert(rows).execute()
        print(f"{args.city}: wrote {len(rows)} cv_detected rows")


if __name__ == "__main__":
    main()
