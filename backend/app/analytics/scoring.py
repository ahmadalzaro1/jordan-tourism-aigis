"""
Priority Investment Scoring for Jordan Tourism AI-GIS.

Per RFP ToR Section 3.2.5:
- Score = weighted combination of forecast demand, capacity gap, occupancy pressure
- Accessibility rating (road network + airline routes)
- Rule-based recommended investment type per zone

Scoring Formula (configurable weights):
  Priority Score = (w1 * demand_score) + (w2 * capacity_gap_score) +
                   (w3 * occupancy_pressure_score) + (w4 * growth_score) +
                   (w5 * accessibility_score)
"""

from typing import Optional


# Default weights (must sum to 1.0)
DEFAULT_WEIGHTS = {
    "demand_score": 0.25,
    "capacity_gap_score": 0.30,
    "occupancy_pressure_score": 0.20,
    "growth_score": 0.15,
    "accessibility_score": 0.10,
}


def normalize_score(value: float, min_val: float, max_val: float) -> float:
    """Normalize a value to 0-100 scale."""
    if max_val == min_val:
        return 50.0
    return round(max(0, min(100, ((value - min_val) / (max_val - min_val)) * 100)), 1)


def demand_score(forecast_visitors: int, max_visitors: int = 5000000) -> float:
    """
    Score based on forecasted visitor demand.
    Higher demand = higher score (more investment needed).
    """
    return normalize_score(forecast_visitors, 0, max_visitors)


def capacity_gap_score(
    total_beds: int,
    forecast_visitors: int,
    avg_stay_nights: float = 2.5,
) -> float:
    """
    Score based on capacity gap (demand vs supply).

    Gap = (demand_nights - supply_nights) / demand_nights * 100
    Positive gap = under-capacity = higher score (needs investment)
    """
    if forecast_visitors <= 0:
        return 0

    demand_nights = forecast_visitors * avg_stay_nights
    supply_nights = total_beds * 365 * 0.75  # 75% target occupancy

    gap = (
        ((demand_nights - supply_nights) / demand_nights) * 100
        if demand_nights > 0
        else 0
    )

    # Normalize: -100% (huge surplus) to +200% (huge deficit)
    return normalize_score(gap, -100, 200)


def occupancy_pressure_score(occupancy_pressure_index: float) -> float:
    """
    Score based on occupancy pressure.
    Higher pressure = higher score (more investment needed).
    """
    return normalize_score(occupancy_pressure_index, 0, 100)


def growth_score(growth_pct: float) -> float:
    """
    Score based on visitor growth rate.
    Higher growth = higher score (demand is increasing).
    """
    return normalize_score(growth_pct, -20, 50)


def accessibility_score(
    has_airport: bool = False, highway_distance_km: float = 50
) -> float:
    """
    Score based on accessibility.
    Better accessibility = higher score (easier to develop).

    - Airport nearby: +30
    - Highway distance: closer = higher score
    """
    score = 0
    if has_airport:
        score += 30

    # Highway proximity: 0km = 70 points, 200km = 0 points
    highway_points = max(0, 70 - (highway_distance_km * 0.35))
    score += highway_points

    return round(min(100, score), 1)


