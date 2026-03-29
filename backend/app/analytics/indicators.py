"""
Demand-Capacity Diagnostic Indicators for Jordan Tourism AI-GIS.

Per RFP ToR Section 3.2.2:
- Rooms/Beds per 1,000 visitors
- Occupancy pressure index (avg + peak occupancy)
- Growth pressure index (multi-year visitor trend)
- Capacity adequacy index (beds relative to visitors)
- Over/under/balanced capacity classification

All indicators are transparent, formula-based, and 100% reproducible.
"""

import numpy as np
from typing import Optional


def rooms_per_1000_visitors(total_rooms: int, total_visitors: int) -> Optional[float]:
    """
    Rooms per 1,000 visitors.

    Formula: (total_rooms / total_visitors) * 1000

    Higher = more capacity per visitor (less stress)
    Lower = fewer rooms per visitor (more stress)
    """
    if total_visitors <= 0:
        return None
    return round((total_rooms / total_visitors) * 1000, 2)


def beds_per_1000_visitors(total_beds: int, total_visitors: int) -> Optional[float]:
    """
    Beds per 1,000 visitors.

    Formula: (total_beds / total_visitors) * 1000
    """
    if total_visitors <= 0:
        return None
    return round((total_beds / total_visitors) * 1000, 2)


def occupancy_pressure_index(
    avg_occupancy: float,
    peak_occupancy: float,
    avg_weight: float = 0.6,
    peak_weight: float = 0.4,
) -> float:
    """
    Occupancy Pressure Index (OPI).

    Combines average and peak occupancy rates into a single pressure metric.

    Formula: (avg_occupancy * avg_weight) + (peak_occupancy * peak_weight)

    Ranges:
      0-30: Low pressure (under-capacity)
      30-60: Moderate pressure (balanced)
      60-80: High pressure (approaching over-capacity)
      80-100: Critical pressure (over-capacity)

    Returns value 0-100.
    """
    return round((avg_occupancy * avg_weight) + (peak_occupancy * peak_weight), 2)


def growth_pressure_index(
    visitors_current: int,
    visitors_prev_year: int,
    visitors_2yr_ago: int = None,
) -> Optional[float]:
    """
    Growth Pressure Index (GPI).

    Measures visitor growth trend. Higher growth = more pressure on capacity.

    Formula (2-year): (current - prev) / prev * 100
    Formula (3-year): weighted average of 2-year growth rates

    Returns: percentage growth rate. Positive = growing (more pressure).
    """
    if visitors_prev_year <= 0:
        return None

    growth_1yr = ((visitors_current - visitors_prev_year) / visitors_prev_year) * 100

    if visitors_2yr_ago is not None and visitors_2yr_ago > 0:
        growth_2yr = ((visitors_prev_year - visitors_2yr_ago) / visitors_2yr_ago) * 100
        # Weighted average: recent growth weighted more
        return round((growth_1yr * 0.7) + (growth_2yr * 0.3), 2)

    return round(growth_1yr, 2)


def capacity_adequacy_index(
    total_beds: int,
    total_visitors: int,
    avg_stay_nights: float = 2.5,
    occupancy_target: float = 0.75,
) -> Optional[float]:
    """
    Capacity Adequacy Index (CAI).

    Measures whether beds are sufficient for visitor demand.

    Formula:
      demand_nights = total_visitors * avg_stay_nights
      supply_nights = total_beds * 365 * occupancy_target (annual)
      CAI = supply_nights / demand_nights

    Interpretation:
      > 1.0: Over-capacity (more supply than demand)
      = 1.0: Balanced
      < 1.0: Under-capacity (demand exceeds supply)
    """
    if total_visitors <= 0 or total_beds <= 0:
        return None

    demand_nights = total_visitors * avg_stay_nights
    supply_nights = total_beds * 365 * occupancy_target

    if demand_nights <= 0:
        return None

    return round(supply_nights / demand_nights, 3)


