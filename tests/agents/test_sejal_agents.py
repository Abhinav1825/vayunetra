from agents.advisory import build_advisories, risk_tier, vulnerability_adjusted_tier
from agents.multicity import build_comparison


def test_advisory_risk_and_vulnerability_adjustment():
    assert risk_tier(95) == "poor"
    assert vulnerability_adjusted_tier("poor", 0.8) == "very_poor"


def test_build_advisories_generates_languages_and_channels():
    rows = build_advisories(
        "delhi",
        "Delhi",
        [{"horizon_h": 24, "value": 130}],
        [{"ward_id": "ward-12", "vulnerability_index": 0.82, "outdoor_worker_share": 0.31}],
        ["en", "hi"],
        issued_at="2026-06-27T09:00:00Z",
    )
    assert len(rows) == 8  # 2 languages x 4 channels
    assert {r["language"] for r in rows} == {"en", "hi"}
    assert {r["channel"] for r in rows} == {"pwa", "telegram", "ivr", "display"}


def test_multicity_comparison_returns_playbooks():
    out = build_comparison(
        [{"city_id": "delhi", "name": "Delhi"}, {"city_id": "mumbai", "name": "Mumbai"}],
        [
            {"city_id": "delhi", "pm25": 100, "dominant_source": "construction_dust"},
            {"city_id": "mumbai", "pm25": 80, "dominant_source": "traffic"},
        ],
        [
            {"city_id": "delhi", "horizon_h": 24, "value": 130},
            {"city_id": "mumbai", "horizon_h": 24, "value": 90},
        ],
    )
    assert out["summary"]["cities_compared"] == 2
    assert out["cities"][0]["playbook"]
