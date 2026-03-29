"""
Analytics API routes for Jordan Tourism AI-GIS.

Endpoints:
- POST /api/analytics/indicators — Compute indicators for a governorate/period
- POST /api/analytics/forecast — Run demand forecast for a governorate
- POST /api/analytics/simulate — Run what-if simulation
- POST /api/analytics/score — Compute priority investment scores
- GET  /api/analytics/investment-ranker — Rank all governorates by priority
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.db.database import get_db
from app.db.models import (
    Governorate,
    VisitorData,
    OccupancyData,
    Hotel,
    CapacityIndicator,
)
from app.analytics.indicators import compute_indicators_for_period
from app.analytics.classification import classify_capacity
from app.analytics.forecasting import prepare_monthly_series, forecast_best
from app.analytics.simulation import accommodation_scenario, demand_scenario
from app.analytics.scoring import compute_priority_score, compute_priority_batch
from app.analytics.clusters import (
    TOURISM_CLUSTERS,
    ACCOMMODATION_CLASSES,
    get_cluster_summary,
)

router = APIRouter()


@router.post("/indicators/{governorate_id}")
def compute_indicators(
    governorate_id: int,
    year: int = Query(2025),
    db: Session = Depends(get_db),
):
    """Compute all capacity indicators for a governorate in a given year."""
    gov = db.query(Governorate).filter(Governorate.id == governorate_id).first()
    if not gov:
        raise HTTPException(404, "Governorate not found")

    # Get current year data
    visitors = (
        db.query(
            func.sum(VisitorData.total_visitors),
            func.sum(VisitorData.international_visitors),
            func.sum(VisitorData.domestic_visitors),
        )
        .filter(
            VisitorData.governorate_id == governorate_id,
            VisitorData.year == year,
        )
        .first()
    )

    occupancy = (
        db.query(
            func.avg(OccupancyData.avg_occupancy_rate),
            func.max(OccupancyData.avg_occupancy_rate),
            func.coalesce(func.sum(OccupancyData.total_rooms), 0),
            func.coalesce(func.sum(OccupancyData.total_beds), 0),
        )
        .filter(
            OccupancyData.governorate_id == governorate_id,
            OccupancyData.year == year,
        )
        .first()
    )

    # Get previous year visitors
    prev_visitors = (
        db.query(
            func.sum(VisitorData.total_visitors),
        )
        .filter(
            VisitorData.governorate_id == governorate_id,
            VisitorData.year == year - 1,
        )
        .scalar()
        or 0
    )

    two_yr_visitors = (
        db.query(
            func.sum(VisitorData.total_visitors),
        )
        .filter(
            VisitorData.governorate_id == governorate_id,
            VisitorData.year == year - 2,
        )
        .scalar()
        or 0
    )

    total_visitors = visitors[0] or 0
    total_rooms = occupancy[2] or 0
    total_beds = occupancy[3] or 0
    avg_occ = occupancy[0] or 0
    peak_occ = occupancy[1] or 0

    indicators = compute_indicators_for_period(
        total_rooms=total_rooms,
        total_beds=total_beds,
        total_visitors=total_visitors,
        avg_occupancy=avg_occ,
        peak_occupancy=peak_occ,
        visitors_prev_year=prev_visitors,
        visitors_2yr_ago=two_yr_visitors,
    )

    classification = classify_capacity(indicators)

    # Save to database
    existing = (
        db.query(CapacityIndicator)
        .filter(
            CapacityIndicator.governorate_id == governorate_id,
            CapacityIndicator.year == year,
            CapacityIndicator.month == 0,  # annual aggregate
        )
        .first()
    )

    if existing:
        for k, v in indicators.items():
            setattr(existing, k, v)
        existing.capacity_classification = classification
    else:
        record = CapacityIndicator(
            governorate_id=governorate_id,
            year=year,
            month=0,
            **indicators,
            capacity_classification=classification,
        )
        db.add(record)
    db.commit()

    return {
        "governorate": {"id": gov.id, "name_en": gov.name_en, "code": gov.code},
        "year": year,
        "inputs": {
            "total_visitors": total_visitors,
            "total_rooms": total_rooms,
            "total_beds": total_beds,
            "avg_occupancy": round(avg_occ, 1),
            "peak_occupancy": round(peak_occ, 1),
        },
        "indicators": indicators,
        "classification": classification,
    }


@router.post("/forecast/{governorate_id}")
def run_forecast(
    governorate_id: int,
    horizon_months: int = Query(12, ge=1, le=36),
    db: Session = Depends(get_db),
):
    """Run demand forecast for a governorate."""
    gov = db.query(Governorate).filter(Governorate.id == governorate_id).first()
    if not gov:
        raise HTTPException(404, "Governorate not found")

    # Get monthly visitor data
    visitor_data = (
        db.query(
            VisitorData.year,
            VisitorData.month,
            VisitorData.total_visitors.label("total"),
        )
        .filter(
            VisitorData.governorate_id == governorate_id,
        )
        .order_by(VisitorData.year, VisitorData.month)
        .all()
    )

    if len(visitor_data) < 12:
        raise HTTPException(400, "Need at least 12 months of data for forecasting")

    data_list = [
        {"year": r.year, "month": r.month, "total": r.total} for r in visitor_data
    ]
    df = prepare_monthly_series(data_list)
    result = forecast_best(df, horizon_months)

    return {
        "governorate": {"id": gov.id, "name_en": gov.name_en, "code": gov.code},
        **result,
    }


@router.post("/simulate")
def run_simulation(
    governorate_id: int = Query(...),
    scenario_type: str = Query(...),  # "accommodation" or "demand"
    added_beds: int = Query(0),
    visitor_change_pct: float = Query(0),
    target_months_ahead: int = Query(
        12, description="Target future period in months (default 12)"
    ),
    db: Session = Depends(get_db),
):
    """
    Run forecast-based what-if simulation for a governorate.

    Per RFP ToR Section 3.2.2(5):
    - Compares scenario against FORECASTED BASELINE (not current data)
    - Target future period is configurable (default 12 months ahead)
    - Recalculates all indicators for the future period
    """
    gov = db.query(Governorate).filter(Governorate.id == governorate_id).first()
    if not gov:
        raise HTTPException(404, "Governorate not found")

    year = 2025  # latest year with data

    # Step 1: Get historical visitor data and run forecast
    visitor_data = (
        db.query(
            VisitorData.year,
            VisitorData.month,
            VisitorData.total_visitors.label("total"),
        )
        .filter(
            VisitorData.governorate_id == governorate_id,
        )
        .order_by(VisitorData.year, VisitorData.month)
        .all()
    )

    if len(visitor_data) < 12:
        raise HTTPException(
            400, "Need at least 12 months of data for forecast-based simulation"
        )

    data_list = [
        {"year": r.year, "month": r.month, "total": r.total} for r in visitor_data
    ]
    df = prepare_monthly_series(data_list)
    forecast_result = forecast_best(df, target_months_ahead)

    # Step 2: Get forecasted visitors for target future period
    forecast_entries = forecast_result.get("forecast", [])
    if not forecast_entries:
        raise HTTPException(500, "Forecast failed to produce results")

    # Use the target month from forecast (index target_months_ahead - 1)
    target_idx = min(target_months_ahead - 1, len(forecast_entries) - 1)
    target_forecast = forecast_entries[target_idx]
    forecast_visitors = target_forecast["predicted"]

    # Also sum forecast for annual projection
    forecast_annual = sum(f["predicted"] for f in forecast_entries)

    # Step 3: Get current accommodation data (beds/rooms don't change unless scenario adds them)
    occupancy = (
        db.query(
            func.avg(OccupancyData.avg_occupancy_rate),
            func.max(OccupancyData.avg_occupancy_rate),
            func.coalesce(func.sum(OccupancyData.total_rooms), 0),
            func.coalesce(func.sum(OccupancyData.total_beds), 0),
        )
        .filter(
            OccupancyData.governorate_id == governorate_id,
            OccupancyData.year == year,
        )
        .first()
    )

    current_beds = occupancy[3] or 0
    current_rooms = occupancy[2] or 0
    current_avg_occ = occupancy[0] or 0
    current_peak_occ = occupancy[1] or 0

    # Step 4: Calculate FORECASTED BASELINE indicators
    # For future period, estimate occupancy based on forecasted demand
    if current_beds > 0:
        forecast_occupancy = min(
            95, (forecast_visitors * 2.5) / (current_beds * 30) * 100
        )
    else:
        forecast_occupancy = current_avg_occ

    forecast_baseline_indicators = compute_indicators_for_period(
        total_rooms=current_rooms,
        total_beds=current_beds,
        total_visitors=forecast_visitors,
        avg_occupancy=forecast_occupancy,
        peak_occupancy=min(100, forecast_occupancy * 1.3),
        visitors_prev_year=forecast_visitors,  # self-reference for stable growth
        visitors_2yr_ago=None,
    )
    baseline_class = classify_capacity(forecast_baseline_indicators)

    # Step 5: Build forecasted baseline
    forecasted_baseline = {
        "total_rooms": current_rooms,
        "total_beds": current_beds,
        "total_visitors": forecast_visitors,
        "avg_occupancy": round(forecast_occupancy, 1),
        "peak_occupancy": round(min(100, forecast_occupancy * 1.3), 1),
        "visitors_prev_year": forecast_visitors,
        "indicators": forecast_baseline_indicators,
        "classification": baseline_class,
    }

    # Step 6: Apply scenario on top of forecasted baseline
    if scenario_type == "accommodation":
        result = _accommodation_scenario_forecast(
            forecasted_baseline,
            gov.name_en,
            added_beds,
            target_forecast,
            forecast_entries,
        )
    elif scenario_type == "demand":
        result = _demand_scenario_forecast(
            forecasted_baseline,
            gov.name_en,
            visitor_change_pct,
            target_forecast,
            forecast_entries,
        )
    else:
        raise HTTPException(400, f"Invalid scenario_type: {scenario_type}")

    # Step 7: Add simulation metadata
    result["simulation_time_reference"] = {
        "target_future_period": f"{target_forecast['year']}-{target_forecast['month']:02d}",
        "months_ahead": target_months_ahead,
        "method": forecast_result.get("method", "unknown"),
    }

    return result


def _accommodation_scenario_forecast(
    baseline, gov_name, added_beds, target_forecast, forecast_entries
):
    """Accommodation scenario using forecasted baseline."""
    from app.analytics.simulation import accommodation_scenario

    # Adjust occupancy: more beds at same forecasted visitors = lower occupancy
    scenario_beds = baseline["total_beds"] + added_beds
    scenario_rooms = baseline["total_rooms"] + max(0, added_beds // 2)

    if baseline["total_beds"] > 0 and added_beds != 0:
        occ_factor = baseline["total_beds"] / scenario_beds
        scenario_occupancy = baseline["avg_occupancy"] * occ_factor
    else:
        scenario_occupancy = baseline["avg_occupancy"]

    scenario_indicators = compute_indicators_for_period(
        total_rooms=scenario_rooms,
        total_beds=scenario_beds,
        total_visitors=baseline["total_visitors"],
        avg_occupancy=scenario_occupancy,
        peak_occupancy=min(100, scenario_occupancy * 1.3),
        visitors_prev_year=baseline["total_visitors"],
    )
    scenario_class = classify_capacity(scenario_indicators)

    return {
        "scenario_type": "accommodation",
        "governorate": gov_name,
        "changes": {"added_beds": added_beds, "added_rooms": max(0, added_beds // 2)},
        "baseline": baseline,
        "scenario": {
            "total_rooms": scenario_rooms,
            "total_beds": scenario_beds,
            "total_visitors": baseline["total_visitors"],
            "avg_occupancy": round(scenario_occupancy, 1),
            "indicators": scenario_indicators,
            "classification": scenario_class,
        },
        "difference": _compute_diff(
            baseline["indicators"],
            scenario_indicators,
            baseline["classification"],
            scenario_class,
        ),
    }


def _demand_scenario_forecast(
    baseline, gov_name, visitor_change_pct, target_forecast, forecast_entries
):
    """Visitor demand scenario using forecasted baseline."""
    from app.analytics.simulation import demand_scenario

    multiplier = 1 + (visitor_change_pct / 100)
    scenario_visitors = int(baseline["total_visitors"] * multiplier)
    scenario_occupancy = min(95, baseline["avg_occupancy"] * multiplier)

    scenario_indicators = compute_indicators_for_period(
        total_rooms=baseline["total_rooms"],
        total_beds=baseline["total_beds"],
        total_visitors=scenario_visitors,
        avg_occupancy=scenario_occupancy,
        peak_occupancy=min(100, scenario_occupancy * 1.3),
        visitors_prev_year=baseline["total_visitors"],
    )
    scenario_class = classify_capacity(scenario_indicators)

    return {
        "scenario_type": "demand",
        "governorate": gov_name,
        "changes": {
            "visitor_change_pct": visitor_change_pct,
            "visitors_before": baseline["total_visitors"],
            "visitors_after": scenario_visitors,
        },
        "baseline": baseline,
        "scenario": {
            "total_rooms": baseline["total_rooms"],
            "total_beds": baseline["total_beds"],
            "total_visitors": scenario_visitors,
            "avg_occupancy": round(scenario_occupancy, 1),
            "indicators": scenario_indicators,
            "classification": scenario_class,
        },
        "difference": _compute_diff(
            baseline["indicators"],
            scenario_indicators,
            baseline["classification"],
            scenario_class,
        ),
    }


def _compute_diff(base_ind, scen_ind, base_class, scen_class):
    """Compute difference between baseline and scenario indicators."""
    diff = {}
    for key in base_ind:
        b = base_ind[key]
        s = scen_ind.get(key)
        if b is not None and s is not None:
            diff[key] = {
                "baseline": b,
                "scenario": s,
                "change": round(s - b, 3),
                "change_pct": round(((s - b) / b) * 100, 1) if b != 0 else None,
            }
    diff["classification_changed"] = base_class != scen_class
    diff["classification_before"] = base_class
    diff["classification_after"] = scen_class
    return diff


@router.get("/investment-ranker")
def investment_ranker(db: Session = Depends(get_db)):
    """Rank all governorates by investment priority score."""
    year = 2025
    governorates = db.query(Governorate).all()

    batch_input = []
    for gov in governorates:
        visitors = (
            db.query(
                func.sum(VisitorData.total_visitors),
            )
            .filter(
                VisitorData.governorate_id == gov.id,
                VisitorData.year == year,
            )
            .scalar()
            or 0
        )

        occupancy = (
            db.query(
                func.avg(OccupancyData.avg_occupancy_rate),
                func.coalesce(func.sum(OccupancyData.total_beds), 0),
            )
            .filter(
                OccupancyData.governorate_id == gov.id,
                OccupancyData.year == year,
            )
            .first()
        )

        prev = (
            db.query(func.sum(VisitorData.total_visitors))
            .filter(
                VisitorData.governorate_id == gov.id,
                VisitorData.year == year - 1,
            )
            .scalar()
            or 1
        )

        growth = ((visitors - prev) / prev * 100) if prev > 0 else 0

        batch_input.append(
            {
                "id": gov.id,
                "name": gov.name_en,
                "forecast_visitors": visitors,
                "total_beds": occupancy[1] if occupancy else 0,
                "occupancy_pressure": occupancy[0] if occupancy else 0,
                "growth_pct": growth,
                "has_airport": gov.code in ["AMM", "AQAB"],
                "highway_distance_km": 20 if gov.code in ["AMM", "AQAB"] else 50,
            }
        )

    results = compute_priority_batch(batch_input)
    return {"year": year, "rankings": results}


@router.post("/compute-all")
def compute_all_indicators(year: int = Query(2025), db: Session = Depends(get_db)):
    """Compute indicators for ALL governorates. Bulk operation."""
    governorates = db.query(Governorate).all()
    results = []

    for gov in governorates:
        try:
            visitors = (
                db.query(
                    func.sum(VisitorData.total_visitors),
                )
                .filter(
                    VisitorData.governorate_id == gov.id,
                    VisitorData.year == year,
                )
                .first()
            )

            occupancy = (
                db.query(
                    func.avg(OccupancyData.avg_occupancy_rate),
                    func.max(OccupancyData.avg_occupancy_rate),
                    func.coalesce(func.sum(OccupancyData.total_rooms), 0),
                    func.coalesce(func.sum(OccupancyData.total_beds), 0),
                )
                .filter(
                    OccupancyData.governorate_id == gov.id,
                    OccupancyData.year == year,
                )
                .first()
            )

            prev = (
                db.query(func.sum(VisitorData.total_visitors))
                .filter(
                    VisitorData.governorate_id == gov.id,
                    VisitorData.year == year - 1,
                )
                .scalar()
                or 0
            )

            indicators = compute_indicators_for_period(
                total_rooms=occupancy[2] or 0,
                total_beds=occupancy[3] or 0,
                total_visitors=visitors[0] or 0,
                avg_occupancy=occupancy[0] or 0,
                peak_occupancy=occupancy[1] or 0,
                visitors_prev_year=prev,
            )

            classification = classify_capacity(indicators)
            results.append(
                {
                    "governorate": gov.name_en,
                    "code": gov.code,
                    "indicators": indicators,
                    "classification": classification,
                }
            )
        except Exception as e:
            results.append(
                {
                    "governorate": gov.name_en,
                    "code": gov.code,
                    "error": str(e),
                }
            )

    return {"year": year, "results": results}


@router.get("/clusters")
def list_clusters():
    """List all tourism clusters."""
    return {
        "clusters": [
            {
                "key": k,
                "name_en": v["name_en"],
                "name_ar": v["name_ar"],
                "description": v["description"],
                "governorate_codes": v["governorate_codes"],
                "site_count": len(v["site_names"]),
            }
            for k, v in TOURISM_CLUSTERS.items()
        ]
    }


@router.get("/clusters/{cluster_key}")
def get_cluster_detail(cluster_key: str, db: Session = Depends(get_db)):
    """Get detailed data for a tourism cluster."""
    summary = get_cluster_summary(cluster_key, db)
    if not summary:
        raise HTTPException(404, f"Cluster '{cluster_key}' not found")
    return summary


@router.post("/simulate-national")
def run_national_simulation(
    scenario_type: str = Query(...),
    added_beds: int = Query(0),
    visitor_change_pct: float = Query(0),
    target_months_ahead: int = Query(12),
    db: Session = Depends(get_db),
):
    """
    National-level what-if simulation.
    Aggregates all governorates into national totals for the scenario.
    """
    year = 2025
    governorates = db.query(Governorate).all()

    # National totals
    total_visitors = (
        db.query(func.sum(VisitorData.total_visitors))
        .filter(
            VisitorData.year == year,
        )
        .scalar()
        or 0
    )

    prev_visitors = (
        db.query(func.sum(VisitorData.total_visitors))
        .filter(
            VisitorData.year == year - 1,
        )
        .scalar()
        or 0
    )

    occupancy = (
        db.query(
            func.avg(OccupancyData.avg_occupancy_rate),
            func.coalesce(func.sum(OccupancyData.total_rooms), 0),
            func.coalesce(func.sum(OccupancyData.total_beds), 0),
        )
        .filter(OccupancyData.year == year)
        .first()
    )

    baseline = {
        "total_rooms": occupancy[1] if occupancy else 0,
        "total_beds": occupancy[2] if occupancy else 0,
        "total_visitors": total_visitors,
        "avg_occupancy": occupancy[0] if occupancy else 0,
        "peak_occupancy": (occupancy[0] * 1.3) if occupancy else 0,
        "visitors_prev_year": prev_visitors,
    }

    # Apply scenario
    if scenario_type == "accommodation":
        from app.analytics.simulation import accommodation_scenario

        result = accommodation_scenario(baseline, "Jordan (National)", added_beds)
    elif scenario_type == "demand":
        from app.analytics.simulation import demand_scenario

        result = demand_scenario(baseline, "Jordan (National)", visitor_change_pct)
    else:
        raise HTTPException(400, f"Invalid scenario_type: {scenario_type}")

    result["simulation_time_reference"] = {
        "target": "national",
        "months_ahead": target_months_ahead,
    }

    return result


@router.get("/accommodation-classes")
def list_accommodation_classes():
    """List available accommodation classes for simulation filtering."""
    return {"classes": ACCOMMODATION_CLASSES}
