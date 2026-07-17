"""Ingest E6 Sentinel-2 patch evidence into kb_chunks.

Reads ``emission_sources`` rows with ``source_origin='cv_detected'`` and writes
one ``kb_chunks`` row per source with ``modality='image'``. The image reference is
taken from source attributes such as ``sentinel2_patch_url`` or ``patch_url``.

This is intentionally lean: it uses deterministic metadata embeddings unless an
offline ML workflow has already supplied patch URLs. The API never imports torch.

Usage:
    DEMO_MODE=false python scripts/ingest_e6_image_patches.py --city delhi
    DEMO_MODE=false python scripts/ingest_e6_image_patches.py --city delhi --allow-placeholder
"""
from __future__ import annotations

import argparse
from typing import Any

import core.env  # noqa: F401
from core.supa import client
from rag.multimodal import image_chunk_from_source


def _fetch_sources(db: Any, city: str | None) -> list[dict]:
    q = (
        db.table("emission_sources")
        .select("id,city_id,geom,type,name,source_origin,detection_confidence,attributes")
        .eq("source_origin", "cv_detected")
        .limit(1000)
    )
    if city:
        q = q.eq("city_id", city)
    return q.execute().data


def ingest(city: str | None = None, allow_placeholder: bool = False) -> dict:
    db = client()
    sources = _fetch_sources(db, city)
    rows = []
    skipped = 0
    for src in sources:
        row = image_chunk_from_source(src, allow_placeholder=allow_placeholder)
        if row:
            rows.append(row)
        else:
            skipped += 1

    if rows:
        doc_ids = [r["doc_id"] for r in rows]
        db.table("kb_chunks").delete().in_("doc_id", doc_ids).execute()
        db.table("kb_chunks").insert(rows).execute()

    return {"sources": len(sources), "upserted": len(rows), "skipped_no_patch_ref": skipped}


def main() -> None:
    parser = argparse.ArgumentParser(description="Index Sentinel-2 image patch evidence for E6.")
    parser.add_argument("--city", help="Optional city_id filter, e.g. delhi")
    parser.add_argument(
        "--allow-placeholder",
        action="store_true",
        help="Create a labeled visual marker when a source lacks a real patch URL.",
    )
    args = parser.parse_args()
    result = ingest(city=args.city, allow_placeholder=args.allow_placeholder)
    print(
        "[e6] indexed {upserted}/{sources} cv_detected sources "
        "({skipped_no_patch_ref} skipped without patch refs)".format(**result)
    )


if __name__ == "__main__":
    main()