def compute_indicators_for_period(
    total_rooms: int,
    total_beds: int,
    total_visitors: int,
    avg_occupancy: float,
    peak_occupancy: float = None,
    visitors_prev_year: int = None,
    visitors_2yr_ago: int = None,
) -> dict:
    """
    Compute all indicators for a single governorate/period combination.
    Returns a dict ready for database storage.
    """
    if peak_occupancy is None:
        peak_occupancy = min(avg_occupancy * 1.3, 100)

    return {
        "rooms_per_1000_visitors": rooms_per_1000_visitors(total_rooms, total_visitors),
        "beds_per_1000_visitors": beds_per_1000_visitors(total_beds, total_visitors),
        "occupancy_pressure_index": occupancy_pressure_index(
            avg_occupancy, peak_occupancy
        ),
        "growth_pressure_index": growth_pressure_index(
            total_visitors, visitors_prev_year, visitors_2yr_ago
        ),
        "capacity_adequacy_index": capacity_adequacy_index(total_beds, total_visitors),
    }


def demand_elasticity(visitors_series: list, beds_series: list) -> float:
    """
    Demand elasticity: % change in visitors / % change in beds.
    > 1: elastic (demand responds strongly to capacity)
    < 1: inelastic (demand is insensitive to capacity)
    """
    if len(visitors_series) < 2 or len(beds_series) < 2:
        return None
    v_pct = [
        (visitors_series[i] - visitors_series[i - 1]) / visitors_series[i - 1]
        for i in range(1, len(visitors_series))
        if visitors_series[i - 1] > 0
    ]
    b_pct = [
        (beds_series[i] - beds_series[i - 1]) / beds_series[i - 1]
        for i in range(1, len(beds_series))
        if beds_series[i - 1] > 0
    ]
    if not v_pct or not b_pct:
        return None
    avg_v = sum(v_pct) / len(v_pct)
    avg_b = sum(b_pct) / len(b_pct)
    return round(avg_v / avg_b, 3) if avg_b != 0 else None


def peak_capacity_ratio(monthly_occupancy: list) -> float:
    """
    Peak-to-average occupancy ratio.
    Higher = more extreme seasonality (invest in seasonal capacity)
    Lower = stable demand (invest in permanent capacity)
    """
    if not monthly_occupancy:
        return None
    avg = sum(monthly_occupancy) / len(monthly_occupancy)
    peak = max(monthly_occupancy)
    return round(peak / avg, 3) if avg > 0 else None


def visitor_concentration_index(visitors_by_gov: dict) -> float:
    """
    Herfindahl-Hirschman Index for visitor concentration.
    0 = perfectly distributed, 1 = all in one governorate.
    Higher = more concentrated (risky for tourism sector).
    """
    total = sum(visitors_by_gov.values())
    if total == 0:
        return None
    shares = [v / total for v in visitors_by_gov.values()]
    return round(sum(s**2 for s in shares), 4)


def growth_acceleration(visitors_by_year: list) -> float:
    """
    Growth acceleration: change in growth rate.
    Positive = growth is accelerating (good for investment)
    Negative = growth is decelerating (caution needed)
    """
    if len(visitors_by_year) < 3:
        return None
    growth_rates = []
    for i in range(1, len(visitors_by_year)):
        if visitors_by_year[i - 1] > 0:
            growth_rates.append(
                (visitors_by_year[i] - visitors_by_year[i - 1])
                / visitors_by_year[i - 1]
            )
    if len(growth_rates) < 2:
        return None
    accels = [
        growth_rates[i] - growth_rates[i - 1] for i in range(1, len(growth_rates))
    ]
    return round(sum(accels) / len(accels), 4)


def tourism_dependency_ratio(tourism_visitors, population):
    """Tourism visitors as % of local population. Higher = more dependent on tourism."""
    if population <= 0: return None
    return round(tourism_visitors / population * 100, 2)


