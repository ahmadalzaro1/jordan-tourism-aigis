"""
Capacity Classification for Jordan Tourism AI-GIS.

Classifies governorates into:
  - under: Under-capacity (demand exceeds supply, needs investment)
  - balanced: Balanced capacity
  - over: Over-capacity (excess supply)

Classification is based on configurable thresholds.
"""

# Default thresholds (configurable per RFP)
DEFAULT_THRESHOLDS = {
    "rooms_per_1000": {"under": 5.0, "over": 20.0},
    "beds_per_1000": {"under": 8.0, "over": 35.0},
    "occupancy_pressure": {"under": 25.0, "over": 70.0},
    "capacity_adequacy": {"under": 0.7, "over": 1.5},
}


def classify_capacity(indicators: dict, thresholds: dict = None) -> str:
    """
    Classify a governorate's capacity status.

    Uses multiple indicators and majority voting:
    1. rooms_per_1000_visitors: low = under, high = over
    2. beds_per_1000_visitors: low = under, high = over
    3. occupancy_pressure_index: low = over, high = under (inverted!)
    4. capacity_adequacy_index: low = under, high = over

    Returns: "under", "balanced", or "over"
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    votes = []

    # rooms_per_1000: higher = more capacity = over
    r1k = indicators.get("rooms_per_1000_visitors")
    if r1k is not None:
        t = thresholds["rooms_per_1000"]
        if r1k < t["under"]:
            votes.append("under")
        elif r1k > t["over"]:
            votes.append("over")
        else:
            votes.append("balanced")

    # beds_per_1000: higher = more capacity = over
    b1k = indicators.get("beds_per_1000_visitors")
    if b1k is not None:
        t = thresholds["beds_per_1000"]
        if b1k < t["under"]:
            votes.append("under")
        elif b1k > t["over"]:
            votes.append("over")
        else:
            votes.append("balanced")

    # occupancy_pressure: higher = more pressure = under (INVERTED)
    opi = indicators.get("occupancy_pressure_index")
    if opi is not None:
        t = thresholds["occupancy_pressure"]
        if opi < t["under"]:
            votes.append("over")  # low occupancy = over-capacity
        elif opi > t["over"]:
            votes.append("under")  # high occupancy = under-capacity
        else:
            votes.append("balanced")

    # capacity_adequacy: <1 = under, >1.5 = over
    cai = indicators.get("capacity_adequacy_index")
    if cai is not None:
        t = thresholds["capacity_adequacy"]
        if cai < t["under"]:
            votes.append("under")
        elif cai > t["over"]:
            votes.append("over")
        else:
            votes.append("balanced")

    if not votes:
        return "balanced"

    # Majority vote
    under_count = votes.count("under")
    over_count = votes.count("over")
    balanced_count = votes.count("balanced")

    if under_count > over_count and under_count > balanced_count:
        return "under"
    elif over_count > under_count and over_count > balanced_count:
        return "over"
    else:
        return "balanced"


def classify_batch(indicators_list: list, thresholds: dict = None) -> list:
    """Classify multiple governorate indicators at once."""
    results = []
    for indicators in indicators_list:
        classification = classify_capacity(indicators, thresholds)
        results.append({**indicators, "capacity_classification": classification})
    return results


def classify_capacity_seasonal(
    indicators_by_month: list, thresholds: dict = None
) -> dict:
    """
    Classify capacity by season instead of annual.
    Spring (Mar-May): highest demand
    Summer (Jun-Aug): moderate
    Fall (Sep-Nov): high demand
    Winter (Dec-Feb): low demand
    """
    seasons = {
        "spring": [3, 4, 5],
        "summer": [6, 7, 8],
        "fall": [9, 10, 11],
        "winter": [12, 1, 2],
    }
    results = {}
    for season_name, months in seasons.items():
        season_indicators = [
            ind for ind in indicators_by_month if ind.get("month") in months
        ]
        if season_indicators:
            avg = {}
            for key in [
                "rooms_per_1000_visitors",
                "beds_per_1000_visitors",
                "occupancy_pressure_index",
                "capacity_adequacy_index",
            ]:
                values = [
                    ind[key] for ind in season_indicators if ind.get(key) is not None
                ]
                avg[key] = sum(values) / len(values) if values else None
            results[season_name] = classify_capacity(avg, thresholds)
    return results
