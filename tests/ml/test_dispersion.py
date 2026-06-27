"""Unit tests for the dispersion engine (Gaussian plume + advection)."""
import numpy as np

from ml.dispersion import (
    decay,
    gaussian_plume_concentration as plume,
    pasquill_stability,
    sigma_y,
    sigma_z,
    upwind_origin,
)


# --- Gaussian plume -------------------------------------------------------
def test_upwind_is_zero():
    assert float(plume(Q=100, u=3, x=-50)) == 0.0
    assert float(plume(Q=100, u=3, x=0)) == 0.0


def test_concentration_decreases_downwind():
    near = float(plume(Q=100, u=3, x=200))
    far = float(plume(Q=100, u=3, x=2000))
    assert near > far > 0


def test_crosswind_symmetric_and_peaks_on_centerline():
    centre = float(plume(Q=100, u=3, x=500, y=0))
    off = float(plume(Q=100, u=3, x=500, y=200))
    left = float(plume(Q=100, u=3, x=500, y=-200))
    assert centre > off
    assert abs(off - left) < 1e-12  # symmetry in y


def test_higher_wind_dilutes():
    slow = float(plume(Q=100, u=1, x=500))
    fast = float(plume(Q=100, u=8, x=500))
    assert slow > fast


def test_sigmas_grow_with_distance():
    assert sigma_y(2000, "D") > sigma_y(200, "D") > 0
    assert sigma_z(2000, "D") > sigma_z(200, "D") > 0


def test_vectorised_input():
    out = plume(Q=100, u=3, x=np.array([-10, 200, 2000]))
    assert out.shape == (3,)
    assert out[0] == 0.0 and out[1] > out[2] > 0


def test_stability_classes():
    assert pasquill_stability(1.0, is_day=True) == "A-B"
    assert pasquill_stability(6.0, is_day=True) == "D"
    assert pasquill_stability(1.0, is_day=False) == "E-F"


# --- Advection ------------------------------------------------------------
def test_zero_wind_origin_is_receptor():
    lat, lng = upwind_origin(28.61, 77.21, u=0, v=0, hours=6)
    assert abs(lat - 28.61) < 1e-12 and abs(lng - 77.21) < 1e-12


def test_wind_from_west_origin_is_west():
    # u > 0 = wind blowing east, so pollution came from the WEST (smaller lng)
    _, lng = upwind_origin(28.61, 77.21, u=10, v=0, hours=1)
    assert lng < 77.21
    # 10 m/s for 1h = 36 km ~ 0.37 deg lng at this latitude
    assert 77.21 - lng > 0.3


def test_decay_halves_at_half_life():
    assert decay(100.0, half_life_h=6, hours=6) == 50.0
    assert decay(100.0, half_life_h=6, hours=0) == 100.0
