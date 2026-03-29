"""
Scoring Configuration for Jordan Tourism AI-GIS.

All scoring rules, weights, and thresholds are defined here.
MoTA/JTB analysts can adjust these values to tune the system.

Per RFP ToR Section 3.2.2(6):
"All scoring rules must be documented and adjustable by MoTA/JTB analysts"
"""

# ==========================================
# Priority Score Weights (must sum to 1.0)
# ==========================================
PRIORITY_WEIGHTS = {
    "demand_score": 0.25,  # Forecast visitor demand
    "capacity_gap_score": 0.30,  # Supply vs demand gap
    "occupancy_pressure_score": 0.20,  # Average + peak occupancy
    "growth_score": 0.15,  # Year-over-year growth
    "accessibility_score": 0.10,  # Transport network access
}

# ==========================================
# Capacity Classification Thresholds
# ==========================================
CLASSIFICATION_THRESHOLDS = {
    "rooms_per_1000": {
        "under": 5.0,  # Below 5 rooms per 1000 visitors = under-capacity
        "over": 20.0,  # Above 20 rooms per 1000 visitors = over-capacity
    },
    "beds_per_1000": {
        "under": 8.0,  # Below 8 beds per 1000 visitors = under-capacity
        "over": 35.0,  # Above 35 beds per 1000 visitors = over-capacity
    },
    "occupancy_pressure": {
        "under": 25.0,  # Below 25% occupancy pressure = over-capacity (inverted!)
        "over": 70.0,  # Above 70% occupancy pressure = under-capacity (inverted!)
    },
    "capacity_adequacy": {
        "under": 0.7,  # Below 0.7 adequacy = under-capacity
        "over": 1.5,  # Above 1.5 adequacy = over-capacity
    },
}

# ==========================================
# Investment Type Rules
# ==========================================
INVESTMENT_RULES = {
    "new_hotel_4star": {
        "condition": "pressure > 70 AND gap > 60",
        "description": "Critical pressure with significant capacity gap",
    },
    "hotel_expansion": {
        "condition": "pressure > 50 AND gap > 40",
        "description": "Elevated pressure with moderate gap",
    },
    "eco_lodge": {
        "condition": "demand > 60 AND beds < 500",
        "description": "High demand but limited accommodation",
    },
    "guest_house": {
        "condition": "pressure > 40",
        "description": "Moderate pressure across the board",
    },
    "campsite_upgrade": {
        "condition": "demand > 30",
        "description": "Growing demand, basic accommodation needed",
    },
    "infrastructure_improvement": {
        "condition": "default",
        "description": "Standard infrastructure investment",
    },
}

# ==========================================
# Accessibility Scoring Rules
# ==========================================
ACCESSIBILITY_RULES = {
    "airport_bonus": 30,  # Points added if governorate has airport
    "highway_max_points": 70,  # Maximum points from highway proximity
    "highway_max_distance_km": 200,  # Distance at which highway score = 0
    "airport_governorates": ["Amman", "Aqaba"],  # Governorates with airports
}

# ==========================================
# Forecast Configuration
# ==========================================
FORECAST_CONFIG = {
    "default_horizon_months": 12,
    "available_horizons": [6, 12, 24],
    "prophet_yearly_seasonality": True,
    "prophet_weekly_seasonality": False,
    "prophet_daily_seasonality": False,
    "arima_order": [1, 1, 1],
    "backtest_months": 12,
    "target_mape_percent": 20.0,  # RFP KPI: ≤ 20% at national level
}

# ==========================================
# Simulation Configuration
# ==========================================
SIMULATION_CONFIG = {
    "default_avg_stay_nights": 2.5,
    "default_occupancy_target": 0.75,
    "max_beds_scenario": 5000,
    "max_visitor_change_pct": 100,
}