def compute_priority_score(
    forecast_visitors: int,
    total_beds: int,
    occupancy_pressure: float,
    growth_pct: float,
    has_airport: bool = False,
    highway_distance_km: float = 50,
    weights: dict = None,
) -> dict:
    """
    Compute the composite priority investment score.

    Returns:
        dict with component scores, total score, and recommended investment type
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    components = {
        "demand_score": demand_score(forecast_visitors),
        "capacity_gap_score": capacity_gap_score(total_beds, forecast_visitors),
        "occupancy_pressure_score": occupancy_pressure_score(occupancy_pressure),
        "growth_score": growth_score(growth_pct),
        "accessibility_score": accessibility_score(has_airport, highway_distance_km),
    }

    # Weighted total
    total = sum(components[k] * weights.get(k, 0) for k in components)

    # Recommended investment type based on indicators
    investment_type = _recommend_investment_type(
        components, forecast_visitors, total_beds, occupancy_pressure
    )

    return {
        "priority_score": round(total, 1),
        "components": components,
        "weights": weights,
        "recommended_investment_type": investment_type,
        "justification": _generate_justification(
            components, forecast_visitors, total_beds
        ),
    }


def compute_priority_batch(
    governorates: list,
    weights: dict = None,
) -> list:
    """Compute priority scores for multiple governorates and rank them."""
    results = []
    for gov in governorates:
        score_result = compute_priority_score(
            forecast_visitors=gov.get("forecast_visitors", 0),
            total_beds=gov.get("total_beds", 0),
            occupancy_pressure=gov.get("occupancy_pressure", 0),
            growth_pct=gov.get("growth_pct", 0),
            has_airport=gov.get("has_airport", False),
            highway_distance_km=gov.get("highway_distance_km", 50),
            weights=weights,
        )
        results.append(
            {
                "governorate": gov.get("name"),
                "governorate_id": gov.get("id"),
                **score_result,
            }
        )

    # Sort by priority score descending
    results.sort(key=lambda x: x["priority_score"], reverse=True)

    # Add rank
    for i, r in enumerate(results):
        r["rank"] = i + 1

    return results


def _recommend_investment_type(
    components, forecast_visitors, total_beds, occupancy_pressure
):
    """Rule-based recommendation for investment type."""
    gap = components["capacity_gap_score"]
    demand = components["demand_score"]
    pressure = components["occupancy_pressure_score"]

    if pressure > 70 and gap > 60:
        return "new_hotel_4star"
    elif pressure > 50 and gap > 40:
        return "hotel_expansion"
    elif demand > 60 and total_beds < 500:
        return "eco_lodge"
    elif pressure > 40:
        return "guest_house"
    elif demand > 30:
        return "campsite_upgrade"
    else:
        return "infrastructure_improvement"


def _generate_justification(components, forecast_visitors, total_beds):
    """Generate human-readable justification for the score."""
    parts = []

    if components["demand_score"] > 60:
        parts.append(f"High forecast demand ({forecast_visitors:,} visitors)")

    if components["capacity_gap_score"] > 60:
        parts.append(f"Significant capacity gap (only {total_beds:,} beds)")
    elif components["capacity_gap_score"] > 40:
        parts.append("Moderate capacity gap")

    if components["occupancy_pressure_score"] > 70:
        parts.append("Critical occupancy pressure")
    elif components["occupancy_pressure_score"] > 50:
        parts.append("Elevated occupancy pressure")

    if components["growth_score"] > 60:
        parts.append("Strong visitor growth trend")

    if components["accessibility_score"] > 70:
        parts.append("Good transport accessibility")

    return "; ".join(parts) if parts else "Standard investment priority"


def investment_roi_proxy(
    current_visitors: int,
    forecast_visitors: int,
    current_beds: int,
    added_beds: int,
    avg_revenue_per_visitor: float = 150.0,
    avg_cost_per_bed: float = 50000.0,
) -> dict:
    """
    Simple ROI proxy for tourism infrastructure investment.
    Estimates additional revenue from added capacity vs investment cost.
    """
    if current_beds <= 0 or added_beds <= 0:
        return None
    current_visitors_per_bed = current_visitors / current_beds
    additional_visitors = int(added_beds * current_visitors_per_bed * 0.7)
    additional_revenue = additional_visitors * avg_revenue_per_visitor
    investment_cost = added_beds * avg_cost_per_bed
    payback_years = (
        round(investment_cost / additional_revenue, 1)
        if additional_revenue > 0
        else float("inf")
    )
    return {
        "additional_visitors": additional_visitors,
        "additional_revenue_annual": round(additional_revenue),
        "investment_cost": round(investment_cost),
        "payback_years": payback_years,
        "roi_5year": round(
            ((additional_revenue * 5) - investment_cost) / investment_cost * 100, 1
        ),
    }


def investment_urgency(occupancy_pct, growth_pct, current_beds, forecast_visitors):
    """How urgent is investment? 0-100."""
    urgency = 0
    if occupancy_pct > 80: urgency += 40
    elif occupancy_pct > 60: urgency += 20
    if growth_pct > 10: urgency += 30
    elif growth_pct > 5: urgency += 15
    if current_beds > 0 and forecast_visitors/current_beds > 50: urgency += 30
    return min(100, urgency)


def conflict_resilience_score(source_markets):
    """
    Score how resilient a governorate is to regional conflicts.
    Based on source market mix: more Saudi = more resilient, more Western = less.
    """
    if not source_markets:
        return 50  # default
    
    resilient_markets = {"Saudi Arabia", "Egypt", "Gulf States", "Jordan"}
    vulnerable_markets = {"USA", "UK", "Germany", "France", "Japan", "Italy"}
    
    resilient_pct = sum(v for k, v in source_markets.items() if k in resilient_markets)
    vulnerable_pct = sum(v for k, v in source_markets.items() if k in vulnerable_markets)
    
    return round(resilient_pct - vulnerable_pct + 50, 1)


def market_vulnerability_index(markets):
    """
    Aggregate vulnerability of all source markets to conflicts.
    0 = fully resilient, 100 = fully vulnerable.
    """
    if not markets:
        return 50
    
    exposure_map = {"critical": 100, "advisory-driven": 70, "ukraine-war": 60, "low": 10, "varies": 50}
    total_weight = sum(m.get("pct", 0) for m in markets)
    if total_weight == 0:
        return 50
    
    weighted = sum(m.get("pct", 0) * exposure_map.get(m.get("exposure", "varies"), 50) for m in markets)
    return round(weighted / total_weight, 1)


def conflict_lag_impact(severity, visitors):
    """How many months does conflict impact tourism?"""
    best_lag, best_r = 0, 0
    for lag in range(13):
        if lag >= len(severity): break
        sv = visitors[lag:] if lag > 0 else visitors
        ss = severity[:len(sv)]
        if len(sv) > 2:
            r = np.corrcoef(ss, sv)[0,1]
            if abs(r) > abs(best_r):
                best_r, best_lag = r, lag
    return {"lag_months": best_lag, "correlation": round(best_r, 3)}
