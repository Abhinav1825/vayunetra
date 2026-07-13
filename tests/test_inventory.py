"""Attribution-vs-inventory anchor tests (PS5 evaluation focus)."""
import pytest

from ml.attribution.inventory import (
    CITY_INVENTORY,
    LOCAL_CATEGORIES,
    compare_with_inventory,
)
from ml.simulator.counterfactual import INTERVENTIONS, INTERVENTION_CITATIONS


def test_every_anchor_is_cited_and_plausible():
    for city, anchor in CITY_INVENTORY.items():
        assert anchor.source and anchor.caveat, f"{city} anchor must carry citation + caveat"
        assert 0.9 <= sum(anchor.shares.values()) <= 1.1  # shares ~sum to 1
        assert set(LOCAL_CATEGORIES) <= set(anchor.shares)


def test_comparison_renormalizes_and_scores():
    ours = {"traffic": 0.4, "construction_dust": 0.2, "industrial": 0.2,
            "biomass_burning": 0.05, "transported": 0.1, "other": 0.05}
    r = compare_with_inventory("delhi", attribution_means=ours)
    assert 0 <= r["cosine_similarity"] <= 1
    assert set(r["categories"]) == set(LOCAL_CATEGORIES)
    for v in r["categories"].values():  # both sides renormalized to local sum=1
        assert 0 <= v["attribution"] <= 1 and 0 <= v["inventory"] <= 1
    assert "SAFAR" in r["inventory_source"]


def test_unknown_city_raises():
    with pytest.raises(ValueError):
        compare_with_inventory("atlantis", attribution_means={})


def test_every_intervention_magnitude_is_cited():
    for name in INTERVENTIONS:
        cites = INTERVENTION_CITATIONS.get(name)
        assert cites, f"intervention '{name}' has no literature citation"
        assert all(c.get("source") for c in cites)
