from typing import Any
from itertools import combinations
from .counterfactual import simulate_intervention, INTERVENTIONS

# Heuristic costs in inspector-hours
INTERVENTION_COSTS = {
    "construction_halt": 8,
    "traffic_restriction": 20,
    "industrial_shutdown": 12,
    "waste_burn_ban": 5,
    "grap_stage3": 40,
}

def optimize_interventions(
    city_id: str,
    budget_inspector_hours: int,
    horizon_h: int = 24,
    target_cells: list[str] | None = None,
) -> dict[str, Any]:
    """
    E5 Prescriptive Optimiser: priority-knapsack search over E3 simulations.
    Finds top-3 intervention combinations that maximize people_protected under budget.
    """
    candidate_types = list(INTERVENTIONS.keys())
    
    # 1. Run simulation for each individual intervention to get its base value
    # Since these are approximations, we can combine them linearly for the search.
    # A true counterfactual would simulate combinations natively, but for performance
    # and linear approximation we estimate combined impact.
    individual_results = {}
    for itype in candidate_types:
        res = simulate_intervention(
            city_id=city_id,
            intervention_type=itype,
            target_cells=target_cells,
            horizon_h=horizon_h
        )
        individual_results[itype] = {
            "people_protected": res["people_protected"],
            "delta_aqi_by_cell": res["delta_aqi_by_cell"],
            "cost": INTERVENTION_COSTS.get(itype, 10),
            "confidence": res["confidence"]
        }

    # 2. Generate feasible packages (combinations of 1 to 3 interventions)
    valid_packages = []
    
    for r in range(1, min(4, len(candidate_types) + 1)):
        for combo in combinations(candidate_types, r):
            total_cost = sum(individual_results[itype]["cost"] for itype in combo)
            if total_cost <= budget_inspector_hours:
                # Estimate combined people protected (subadditive heuristic)
                # In a real rigorous setup, you'd run `simulate_intervention` with merged reductions.
                # Here we use a heuristic subadditive sum for speed.
                total_protected = sum(individual_results[itype]["people_protected"] for itype in combo)
                # Apply a slight penalty for overlapping effects
                total_protected = int(total_protected * (0.9 ** (len(combo) - 1)))
                
                valid_packages.append({
                    "interventions": list(combo),
                    "total_cost": total_cost,
                    "people_protected": total_protected,
                    "score": total_protected / max(1, total_cost) # value density
                })
                
    # 3. Sort packages by people_protected (primary) and cost (secondary)
    valid_packages.sort(key=lambda x: (x["people_protected"], -x["total_cost"]), reverse=True)
    
    # Top 3 packages
    top_3 = valid_packages[:3]
    
    return {
        "budget": budget_inspector_hours,
        "packages": top_3
    }