def seasonal_cv(monthly_values):
    """Coefficient of variation across months. Higher = more seasonal."""
    if not monthly_values or len(monthly_values) < 2: return None
    mean = sum(monthly_values)/len(monthly_values)
    if mean == 0: return None
    std = (sum((x-mean)**2 for x in monthly_values)/len(monthly_values))**0.5
    return round(std/mean, 3)


def capacity_utilization_efficiency(actual_visitors, theoretical_max):
    """How efficiently is capacity being used? 0-100%."""
    if theoretical_max <= 0: return None
    return round(min(100, actual_visitors/theoretical_max*100), 1)


def weather_adjusted_visitors(visitors, temp, optimal_temp=20.0):
    """
    Adjust visitor count for weather conditions.
    Optimal temperature is 20C (neither too hot nor too cold).
    """
    if temp is None or optimal_temp == 0:
        return visitors
    temp_factor = 1.0 - abs(temp - optimal_temp) / optimal_temp * 0.3
    return int(visitors * max(0.5, min(1.5, temp_factor)))


def ramadan_adjusted_classification(indicators, ramadan_days, total_days=30):
    """
    Adjust capacity classification to account for Ramadan effect.
    During Ramadan, apparent occupancy drops but is not a real capacity change.
    """
    if ramadan_days <= 0:
        return indicators.get("capacity_classification", "unknown")
    
    ramadan_factor = ramadan_days / total_days
    adjusted_occ = indicators.get("occupancy_pressure_index", 50) * (1 + ramadan_factor * 0.3)
    
    # Re-classify with adjusted occupancy
    adjusted = dict(indicators)
    adjusted["occupancy_pressure_index"] = min(100, adjusted_occ)
    return adjusted


def attention_to_visitor_ratio(wiki_views, actual_visitors):
    """
    Ratio of Wikipedia page views to actual visitors.
    High ratio = lots of interest but few visits = untapped potential.
    Low ratio = visitors come without researching = established destination.
    """
    if actual_visitors <= 0 or wiki_views <= 0:
        return None
    return round(wiki_views / actual_visitors, 3)


def airport_conversion_rate(total_visitors, airport_passengers):
    """
    What percentage of airport passengers become registered tourists?
    Low rate = many transit/business passengers.
    """
    if airport_passengers <= 0:
        return None
    return round(total_visitors / airport_passengers * 100, 2)


def gdp_tourism_elasticity(gdp_series, tourism_series):
    """
    How much does tourism change when GDP changes by 1%?
    > 1: tourism grows faster than economy
    < 1: tourism grows slower than economy
    """
    if len(gdp_series) < 2 or len(tourism_series) < 2:
        return None
    
    gdp_growth = [(gdp_series[i]-gdp_series[i-1])/gdp_series[i-1] for i in range(1,len(gdp_series)) if gdp_series[i-1]>0]
    tour_growth = [(tourism_series[i]-tourism_series[i-1])/tourism_series[i-1] for i in range(1,len(tourism_series)) if tourism_series[i-1]>0]
    
    min_len = min(len(gdp_growth), len(tour_growth))
    if min_len == 0:
        return None
    
    gdp_g = sum(gdp_growth[:min_len]) / min_len
    tour_g = sum(tour_growth[:min_len]) / min_len
    
    return round(tour_g / gdp_g, 3) if gdp_g != 0 else None


def demand_concentration(visitors_by_gov):
    """
    Herfindahl-Hirschman Index for demand concentration.
    0 = perfectly distributed, 1 = all in one governorate.
    Uses visitors_by_gov: dict of {gov_code: visitor_count}
    """
    total = sum(visitors_by_gov.values())
    if total <= 0:
        return None
    shares = [v / total for v in visitors_by_gov.values()]
    return round(sum(s ** 2 for s in shares), 4)


