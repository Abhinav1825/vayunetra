"""Enforcement-notice content + PDF tests.

The notice is officer-facing paper: no duplicate citations, no raw data URIs,
a real addressee, an explicit deadline, and a signature block. The PDF must
embed the actual satellite JPEG when one exists.
"""
import base64
import io
import os

os.environ["DEMO_MODE"] = "true"

from agents.enforcement import _build_notice_text  # noqa: E402
from agents.notice_pdf import _jpeg_from_data_uri, notice_pdf_bytes  # noqa: E402

REC = {
    "id": 495,
    "city_id": "mumbai",
    "h3_cell": "88608b55c5fffff",
    "contribution": 0.6644,
    "pop_exposed": 18786,
    "rationale": "Construction dust contributes approximately 66.4% of PM2.5 in this cell.",
}
CITATIONS = [
    {"rule": "GRADED RESPONSE ACTION PLAN (GRAP) — FULL TEXT", "excerpt": "Stage II requires mechanised sweeping and water sprinkling on identified roads. " * 4},
    {"rule": "GRADED RESPONSE ACTION PLAN (GRAP) — FULL TEXT", "excerpt": "dup"},
    {"rule": "GRADED RESPONSE ACTION PLAN (GRAP) — FULL TEXT", "excerpt": "dup"},
]
PATCH = {
    "title": "Sentinel-2 patch - Marathon Millenia",
    "image_ref": "data:image/jpeg;base64,AAAA",
    "metadata": {"detection_confidence": 0.9},
}
SOURCE = {"name": "Marathon Millenia", "type": "construction"}


def _tiny_jpeg() -> str:
    """Minimal valid JPEG (2x2 gray) as a data URI, built by PIL."""
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (40, 30), (120, 130, 140)).save(buf, format="JPEG")
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def test_notice_dedupes_and_prettifies_citations():
    text = _build_notice_text(REC, CITATIONS, PATCH, SOURCE)
    assert text.count("Graded Response Action Plan (GRAP)") == 1
    assert "FULL TEXT" not in text  # registry label leak


def test_notice_never_contains_raw_data_uri():
    text = _build_notice_text(REC, CITATIONS, PATCH, SOURCE)
    assert "base64" not in text
    assert "[[SATELLITE_IMAGE]]" in text  # renderer marker instead


def test_notice_has_addressee_deadline_and_signature():
    text = _build_notice_text(REC, CITATIONS, PATCH, SOURCE)
    assert "The Occupier / Site Manager, Marathon Millenia, Mumbai" in text
    assert "IST" in text and "24 hours from issue" in text
    assert "AUTHORISATION:" in text and "Designation:" in text
    assert "DRAFT - pending officer authorisation" in text


def test_notice_confidence_is_percent_not_fraction():
    text = _build_notice_text(REC, CITATIONS, PATCH, SOURCE)
    assert "90% detection confidence" in text
    assert "confidence: 0.9" not in text


def test_notice_without_source_still_addresses_premises():
    text = _build_notice_text(REC, CITATIONS, None, None)
    assert "The Occupier / Site Manager of the identified premises, Mumbai" in text


def test_jpeg_data_uri_parsing():
    uri = _tiny_jpeg()
    parsed = _jpeg_from_data_uri(uri)
    assert parsed is not None
    raw, w, h, ncomp = parsed
    assert (w, h) == (40, 30) and ncomp == 3
    assert _jpeg_from_data_uri("data:image/jpeg;base64,!!!notb64") is None
    assert _jpeg_from_data_uri(None) is None


def test_pdf_embeds_jpeg_xobject():
    patch = dict(PATCH, image_ref=_tiny_jpeg())
    text = _build_notice_text(REC, CITATIONS, patch, SOURCE)
    pdf = notice_pdf_bytes(text, image_data_uri=patch["image_ref"])
    assert pdf.startswith(b"%PDF")
    assert b"/DCTDecode" in pdf and b"/Im1" in pdf


def test_pdf_renders_without_image_too():
    text = _build_notice_text(REC, CITATIONS, PATCH, SOURCE)
    pdf = notice_pdf_bytes(text, image_data_uri="data:image/jpeg;base64,broken")
    assert pdf.startswith(b"%PDF")
    assert b"/DCTDecode" not in pdf


# --- impact projection + chart ------------------------------------------------

def test_impact_projection_math_and_gates():
    from agents.enforcement import _impact_projection

    fc = [
        {"horizon_h": 24, "value": 80.0},
        {"horizon_h": 48, "value": 60.0},
        {"horizon_h": 72, "value": 50.0},
        {"horizon_h": 24, "value": 999.0},  # older duplicate — first wins
    ]
    p = _impact_projection({"contribution": 0.25}, fc)
    assert p["contribution_pct"] == 25.0
    assert p["horizons"][0] == {"h": 24, "base": 80.0, "with_compliance": 60.0}
    assert len(p["horizons"]) == 3
    # gates: negligible share or no forecasts -> no chart, no fake numbers
    assert _impact_projection({"contribution": 0.01}, fc) is None
    assert _impact_projection({"contribution": 0.25}, []) is None


def test_notice_text_carries_projection_section():
    from agents.enforcement import _impact_projection

    p = _impact_projection(REC, [{"horizon_h": 24, "value": 41.0}, {"horizon_h": 48, "value": 29.0}])
    text = _build_notice_text(REC, CITATIONS, PATCH, SOURCE, p)
    assert "PROJECTED IMPACT OF COMPLIANCE:" in text
    assert "[[IMPACT_CHART]]" in text
    assert "screening estimate, not a guarantee" in text


def test_pdf_draws_impact_chart():
    from agents.enforcement import _impact_projection

    p = _impact_projection(REC, [{"horizon_h": 24, "value": 41.0}, {"horizon_h": 72, "value": 28.0}])
    text = _build_notice_text(REC, CITATIONS, None, SOURCE, p)
    pdf = notice_pdf_bytes(text, impact_chart=p)
    assert pdf.startswith(b"%PDF")
    assert b"with source compliance" in pdf  # legend text present in content stream
