from datetime import datetime, timezone

from connectors.mobility import build_mobility_rows, time_multiplier
from connectors.static_layers import build_static_layers


def test_static_layers_have_stage1_contract():
    layer = build_static_layers("delhi")
    assert layer["city_id"] == "delhi"
    assert layer["emission_sources"]
    assert layer["vulnerability"]
    assert layer["roads"]
    assert {"coordinates", "type", "detection_confidence"} <= set(layer["emission_sources"][0])


def test_mobility_builds_canonical_traffic_rows():
    rows = build_mobility_rows("bengaluru", hours=2, start=datetime(2026, 6, 27, tzinfo=timezone.utc))
    assert rows
    assert {r["variable"] for r in rows} == {"traffic"}
    assert {r["source"] for r in rows} == {"osm_gtfs"}
    assert all(r["h3_cell"].startswith("88") for r in rows)


def test_time_multiplier_peaks_on_weekday_evening():
    off_peak = time_multiplier(datetime(2026, 6, 30, 14, tzinfo=timezone.utc))
    peak = time_multiplier(datetime(2026, 6, 30, 18, tzinfo=timezone.utc))
    assert peak > off_peak
