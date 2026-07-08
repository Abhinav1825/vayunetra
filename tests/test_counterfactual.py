"""Unit tests for the E3 counterfactual simulator (pure core)."""
import pytest

from ml.simulator.counterfactual import (
    INTERVENTIONS,
    CellState,
    apply_reductions,
    pm25_to_aqi,
)


def _cell(h3: str, pm25: float, dust: float = 0.6, transported: float = 0.2) -> CellState:
    other = max(0.0, 1.0 - dust - transported)
    return CellState(
        h3_cell=h3,
        pm25_forecast=pm25,
        shares={"construction_dust": dust, "transported": transported, "other": other},
        confidence=0.7,
    )


def test_pm25_to_aqi_cpcb_bands():
    assert pm25_to_aqi(0) == 0
    assert pm25_to_aqi(30) == 50
    assert pm25_to_aqi(60) == 100
    assert pm25_to_aqi(120) == 300
    assert pm25_to_aqi(999) == 500


def test_construction_halt_reduces_dusty_cell_most():
    dusty = _cell("cellA", 150, dust=0.7, transported=0.1)
    clean = _cell("cellB", 150, dust=0.1, transported=0.1)
    r = apply_reductions([dusty, clean], INTERVENTIONS["construction_halt"])
    assert r["delta_pm25_by_cell"]["cellA"] < r["delta_pm25_by_cell"]["cellB"] < 0
    assert r["delta_aqi_by_cell"]["cellA"] < 0
    assert 0 < r["confidence"] <= 1


def test_dispersion_hop_reduces_transported_component():
    # a cell with ONLY transported share still improves when the city acts
    downwind = CellState("down", 100, {"transported": 1.0}, 0.6)
    source_cell = _cell("src", 100, dust=0.8, transported=0.0)
    r = apply_reductions([downwind, source_cell], {"construction_dust": 0.8})
    assert r["delta_pm25_by_cell"]["down"] < 0  # improved via advection coupling


def test_target_cells_filter_and_people_protected():
    cells = [_cell(f"c{i}", 200, dust=0.8) for i in range(3)]
    r = apply_reductions(cells, {"construction_dust": 1.0}, target_cells=["c0"])
    assert set(r["delta_aqi_by_cell"]) == {"c0"}
    assert r["people_protected"] == 40_000  # one protected cell x heuristic pop


def test_honest_fields():
    r = apply_reductions([_cell("x", 80)], INTERVENTIONS["traffic_restriction"])
    assert r["pm25_tonnes_avoided"] is None  # not faked without an inventory
