"""Agent 3 — Enforcement Intelligence & Prioritisation Agent.

Reads attribution + forecast data and the emission source registry, computes an
exposure-weighted priority score for each candidate source, retrieves regulatory
citations via the RAG subsystem, and generates a ranked enforcement worklist with
cited evidence dossiers.

Priority score formula (PRD §12.4):
    priority = source_contribution × population_exposed_norm × actionability × confidence

Each recommendation is written to the ``enforcement_recs`` table (or DEMO fixture).
Owner: Abhinav.
"""
from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import core.env  # noqa: F401

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
FIXTURES = Path(__file__).resolve().parent.parent / "demo" / "fixtures"

# CPCB/GRAP rubric scoring weights (total = 10):
# attribution_match (0–2), actionability (0–2), exposure (0–2),
# regulatory_basis (0–2), confidence (0–1), novelty (0–1)
RUBRIC_MAX = 10


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class AttributionRecord:
    h3_cell: str
    city_id: str
    source_category: str
    share: float            # 0..1
    confidence: float       # 0..1
    evidence: dict = field(default_factory=dict)
    ts_window: Optional[tuple] = None


@dataclass
class EmissionSource:
    id: int
    city_id: str
    name: str
    type: str               # industry, construction, waste_burn, diesel_corridor
    source_origin: str      # registry | cv_detected
    detection_confidence: float = 1.0
    attributes: dict = field(default_factory=dict)
    pop_exposed: int = 0    # derived from spatial join with WorldPop


