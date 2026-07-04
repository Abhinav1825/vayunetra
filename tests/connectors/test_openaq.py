"""Unit tests for the OpenAQ connector transform (no network)."""
from connectors.openaq import rows_from_records


def _records():
    return [
        {"lat": 28.61, "lng": 77.21, "variable": "pm25", "value": 180.0, "unit": "ug/m3",
         "ts": "2026-06-27T08:00:00Z", "station_id": "101"},
        {"lat": 28.61, "lng": 77.21, "variable": "no2", "value": 45.0, "unit": "ug/m3",
         "ts": "2026-06-27T08:00:00Z", "station_id": "101"},
    ]


def test_maps_to_canonical_and_h3():
    rows = rows_from_records("delhi", _records())
    assert len(rows) == 2
    r = rows[0]
    assert r["city_id"] == "delhi"
    assert r["source"] == "openaq"
    assert r["variable"] == "pm25"
    assert r["h3_cell"].startswith("88")           # H3 res-8 cell id
    assert r["station_id"] == "101"


def test_skips_unknown_parameter():
    recs = _records() + [{"lat": 28.6, "lng": 77.2, "variable": "bc", "value": 1.0,
                          "unit": "ug/m3", "ts": "2026-06-27T08:00:00Z", "station_id": "1"}]
    rows = rows_from_records("delhi", recs)
    assert {r["variable"] for r in rows} == {"pm25", "no2"}   # 'bc' dropped


def test_skips_null_or_missing_coords():
    recs = [
        {"lat": None, "lng": 77.2, "variable": "pm25", "value": 10, "unit": "ug/m3",
         "ts": "t", "station_id": "1"},
        {"lat": 28.6, "lng": 77.2, "variable": "pm25", "value": None, "unit": "ug/m3",
         "ts": "t", "station_id": "1"},
    ]
    assert rows_from_records("delhi", recs) == []
