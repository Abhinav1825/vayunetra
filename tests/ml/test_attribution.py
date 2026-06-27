"""Unit tests for the chemical-signature attributor."""
from ml.attribution.signatures import CATEGORIES, signature_shares


def _dominant(values):
    shares, _, _ = signature_shares(values)
    return max(shares, key=shares.get)


def test_shares_sum_to_one_and_cover_all_categories():
    shares, conf, ev = signature_shares({"no2": 50, "co": 1.0, "pm25": 100, "pm10": 150})
    assert set(shares) == set(CATEGORIES)
    assert abs(sum(shares.values()) - 1.0) < 1e-6
    assert 0.30 <= conf <= 0.95
    assert "top_signals" in ev


def test_high_no2_co_is_traffic():
    assert _dominant({"no2": 78, "co": 1.9, "so2": 2, "pm25": 90, "pm10": 110}) == "traffic"


def test_high_so2_is_industrial():
    assert _dominant({"no2": 5, "co": 0.2, "so2": 28, "pm25": 80, "pm10": 90}) == "industrial"


def test_high_coarse_ratio_flags_construction():
    shares, _, _ = signature_shares({"no2": 5, "co": 0.2, "so2": 1, "pm25": 80, "pm10": 280})
    assert shares["construction_dust"] > 0.0  # pm10/pm25 = 3.5 >> 1.8


def test_empty_input_is_safe():
    shares, conf, _ = signature_shares({})
    assert abs(sum(shares.values()) - 1.0) < 1e-6
    # with no markers, the baselines (transported/other) carry the share
    assert shares["transported"] >= shares["traffic"]
