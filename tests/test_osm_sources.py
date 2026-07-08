"""Unit tests for the OSM emission-source registry transform (pure function)."""
from connectors.osm_sources import rows_from_elements


def _el(id_, tags, lat=28.61, lon=77.21, type_="way", center=True):
    el = {"type": type_, "id": id_, "tags": tags}
    if center:
        el["center"] = {"lat": lat, "lon": lon}
    else:
        el["lat"], el["lon"] = lat, lon
    return el


def test_maps_tags_to_registry_types():
    elements = [
        _el(1, {"landuse": "construction", "name": "Metro Depot Site"}),
        _el(2, {"landuse": "industrial", "name": "Okhla Industrial Estate"}),
        _el(3, {"landuse": "landfill", "name": "Ghazipur Landfill"}),
        _el(4, {"power": "plant", "name": "Badarpur Thermal"}),
    ]
    rows = rows_from_elements("delhi", elements)
    types = {r["name"]: r["type"] for r in rows}
    assert types["Metro Depot Site"] == "construction"
    assert types["Okhla Industrial Estate"] == "industry"
    assert types["Ghazipur Landfill"] == "waste_burn"
    assert types["Badarpur Thermal"] == "industry"  # power plants score as industry


def test_row_shape_matches_registry_schema():
    rows = rows_from_elements("delhi", [_el(9, {"landuse": "construction", "name": "Site X"})])
    r = rows[0]
    assert r["city_id"] == "delhi"
    assert r["source_origin"] == "osm"
    assert r["registry_ref"] == "osm:way/9"
    assert r["geom"]["type"] == "Point"
    assert r["attributes"]["h3_cell"].startswith("88")  # res-8 H3
    assert r["attributes"]["pop_exposed_estimate"] > 0


def test_skips_unnamed_except_landfill_and_dedupes():
    elements = [
        _el(1, {"landuse": "construction"}),                         # unnamed -> skipped
        _el(2, {"landuse": "landfill"}),                             # unnamed landfill -> kept w/ fallback name
        _el(3, {"landuse": "industrial", "name": "Peenya"}),
        _el(4, {"landuse": "industrial", "name": "Peenya"}),         # duplicate -> skipped
        _el(5, {"amenity": "school", "name": "Not a source"}),       # unrelated tag -> skipped
    ]
    rows = rows_from_elements("bengaluru", elements)
    names = [r["name"] for r in rows]
    assert len([n for n in names if n == "Peenya"]) == 1
    assert any(n.startswith("Landfill site (OSM") for n in names)
    assert all("Not a source" != n for n in names)


def test_caps_per_type():
    elements = [_el(i, {"landuse": "construction", "name": f"Site {i}"}) for i in range(20)]
    rows = rows_from_elements("mumbai", elements)
    assert len(rows) == 8  # CAP_PER_TYPE["construction"]


def test_water_infrastructure_excluded():
    elements = [
        _el(1, {"landuse": "industrial", "name": "Vrishabhavathi Valley 150MLD Sewage Treatment Plant"}),
        _el(2, {"landuse": "industrial", "name": "Okhla Wastewater Facility"}),
        _el(3, {"landuse": "industrial", "name": "Trombay Thermal Power Station"}),
    ]
    names = [r["name"] for r in rows_from_elements("delhi", elements)]
    assert names == ["Trombay Thermal Power Station"]  # water infra never blames air
