"""Unit tests for H3 spatial helpers incl. ward<->H3 mapping."""
from core.spatial.h3_utils import (
    cell_to_ward,
    cells_for_geojson,
    latlng_to_cell,
    ward_to_cells,
)

# a small square around central Delhi
_POLY = {
    "type": "Polygon",
    "coordinates": [[[77.18, 28.58], [77.24, 28.58], [77.24, 28.64], [77.18, 28.64], [77.18, 28.58]]],
}


def test_latlng_to_cell():
    c = latlng_to_cell(28.61, 77.21, 8)
    assert c.startswith("88") and len(c) == 15


def test_cells_for_geojson_covers_center():
    cells = cells_for_geojson(_POLY, 8)
    assert len(cells) > 0
    assert all(c.startswith("88") for c in cells)
    assert latlng_to_cell(28.61, 77.21, 8) in cells   # the polygon's centre cell is covered


def test_ward_to_cells_and_reverse():
    fc = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": {"ward_id": "W1"}, "geometry": _POLY}],
    }
    w2c = ward_to_cells(fc, 8)
    assert "W1" in w2c and len(w2c["W1"]) > 0
    c2w = cell_to_ward(w2c)
    assert c2w[w2c["W1"][0]] == "W1"
