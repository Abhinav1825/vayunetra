"""GRAP stage mapping + dust×traffic co-occurrence screen."""
from core.grap import dust_traffic_cells, forecast_grap, grap_stage_from_aqi


def test_stage_boundaries():
    assert grap_stage_from_aqi(200) is None          # Moderate — below GRAP
    assert grap_stage_from_aqi(201)["stage"] == 1
    assert grap_stage_from_aqi(300)["stage"] == 1
    assert grap_stage_from_aqi(301)["stage"] == 2
    assert grap_stage_from_aqi(401)["stage"] == 3
    assert grap_stage_from_aqi(450)["stage"] == 3
    assert grap_stage_from_aqi(451)["stage"] == 4
    assert grap_stage_from_aqi(None) is None


def test_forecast_grap_is_proactive_and_cited_by_band():
    g = forecast_grap(96.0)  # CPCB sub-index: 91-120 ug/m3 -> AQI 201-300 -> Stage I
    assert g["stage"] == 1
    assert g["trigger_pm25"] == 96.0
    assert 201 <= g["trigger_aqi"] <= 300
    assert "forecast" in g["trigger"]
    assert forecast_grap(40.0) is None               # Satisfactory air -> no stage
    assert forecast_grap(None) is None


def test_dust_traffic_screen_filters_and_sorts():
    cells = [
        {"h3_cell": "a", "shares": {"construction_dust": 0.30, "traffic": 0.28}},
        {"h3_cell": "b", "shares": {"construction_dust": 0.50, "traffic": 0.26}},
        {"h3_cell": "c", "shares": {"construction_dust": 0.60, "traffic": 0.10}},  # traffic minor
        {"h3_cell": "d", "shares": {}},
    ]
    hits = dust_traffic_cells(cells)
    assert [h["h3_cell"] for h in hits] == ["b", "a"]  # worst combined first
    assert hits[0]["combined"] == 0.76


def test_dust_traffic_handles_missing_shares():
    assert dust_traffic_cells([]) == []
    assert dust_traffic_cells([{"h3_cell": "x"}]) == []
