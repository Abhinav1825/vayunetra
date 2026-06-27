"""Unit tests for seasonal / event calendar features."""
from ml.forecast.seasonal import calendar_features


def test_stubble_season():
    assert calendar_features("2026-10-15T00:00:00+00:00")["is_stubble_season"] == 1
    assert calendar_features("2026-06-15T00:00:00+00:00")["is_stubble_season"] == 0


def test_winter_inversion():
    assert calendar_features("2026-12-15T00:00:00+00:00")["is_winter_inversion"] == 1
    assert calendar_features("2026-07-15T00:00:00+00:00")["is_winter_inversion"] == 0


def test_diwali_window():
    # Diwali 2026 = Nov 8 -> within window; Nov 20 is far outside
    assert calendar_features("2026-11-08T00:00:00+00:00")["is_diwali_window"] == 1
    assert calendar_features("2026-11-20T00:00:00+00:00")["is_diwali_window"] == 0


def test_summer_is_all_clear():
    assert calendar_features("2026-06-15T00:00:00+00:00") == {
        "is_stubble_season": 0, "is_winter_inversion": 0, "is_diwali_window": 0,
    }
