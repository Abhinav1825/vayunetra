"""E6 multimodal evidence helpers.

Runtime code stays lean: no torch/CLIP import here. The offline ingest path stores
precomputed or deterministic embeddings in ``kb_chunks`` with ``modality='image'``;
the API only reads those rows and source metadata.
"""
from __future__ import annotations

import base64
import hashlib
import math
from typing import Any

EMBEDDING_DIM = 384


def hash_embed(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """Deterministic 384-d fallback embedding for image metadata/search text."""
    vec = [0.0] * dim
    for token in text.lower().split():
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        idx = int.from_bytes(digest[:4], "little") % dim
        sign = 1.0 if digest[4] & 1 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def source_coordinates(source: dict[str, Any]) -> list[float] | None:
    geom = source.get("geom") or {}
    coords = geom.get("coordinates") if isinstance(geom, dict) else None
    if isinstance(coords, list) and len(coords) >= 2:
        return [float(coords[0]), float(coords[1])]
    attrs = source.get("attributes") or {}
    coords = attrs.get("coordinates")
    if isinstance(coords, list) and len(coords) >= 2:
        return [float(coords[0]), float(coords[1])]
    return None


def patch_ref_from_source(source: dict[str, Any]) -> str | None:
    attrs = source.get("attributes") or {}
    for key in (
        "sentinel2_patch_url",
        "satellite_patch_url",
        "patch_url",
        "image_ref",
        "thumbnail_url",
    ):
        val = attrs.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def placeholder_patch_data_uri(source: dict[str, Any]) -> str:
    """Demo-only illustrative marker — clearly labeled: NOT satellite imagery."""
    coords = source_coordinates(source) or [77.22, 28.61]
    name = (source.get("name") or f"source {source.get('id', '')}")[:38]
    kind = (source.get("type") or "source").replace("_", " ")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="360" height="240" viewBox="0 0 360 240">
<defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="1"><stop stop-color="#6b7f59"/><stop offset=".45" stop-color="#c9b37a"/><stop offset="1" stop-color="#4f6d7a"/></linearGradient></defs>
<rect width="360" height="240" fill="url(#g)"/>
<path d="M0 164 C58 135 93 156 151 126 S248 88 360 104 L360 240 L0 240 Z" fill="#a3895e" opacity=".58"/>
<path d="M20 38 L338 208 M-18 86 L287 242 M86 -12 L360 142" stroke="#e8dfc4" stroke-width="5" opacity=".45"/>
<rect x="128" y="66" width="104" height="70" fill="#d7c58c" opacity=".82"/>
<rect x="143" y="79" width="74" height="44" fill="#9d7b4c" opacity=".78"/>
<rect x="14" y="156" width="332" height="70" rx="6" fill="rgba(15,23,42,.78)"/>
<text x="26" y="180" fill="#fff" font-family="Arial" font-size="16" font-weight="700">Illustrative site marker (not satellite imagery)</text>
<text x="26" y="201" fill="#dbeafe" font-family="Arial" font-size="12">{name} · {kind}</text>
<text x="26" y="218" fill="#d1d5db" font-family="Arial" font-size="11">{coords[1]:.4f}, {coords[0]:.4f} · Sentinel-2 patch pending ingest</text>
</svg>"""
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def image_chunk_from_source(source: dict[str, Any], allow_placeholder: bool = False) -> dict[str, Any] | None:
    image_ref = patch_ref_from_source(source)
    placeholder_used = False
    if not image_ref and allow_placeholder:
        image_ref = placeholder_patch_data_uri(source)
        placeholder_used = True
    if not image_ref:
        return None

    coords = source_coordinates(source)
    source_id = source.get("id")
    city_id = source.get("city_id")
    name = source.get("name") or f"Detected source {source_id}"
    kind = (source.get("type") or "cv_detected").replace("_", " ")
    origin = source.get("source_origin")
    confidence = source.get("detection_confidence")

    # Only a real image of a CV-detected source may claim to be Sentinel-2
    # evidence — an OSM registry site with a drawn marker must say exactly that.
    if placeholder_used or origin != "cv_detected":
        title = f"Site marker - {name}"
        source_url = "VayuNetra source registry (illustrative marker)"
        chunk_text = (
            f"Illustrative location marker for {name} ({kind}, {origin or 'registry'} origin) "
            f"in {city_id}. No Sentinel-2 evidence patch ingested yet."
        )
    else:
        title = f"Sentinel-2 patch - {name}"
        source_url = "Sentinel-2 / VayuNetra CV detection"
        chunk_text = (
            f"Sentinel-2 image patch for {name}. CV-detected {kind} source "
            f"in {city_id}; detection confidence {confidence}."
        )

    metadata = {
        "source_id": source_id,
        "city_id": city_id,
        "source_type": source.get("type") or "cv_detected",
        "source_origin": origin,
        "detection_confidence": confidence,
        "coordinates": coords,
        "placeholder": placeholder_used,
    }
    return {
        "doc_id": f"sentinel2-source-{source_id}",
        "title": title,
        "source_url": source_url,
        "modality": "image",
        "chunk_text": chunk_text,
        "image_ref": image_ref,
        "embedding": hash_embed(f"{chunk_text} {coords or ''}"),
        "metadata": metadata,
    }


def _metadata(row: dict[str, Any]) -> dict[str, Any]:
    meta = row.get("metadata") or {}
    return meta if isinstance(meta, dict) else {}


def find_image_patch(
    db: Any,
    rec: dict[str, Any],
    source: dict[str, Any] | None = None,
    allow_placeholder: bool = True,
) -> dict[str, Any] | None:
    """Best image evidence row for an enforcement recommendation.

    ``allow_placeholder=False`` (the live path) returns only real ingested
    image chunks — a dossier must never show generated imagery as evidence.
    """
    source_id = rec.get("source_id")
    city_id = rec.get("city_id")
    rows = (
        db.table("kb_chunks")
        .select("id,doc_id,title,source_url,chunk_text,image_ref,metadata")
        .eq("modality", "image")
        .limit(500)
        .execute()
        .data
    )

    def score(row: dict[str, Any]) -> int:
        meta = _metadata(row)
        if source_id is not None and str(meta.get("source_id")) == str(source_id):
            return 3
        if city_id and meta.get("city_id") == city_id:
            return 1
        return 0

    ranked = sorted((r for r in rows if r.get("image_ref")), key=score, reverse=True)
    if ranked and score(ranked[0]) > 0:
        row = ranked[0]
        meta = _metadata(row)
        return {
            "title": row.get("title") or "Sentinel-2 patch",
            "image_ref": row.get("image_ref"),
            "source_url": row.get("source_url"),
            "excerpt": row.get("chunk_text"),
            "similarity": 1.0 if str(meta.get("source_id")) == str(source_id) else 0.72,
            "metadata": meta,
        }

    if source and allow_placeholder:
        chunk = image_chunk_from_source(source, allow_placeholder=True)
        if chunk:
            return {
                "title": chunk["title"],
                "image_ref": chunk["image_ref"],
                "source_url": chunk["source_url"],
                "excerpt": chunk["chunk_text"],
                "similarity": 0.68,
                "metadata": chunk["metadata"],
            }
    return None
