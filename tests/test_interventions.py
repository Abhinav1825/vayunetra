"""Intervention effect measurement — pure-function + endpoint tests."""
import os

os.environ["DEMO_MODE"] = "true"

from datetime import datetime, timezone

from fastapi.testclient import TestClient

import api.main as m
from core.interventions import effect_summary, mean

client = TestClient(m.app)
NOW = datetime(2026, 7, 19, 12, 0, tzinfo=timezone.utc)


def test_mean_ignores_nones_and_empty():
    assert mean([10, None, 20]) == 15.0
    assert mean([]) is None
    assert mean([None]) is None


def test_effect_subtracts_city_drift():
    s = effect_summary(
        baseline_pm25=80.0, cell_after=60.0,      # cell fell 20
        city_before=70.0, city_after=65.0,        # city fell 5 anyway (weather)
        dispatched_at="2026-07-10T12:00:00+00:00", now=NOW,
    )
    assert s["cell_delta"] == -20.0
    assert s["city_drift"] == -5.0
    assert s["effect_pm25"] == -15.0              # improvement beyond the drift
    assert s["status"] == "measured"              # 9 days elapsed


def test_effect_provisional_before_a_week():
    s = effect_summary(80.0, 75.0, 70.0, 70.0, "2026-07-17T12:00:00+00:00", now=NOW)
    assert s["status"] == "provisional"
    assert "needs" in s["note"]


def test_effect_without_data_is_measuring_not_a_verdict():
    s = effect_summary(None, None, None, None, "2026-07-18T12:00:00+00:00", now=NOW)
    assert s["status"] == "measuring"
    assert "effect_pm25" not in s


def test_interventions_endpoint_honest_empty_state():
    body = client.get("/interventions", params={"city": "delhi"}).json()
    assert body["success"] is True
    assert body["data"]["tracked"] == []
    assert "No real-world intervention dispatched yet" in body["data"]["note"]


# --- permits connector (scaffold parser) --------------------------------------

def test_permit_parser_shapes_and_skips_bad_rows(tmp_path):
    from connectors.permits import parse_permits

    p = tmp_path / "delhi.csv"
    p.write_text(
        "permit_id,site_name,lat,lon,valid_from,valid_to,area_sqm,dust_plan\n"
        "DPCC-1,Site A,28.61,77.21,2026-01-01,2027-01-01,9000,true\n"
        ",No Id,28.61,77.21,2026-01-01,2027-01-01,100,false\n"
        "DPCC-2,Bad Coords,999,77.21,2026-01-01,2027-01-01,100,false\n"
    )
    rows = parse_permits(p)
    assert len(rows) == 1
    r = rows[0]
    assert r["source_origin"] == "permit_registry"
    assert r["registry_ref"] == "DPCC-1"
    assert r["geom"]["coordinates"] == [77.21, 28.61]
    assert r["attributes"]["dust_plan"] is True
