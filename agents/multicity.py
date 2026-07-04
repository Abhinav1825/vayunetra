"""Agent 5 - Multi-City Comparative Intelligence (Sejal)."""
from __future__ import annotations

from collections import Counter


def average(rows: list[dict], key: str) -> float:
    vals = [float(r[key]) for r in rows if r.get(key) is not None]
    return round(sum(vals) / len(vals), 2) if vals else 0.0


def dominant_source(rows: list[dict]) -> str:
    if not rows:
        return "unknown"
    counts = Counter(r.get("dominant_source", "unknown") for r in rows)
    return counts.most_common(1)[0][0]


def trend_label(forecast_pm25: float, current_pm25: float) -> str:
    delta = forecast_pm25 - current_pm25
    if delta >= 15:
        return "deteriorating"
    if delta <= -15:
        return "improving"
    return "stable"


def playbook_for(source: str, trend: str) -> list[str]:
    if source == "construction_dust":
        return ["pre-wet exposed soil", "inspect large construction sites", "route debris trucks away from schools"]
    if source == "traffic":
        return ["stagger freight windows", "increase bus priority on high-NO2 corridors", "deploy anti-idling checks"]
    if source == "industrial":
        return ["verify consent-to-operate limits", "inspect stack controls", "schedule night-time SO2 spot checks"]
    if trend == "deteriorating":
        return ["pre-position field team", "push citizen advisory", "refresh source attribution in 1 hour"]
    return ["maintain monitoring", "compare against similar H3 signatures", "keep advisory ready"]


def build_comparison(cities: list[dict], aqi_rows: list[dict], forecast_rows: list[dict]) -> dict:
    cards = []
    for city in cities:
        cid = city["city_id"]
        city_aqi = [r for r in aqi_rows if r.get("city_id") == cid]
        city_fc = [r for r in forecast_rows if r.get("city_id") == cid and int(r.get("horizon_h", 24)) == 24]
        current_pm25 = average(city_aqi, "pm25")
        forecast_pm25 = average(city_fc, "value") or current_pm25
        source = dominant_source(city_aqi)
        trend = trend_label(forecast_pm25, current_pm25)
        cards.append({
            "city_id": cid,
            "name": city["name"],
            "current_pm25": current_pm25,
            "forecast_24h_pm25": forecast_pm25,
            "trend": trend,
            "dominant_source": source,
            "signature_match": "construction-winter" if source == "construction_dust" else f"{source}-signature",
            "playbook": playbook_for(source, trend),
        })
    return {
        "summary": {
            "cities_compared": len(cards),
            "highest_risk_city": max(cards, key=lambda r: r["forecast_24h_pm25"])["city_id"] if cards else None,
            "shared_pattern": "traffic + construction dominate the Stage-1 demo snapshot",
        },
        "cities": cards,
    }