@dataclass
class EnforcementRec:
    city_id: str
    h3_cell: str
    source_id: int
    priority_score: float
    contribution: float
    pop_exposed: int
    rationale: str
    evidence: dict
    rag_citations: list[dict]
    rubric_score: dict
    status: str = "proposed"
    ts: str = ""

    def to_dict(self) -> dict:
        return {
            "city_id": self.city_id,
            "h3_cell": self.h3_cell,
            "source_id": self.source_id,
            "priority_score": round(self.priority_score, 4),
            "contribution": round(self.contribution, 4),
            "pop_exposed": self.pop_exposed,
            "rationale": self.rationale,
            "evidence": self.evidence,
            "rag_citations": self.rag_citations,
            "rubric_score": self.rubric_score,
            "status": self.status,
            "ts": self.ts or datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Demo data loaders (DEMO_MODE)
# ---------------------------------------------------------------------------

def _load_demo_attribution(city_id: str) -> list[dict]:
    p = FIXTURES / "attribution.json"
    if p.exists():
        data = json.loads(p.read_text())
        # inject city_id
        for row in data:
            row.setdefault("city_id", city_id)
        return data
    return []


def _load_demo_emission_sources(city_id: str) -> list[dict]:
    """Return mock emission sources for DEMO_MODE (substitutes Sejal's registry)."""
    return [
        {
            "id": 101,
            "city_id": city_id,
            "name": "Sarai Kale Khan Construction Site",
            "type": "construction",
            "source_origin": "registry",
            "detection_confidence": 1.0,
            "pop_exposed_estimate": 18400,
            "attributes": {"permit": "DMRC-2025-4421", "area_sqm": 45000},
        },
        {
            "id": 102,
            "city_id": city_id,
            "name": "Mayapuri Industrial Cluster",
            "type": "industry",
            "source_origin": "registry",
            "detection_confidence": 1.0,
            "pop_exposed_estimate": 9200,
            "attributes": {"consent_id": "DPCC-2024-IND-1102", "sector": "metal_recycling"},
        },
        {
            "id": 103,
            "city_id": city_id,
            "name": "Timarpur Waste Burning Site",
            "type": "waste_burn",
            "source_origin": "registry",
            "detection_confidence": 0.85,
            "pop_exposed_estimate": 6500,
            "attributes": {"ward": "Timarpur Ward 12"},
        },
    ]


# ---------------------------------------------------------------------------
# Priority score computation
# ---------------------------------------------------------------------------

_ACTIONABILITY = {
    "construction_dust": 0.95,    # inspectors can verify and fine immediately
    "industrial": 0.85,           # requires more process (stack tests, CTO check)
    "biomass_burning": 0.90,      # immediate cessation possible
    "traffic": 0.55,              # harder to act on — diffuse
    "transported": 0.20,          # largely unactionable locally
    "other": 0.40,
}


def _compute_priority(
    share: float,
    pop_exposed: int,
    source_category: str,
    confidence: float,
    max_pop: int = 50_000,
) -> float:
    """Exposure-weighted priority score in [0, 1]."""
    pop_norm = min(pop_exposed / max_pop, 1.0) if max_pop > 0 else 0.0
    actionability = _ACTIONABILITY.get(source_category, 0.5)
    score = share * pop_norm * actionability * confidence
    return round(min(score, 1.0), 4)


def _compute_rubric(
    share: float,
    pop_exposed: int,
    source_category: str,
    confidence: float,
    num_citations: int,
) -> dict:
    """CPCB/GRAP rubric proxy (total 10 points; ≥8 = 'would-act')."""
    attribution_match = 2 if share > 0.3 else (1 if share > 0.1 else 0)
    actionability_score = 2 if _ACTIONABILITY.get(source_category, 0) > 0.7 else (
        1 if _ACTIONABILITY.get(source_category, 0) > 0.4 else 0
    )
    exposure_score = 2 if pop_exposed > 10_000 else (1 if pop_exposed > 3_000 else 0)
    regulatory_score = min(num_citations, 2)
    confidence_score = 1 if confidence > 0.7 else 0
    total = attribution_match + actionability_score + exposure_score + regulatory_score + confidence_score
    return {
        "attribution_match": attribution_match,
        "actionability": actionability_score,
        "exposure": exposure_score,
        "regulatory_basis": regulatory_score,
        "confidence": confidence_score,
        "total": total,
        "would_act": total >= 8,
    }


# ---------------------------------------------------------------------------
# Dossier generation
# ---------------------------------------------------------------------------

def _generate_rationale(
    source: dict,
    share: float,
    pop_exposed: int,
    source_category: str,
    citations: list[dict],
) -> str:
    """Generate a human-readable enforcement rationale string."""
    pct = round(share * 100, 1)
    source_name = source.get("name", "Unknown source")
    source_type = source.get("type", source_category)

    rationale_parts = [
        f"{source_name} ({source_type}) contributes approximately {pct}% of PM2.5 in this cell,",
        f"exposing an estimated {pop_exposed:,} residents.",
    ]

    if source_type == "construction":
        rationale_parts.append(
            "Site inspection required: verify dust suppression norms compliance "
            "(anti-smog gun, water sprinkling, green net coverage)."
        )
    elif source_type == "industry":
        rationale_parts.append(
            "Industrial inspection required: verify stack emission norms, "
            "Consent-to-Operate (CTO) compliance, and OCEMS data."
        )
    elif source_type == "waste_burn":
        rationale_parts.append(
            "Immediate cessation of open burning required; "
            "issue on-the-spot fine under GRAP/SWM Rules 2016."
        )
    elif source_type == "diesel_corridor":
        rationale_parts.append(
            "Enforce PUC certificate checks; restrict pre-BS-IV vehicles during peak hours."
        )

    if citations:
        cited_rules = "; ".join(c.get("rule", "") for c in citations[:2])
        rationale_parts.append(f"Regulatory basis: {cited_rules}.")

    return " ".join(rationale_parts)


# ---------------------------------------------------------------------------
# Main enforcement agent function
# ---------------------------------------------------------------------------

def run_enforcement(
    city_id: str,
    attribution_data: Optional[list[dict]] = None,
    emission_sources: Optional[list[dict]] = None,
    write_to_db: bool = False,
) -> list[EnforcementRec]:
    """Run the enforcement scoring + RAG citation pipeline.

    Args:
        city_id: City to process.
        attribution_data: Pre-loaded attribution rows (or None → load from DB/fixtures).
        emission_sources: Pre-loaded emission source registry (or None → load from DB/fixtures).
        write_to_db: If True and DEMO_MODE=False, upsert recs to Supabase.

    Returns:
        List of EnforcementRec sorted by descending priority_score.
    """
    from rag.retrieve import retrieve_for_enforcement

    # Load data
    if attribution_data is None:
        if DEMO_MODE:
            attribution_data = _load_demo_attribution(city_id)
        else:
            from core.supa import client
            db = client()
            rows = (
                db.table("attribution")
                .select("h3_cell,source_category,share,confidence,evidence,ts_window")
                .eq("city_id", city_id)
                .order("share", desc=True)
                .limit(200)
                .execute()
                .data
            )
            attribution_data = rows

    if emission_sources is None:
        if DEMO_MODE:
            emission_sources = _load_demo_emission_sources(city_id)
        else:
            from core.supa import client
            db = client()
            emission_sources = (
                db.table("emission_sources")
                .select("id,city_id,name,type,source_origin,detection_confidence,attributes")
                .eq("city_id", city_id)
                .execute()
                .data
            )
            if not emission_sources:
                emission_sources = _load_demo_emission_sources(city_id)

    # Build a cell→attribution lookup (dominant source per cell)
    cell_dominant: dict[str, dict] = {}
    for row in attribution_data:
        h3 = row.get("h3_cell", "")
        share = row.get("share", 0.0)
        existing = cell_dominant.get(h3)
        if existing is None or share > existing.get("share", 0):
            cell_dominant[h3] = {**row, "city_id": city_id}

    # Match sources to cells
    recs: list[EnforcementRec] = []
    source_types_seen: set[str] = set()

    for source in emission_sources:
        source_type = source.get("type", "other")
        attrs = source.get("attributes") or {}
        pop_exposed = source.get("pop_exposed_estimate") or attrs.get("pop_exposed_estimate") or 5000

        # Map source type to attribution category
        cat_map = {
            "construction": "construction_dust",
            "industry": "industrial",
            "waste_burn": "biomass_burning",
            "diesel_corridor": "traffic",
        }
        source_category = cat_map.get(source_type, "other")

        # Find the best matching attribution row for this source's category
        best_attr = None
        best_share = 0.0
        for row in attribution_data:
            if row.get("source_category") == source_category and row.get("share", 0) > best_share:
                best_attr = row
                best_share = row["share"]

        if best_attr is None:
            # Fall back to first attribution row
            best_attr = attribution_data[0] if attribution_data else {}
            best_share = best_attr.get("share", 0.1)

        h3_cell = best_attr.get("h3_cell", "")
        confidence = best_attr.get("confidence", 0.7)
        evidence = best_attr.get("evidence", {})

        # RAG citations
        citations_obj = retrieve_for_enforcement(source_category, city_id, top_k=3)
        citations = [c.as_citation() for c in citations_obj]

        # Priority + rubric
        priority = _compute_priority(best_share, pop_exposed, source_category, confidence)
        rubric = _compute_rubric(best_share, pop_exposed, source_category, confidence, len(citations))

        rationale = _generate_rationale(source, best_share, pop_exposed, source_category, citations)

        rec = EnforcementRec(
            city_id=city_id,
            h3_cell=h3_cell,
            source_id=source.get("id", 0),
            priority_score=priority,
            contribution=best_share,
            pop_exposed=pop_exposed,
            rationale=rationale,
            evidence={**evidence, "source_name": source.get("name", ""), "source_type": source_type},
            rag_citations=citations,
            rubric_score=rubric,
            ts=datetime.now(timezone.utc).isoformat(),
        )
        recs.append(rec)

    # Sort by priority descending
    recs.sort(key=lambda r: r.priority_score, reverse=True)

    if write_to_db and not DEMO_MODE:
        from core.supa import client
        db = client()
        rows = [r.to_dict() for r in recs]
        db.table("enforcement_recs").insert(rows).execute()
        print(f"[enforcement] Wrote {len(rows)} recommendations to Supabase.")

    return recs


def build_dossier(rec_id: int, city_id: str = "delhi") -> dict:
    """Generate a full evidence dossier for a single enforcement recommendation.

    In DEMO_MODE, returns a canned dossier from fixtures or generates one inline.
    In live mode, queries enforcement_recs + RAG for a full cited packet.
    """
    from rag.retrieve import retrieve_for_enforcement

    if DEMO_MODE:
        # Use fixture enforcement data to build a rich dossier
        enforcement_data = json.loads((FIXTURES / "enforcement.json").read_text()) if (FIXTURES / "enforcement.json").exists() else []
        rec = next((r for r in enforcement_data if r.get("id") == rec_id), None)
        if rec is None and enforcement_data:
            rec = enforcement_data[0]
            rec["id"] = rec_id

        if rec is None:
            rec = {
                "id": rec_id, "city_id": city_id,
                "rationale": "Construction site driving elevated PM2.5.",
                "contribution": 0.41, "pop_exposed": 18400,
            }

        # Enhance citations via RAG
        cat = "construction_dust"
        chunks = retrieve_for_enforcement(cat, city_id, top_k=5)
        full_citations = [c.as_citation() for c in chunks]

        return {
            "rec_id": rec_id,
            "city_id": city_id,
            "rationale": rec.get("rationale", ""),
            "contribution_pct": round(rec.get("contribution", 0) * 100, 1),
            "pop_exposed": rec.get("pop_exposed", 0),
            "rubric_score": rec.get("rubric_score", {}),
            "status": rec.get("status", "proposed"),
            "citations": full_citations,
            "satellite_patch": None,  # Sejal E6 fills this in Stage 2
            "suggested_notice_text": _build_notice_text(rec, full_citations),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # Live mode — query DB
    from core.supa import client
    db = client()
    rows = db.table("enforcement_recs").select("*").eq("id", rec_id).limit(1).execute().data
    if not rows:
        return {"rec_id": rec_id, "error": "not_found"}
    rec = rows[0]
    source_category = "construction_dust"  # TODO: derive from source registry join
    chunks = retrieve_for_enforcement(source_category, city_id, top_k=5)
    full_citations = [c.as_citation() for c in chunks]
    return {
        "rec_id": rec_id,
        "city_id": rec["city_id"],
        "rationale": rec["rationale"],
        "contribution_pct": round((rec.get("contribution") or 0) * 100, 1),
        "pop_exposed": rec.get("pop_exposed", 0),
        "rubric_score": rec.get("rubric_score", {}),
        "status": rec.get("status", "proposed"),
        "citations": full_citations,
        "satellite_patch": None,
        "suggested_notice_text": _build_notice_text(rec, full_citations),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _build_notice_text(rec: dict, citations: list[dict]) -> str:
    """Generate a draft enforcement notice text (for the UI 'Generate Notice' button)."""
    pct = round((rec.get("contribution", 0) * 100), 1)
    pop = rec.get("pop_exposed", 0)
    rationale = rec.get("rationale", "Pollution violation detected.")
    cited_rules = "; ".join(c.get("rule", "") for c in citations[:3])
    return (
        f"ENFORCEMENT NOTICE\n"
        f"Issued by: VayuNetra AI Enforcement System\n"
        f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n"
        f"SUBJECT: Non-compliance with Air Pollution Control Norms\n\n"
        f"Based on analysis of CAAQMS ground sensor data, satellite imagery, and "
        f"emission source registry, the following violation has been identified:\n\n"
        f"{rationale}\n\n"
        f"IMPACT: Estimated {pop:,} persons exposed; "
        f"source contributes {pct}% of local PM2.5 concentration.\n\n"
        f"APPLICABLE REGULATIONS:\n{cited_rules}\n\n"
        f"REQUIRED ACTION: Immediate inspection and compliance within 24 hours. "
        f"Non-compliance will result in penalties and/or site sealing as per applicable law.\n\n"
        f"[Generated by VayuNetra AI — for officer review before issuance]"
    )


if __name__ == "__main__":
    print("[enforcement] Running demo enforcement scoring for Delhi...")
    recs = run_enforcement("delhi")
    for r in recs:
        d = r.to_dict()
        print(f"\n  Priority {d['priority_score']:.3f} | {d['rationale'][:80]}...")
        print(f"  Rubric: {d['rubric_score']}")
        print(f"  Citations: {[c['rule'] for c in d['rag_citations']]}")
