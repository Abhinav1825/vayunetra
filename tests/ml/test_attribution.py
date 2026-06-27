"""Unit tests for the chemical-signature attributor."""
from ml.attribution.signatures import CATEGORIES, calibrate_references, signature_shares


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


def test_calibrate_references_p90_and_fallback():
    refs = calibrate_references({"no2": list(range(100))})   # p90 of 0..99 ≈ 89
    assert 85 <= refs["no2"] <= 92
    # sparse data (<10 points) falls back to the fixed default
    assert calibrate_references({"no2": [1, 2, 3]})["no2"] == 80.0


def test_satellite_no2_corroborates_traffic():
    # adding the satellite NO2 column raises the traffic share (fusion signal)
    base = signature_shares({"no2": 10, "co": 0.1, "pm25": 50, "pm10": 60})[0]["traffic"]
    with_sat = signature_shares({"no2": 10, "co": 0.1, "pm25": 50, "pm10": 60, "no2_sat": 2e-4})[0]["traffic"]
    assert with_sat > base


def test_calibrated_refs_amplify_local_marker():
    # a modest NO2 reading becomes a strong traffic marker once refs reflect current conditions
    vals = {"no2": 20, "co": 0.1, "so2": 1, "pm25": 40, "pm10": 50}
    low_ref = {"no2": 20, "co": 2, "so2": 30, "pm25": 150, "pm10": 300, "fire": 50}
    shares, _, _ = signature_shares(vals, low_ref)
    assert max(shares, key=shares.get) == "traffic"
    assert shares["traffic"] > shares["transported"]
