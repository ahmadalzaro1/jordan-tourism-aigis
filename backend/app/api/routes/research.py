from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.db.models import Governorate, VisitorData, OccupancyData, Hotel, TourismSite
from app.analytics.indicators import (
    seasonal_amplitude, peak_month_concentration, oversaturation_ratio,
    site_diversification_index, intl_leakage_index, infrastructure_stress,
    demand_concentration, visitor_concentration_index,
)

router = APIRouter()


@router.get("/comprehensive/{governorate_id}")
def get_comprehensive_analysis(governorate_id: int, year: int = Query(2025), db: Session = Depends(get_db)):
    """Full analysis of a governorate using all discovered indicators."""
    gov = db.query(Governorate).filter(Governorate.id == governorate_id).first()
    if not gov:
        return {"error": "Governorate not found"}

    # Monthly data
    visitors = db.query(
        VisitorData.year, VisitorData.month,
        VisitorData.total_visitors, VisitorData.international_visitors,
    ).filter(VisitorData.governorate_id == governorate_id).order_by(
        VisitorData.year, VisitorData.month
    ).all()

    occupancy = db.query(
        OccupancyData.year, OccupancyData.month,
        OccupancyData.avg_occupancy_rate, OccupancyData.total_beds,
    ).filter(OccupancyData.governorate_id == governorate_id).order_by(
        OccupancyData.year, OccupancyData.month
    ).all()

    # Hotels and sites
    hotels = db.query(Hotel).filter(Hotel.governorate_id == governorate_id).all()
    site_list = db.query(TourismSite).filter(TourismSite.governorate_id == governorate_id).all()

    # Compute indicators
    monthly_vis = [v.total_visitors for v in visitors]
    monthly_occ = [o.avg_occupancy_rate for o in occupancy]
    intl_total = sum(v.international_visitors for v in visitors)
    vis_total = sum(monthly_vis)

    site_types = {}
    for s in site_list:
        site_types[s.site_type] = site_types.get(s.site_type, 0) + 1

    return {
        "governorate": {"id": gov.id, "name_en": gov.name_en, "name_ar": gov.name_ar, "code": gov.code},
        "data_points": len(visitors),
        "total_visitors": vis_total,
        "international_share": round(intl_total / vis_total * 100, 1) if vis_total > 0 else 0,
        "seasonal_amplitude": seasonal_amplitude(monthly_vis) if monthly_vis else None,
        "peak_concentration": peak_month_concentration(monthly_vis) if monthly_vis else None,
        "oversaturation": oversaturation_ratio(max(monthly_vis) if monthly_vis else 0, np.mean(monthly_vis) if monthly_vis else 0),
        "infrastructure_stress": infrastructure_stress(max(monthly_occ) if monthly_occ else 0, np.mean(monthly_occ) if monthly_occ else 0),
        "site_diversification": site_diversification_index(site_types) if site_types else None,
        "intl_leakage": intl_leakage_index(intl_total, vis_total),
        "accommodation": {"hotels": len(hotels), "rooms": sum(h.total_rooms or 0 for h in hotels), "beds": sum(h.total_beds or 0 for h in hotels)},
        "tourism_sites": {"total": len(site_list), "types": site_types},
    }


@router.get("/cross-governorate")
def get_cross_governorate_analysis(db: Session = Depends(get_db)):
    """Analyze relationships between governorates."""
    governorates = db.query(Governorate).all()
    results = []
    for gov in governorates:
        visitors = db.query(
            func.sum(VisitorData.total_visitors)
        ).filter(
            VisitorData.governorate_id == gov.id,
            VisitorData.year == 2025,
        ).scalar() or 0

        hotels_count = db.query(func.count(Hotel.id)).filter(Hotel.governorate_id == gov.id).scalar() or 0
        sites_count = db.query(func.count(TourismSite.id)).filter(TourismSite.governorate_id == gov.id).scalar() or 0

        results.append({
            "governorate": gov.name_en,
            "code": gov.code,
            "visitors_2025": visitors,
            "hotels": hotels_count,
            "sites": sites_count,
            "visitors_per_hotel": round(visitors / hotels_count) if hotels_count > 0 else 0,
        })

    return {"rankings": sorted(results, key=lambda x: x["visitors_2025"], reverse=True)}