def growth_leads_occupancy(growth_series, occupancy_series):
    """Does visitor growth predict next month's occupancy? Returns lag and r."""
    best_lag, best_r = 0, 0
    for lag in range(1, 4):
        shifted_occ = occupancy_series[lag:] if lag > 0 else occupancy_series
        shifted_growth = growth_series[:len(shifted_occ)]
        if len(shifted_growth) > 3:
            r = np.corrcoef(shifted_growth, shifted_occ)[0,1]
            if abs(r) > abs(best_r):
                best_r, best_lag = r, lag
    return {"lag": best_lag, "correlation": round(best_r, 3)}


def variance_decomposition(monthly_values):
    """Decompose variance into trend vs seasonal components."""
    vals = np.array(monthly_values, dtype=float)
    trend = np.arange(len(vals))
    X = np.column_stack([np.ones(len(vals)), trend])
    beta, _, _, _ = np.linalg.lstsq(X, vals, rcond=None)
    tc = X @ beta
    total = np.var(vals)
    return {"trend_pct": round(np.var(tc)/total*100,1), "seasonal_pct": round(np.var(vals-tc)/total*100,1)}


def seasonal_amplitude(monthly_values):
    """Peak-to-trough spread as % of mean. Higher = more seasonal."""
    vals = np.array(monthly_values)
    if vals.mean() == 0: return None
    return round((vals.max() - vals.min()) / vals.mean() * 100, 1)


def complementarity_index(gov1_visitors, gov2_visitors):
    """Do two governorates grow together (>0) or compete (<0)?"""
    if len(gov1_visitors) != len(gov2_visitors): return None
    return round(np.corrcoef(gov1_visitors, gov2_visitors)[0,1], 3)


def recovery_speed(drops, series):
    """Average months to recover after a >15% drop."""
    speeds = []
    for i in drops:
        if i >= len(series): continue
        pre_level = series[i-1] if i > 0 else series[i]
        for j in range(i+1, min(i+13, len(series))):
            if series[j] >= pre_level:
                speeds.append(j - i)
                break
    return round(np.mean(speeds), 1) if speeds else None


def neighbor_spillover(gov_growth, neighbor_growth):
    """Does growth in one governorate predict neighbor growth next month?"""
    if len(gov_growth) != len(neighbor_growth): return None
    shifted = neighbor_growth[1:] if len(neighbor_growth) > 1 else []
    original = gov_growth[:len(shifted)]
    if len(shifted) < 3: return None
    return round(np.corrcoef(original, shifted)[0,1], 3)


def peak_month_concentration(monthly_values):
    """What % of annual total does the peak month capture?"""
    vals = np.array(monthly_values)
    total = vals.sum()
    if total == 0: return None
    return round(vals.max() / total * 100, 1)


def site_diversification_index(site_types):
    """HHI for site types. Lower = more diverse tourism offering."""
    if not site_types: return None
    total = sum(site_types.values())
    if total == 0: return None
    return round(sum((v/total)**2 for v in site_types.values()), 3)


def oversaturation_ratio(peak_visitors, mean_visitors):
    """Peak/mean ratio. Higher = more infrastructure stress in peak."""
    if mean_visitors <= 0: return None
    return round(peak_visitors / mean_visitors, 2)


def market_vulnerability(markets_data):
    """% of tourism from conflict-vulnerable markets."""
    total = sum(m.get('pct', 0) for m in markets_data)
    vuln = sum(m.get('pct', 0) for m in markets_data if m.get('exposure') in ['critical','advisory-driven'])
    return round(vuln / total * 100, 1) if total > 0 else None


def intl_leakage_index(intl_visitors, total_visitors):
    """International share. Higher = more money leaves the country."""
    if total_visitors <= 0: return None
    return round(intl_visitors / total_visitors * 100, 1)


def infrastructure_stress(peak_occupancy, avg_occupancy):
    """Peak/avg occupancy ratio. >2.0 = severe seasonal stress."""
    if avg_occupancy <= 0: return None
    return round(peak_occupancy / avg_occupancy, 2)
