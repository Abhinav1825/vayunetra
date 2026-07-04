"""Unit tests for the CPCB/data.gov.in connector transform (no network)."""
from connectors.cpcb import _ts_utc, rows_from_records


def test_handles_both_schema_variants():
    recs = [
        {"pollutant_id": "PM2.5", "avg_value": "180", "latitude": "28.6", "longitude": "77.2",
         "last_update": "01-07-2024 18:00:00", "station": "A"},
        {"pollutant_id": "NO2", "pollutant_avg": "45", "latitude": "28.6", "longitude": "77.2",
         "last_update": "2024-07-01 18:00:00", "station": "A"},
    ]
    rows = rows_from_records("delhi", recs)
    assert {r["variable"] for r in rows} == {"pm25", "no2"}
    assert all(r["source"] == "caaqms" and r["city_id"] == "delhi" for r in rows)
    assert all(r["h3_cell"].startswith("88") for r in rows)


def test_skips_na_and_unknown_pollutant():
    recs = [
        {"pollutant_id": "PM2.5", "avg_value": "NA", "latitude": "28.6", "longitude": "77.2",
         "last_update": "01-07-2024 18:00:00"},
        {"pollutant_id": "NH3", "avg_value": "10", "latitude": "28.6", "longitude": "77.2",
         "last_update": "01-07-2024 18:00:00"},
    ]
    assert rows_from_records("delhi", recs) == []   # NA value skipped, NH3 not in our set


def test_ist_to_utc():
    # 18:00 IST -> 12:30 UTC
    assert _ts_utc("01-07-2024 18:00:00") == "2024-07-01T12:30:00+00:00"
    assert _ts_utc("garbage") is None
