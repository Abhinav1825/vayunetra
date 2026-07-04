"""Unit tests for the Open-Meteo connector transforms (no network)."""
from connectors.openmeteo import build_measurements, wind_uv


def test_wind_uv_from_north():
    # wind FROM the north blows southward: v negative, u ~ 0
    u, v = wind_uv(10.0, 0.0)
    assert abs(u) < 1e-9
    assert v == -10.0


def test_wind_uv_from_east():
    # wind FROM the east blows westward: u negative, v ~ 0
    u, v = wind_uv(10.0, 90.0)
    assert round(u, 6) == -10.0
    assert abs(v) < 1e-9


def _hourly():
    return {
        "time": ["2026-06-27T00:00", "2026-06-27T01:00"],
        "temperature_2m": [30.0, 29.0],
        "relative_humidity_2m": [40, 45],
        "precipitation": [0.0, 0.1],
        "boundary_layer_height": [800, 600],
        "wind_speed_10m": [3.0, 2.0],
        "wind_direction_10m": [0.0, 90.0],
    }


def test_build_measurements_shape():
    rows = build_measurements("delhi", "abc", _hourly())
    # 2 hours x (4 scalar + 2 wind components) = 12 rows
    assert len(rows) == 12
    assert {r["variable"] for r in rows} == {"temp", "rh", "precip", "blh", "wind_u", "wind_v"}
    assert all(r["source"] == "openmeteo" and r["city_id"] == "delhi" for r in rows)
    assert rows[0]["ts"].endswith("+00:00")  # ISO-8601 UTC


def test_build_measurements_skips_nulls():
    hourly = {
        "time": ["2026-06-27T00:00"],
        "temperature_2m": [None],
        "relative_humidity_2m": [40],
        "precipitation": [0.0],
        "boundary_layer_height": [None],
        "wind_speed_10m": [None],
        "wind_direction_10m": [None],
    }
    rows = build_measurements("delhi", "abc", hourly)
    assert {r["variable"] for r in rows} == {"rh", "precip"}
