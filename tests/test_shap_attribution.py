"""Unit tests for the hybrid GBM+SHAP apportionment (Attribution v2)."""
import numpy as np
import pandas as pd
import pytest

from ml.attribution.shap_attribution import (
    BLEND_WEIGHT,
    CellApportionment,
    _blend,
    _calibrated_confidence,
    apportion_cells,
    build_wide,
)
from ml.attribution.signatures import CATEGORIES


def _synthetic_long(hours: int = 900, no2_driven: bool = True) -> pd.DataFrame:
    """Long measurements where PM2.5 is driven by NO2 (traffic) — the model
    should discover that and put the blame there."""
    rng = np.random.default_rng(7)
    ts = pd.date_range("2026-01-01", periods=hours, freq="h", tz="UTC")
    rows = []
    for cell in ("8860145a01fffff", "8860145a03fffff"):
        no2 = rng.uniform(10, 120, hours)
        so2 = rng.uniform(2, 8, hours)          # weak, flat industrial signal
        pm25 = (2.0 * no2 if no2_driven else rng.uniform(30, 60, hours)) + rng.normal(0, 5, hours)
        pm10 = pm25 * 1.4
        for i, t in enumerate(ts):
            iso = t.isoformat()
            for var, val in (("pm25", pm25[i]), ("pm10", pm10[i]), ("no2", no2[i]),
                             ("so2", so2[i]), ("co", no2[i] / 50)):
                rows.append({"city_id": "testcity", "h3_cell": cell, "ts": iso,
                             "variable": var, "value": float(max(val, 0.1))})
    return pd.DataFrame(rows)


def test_blend_normalises_and_weights():
    shap_s = {c: 0.0 for c in CATEGORIES} | {"traffic": 1.0}
    sig_s = {c: 0.0 for c in CATEGORIES} | {"industrial": 1.0}
    blended = _blend(shap_s, sig_s)
    assert abs(sum(blended.values()) - 1.0) < 1e-6
    assert blended["traffic"] == pytest.approx(BLEND_WEIGHT, abs=0.01)
    assert blended["industrial"] == pytest.approx(1 - BLEND_WEIGHT, abs=0.01)


def test_confidence_bounds_and_agreement():
    same = {c: 1 / len(CATEGORIES) for c in CATEGORIES}
    hi = _calibrated_confidence(same, same, r2=0.9, n_cell=72)
    disjoint_a = {c: 0.0 for c in CATEGORIES} | {"traffic": 1.0}
    disjoint_b = {c: 0.0 for c in CATEGORIES} | {"biomass_burning": 1.0}
    lo = _calibrated_confidence(disjoint_a, disjoint_b, r2=0.0, n_cell=5)
    assert 0.30 <= lo < hi <= 0.95


def test_apportion_finds_the_planted_source():
    long_df = _synthetic_long()
    wide = build_wide(long_df)
    sig = {c: {"traffic": 0.3, "industrial": 0.3, "construction_dust": 0.1,
               "biomass_burning": 0.1, "transported": 0.1, "other": 0.1}
           for c in wide["h3_cell"].unique()}
    result, r2 = apportion_cells(wide, sig)
    assert result, "expected at least one apportioned cell"
    for ap in result.values():
        assert isinstance(ap, CellApportionment)
        # PM2.5 was constructed from NO2 -> traffic must dominate
        assert max(ap.shares, key=ap.shares.get) == "traffic"
        assert abs(sum(ap.shares.values()) - 1.0) < 0.01
        assert ap.shap_drivers and ap.shap_drivers[0]["source"] == "traffic"
    assert r2 > 0.5  # the planted relationship is learnable


def test_thin_data_raises_for_fallback():
    long_df = _synthetic_long(hours=30)  # << MIN_SAMPLES
    wide = build_wide(long_df)
    with pytest.raises(ValueError):
        apportion_cells(wide, {})
