from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.db.models import (
    Governorate,
    VisitorData,
    OccupancyData,
    Hotel,
    CapacityIndicator,
)

router = APIRouter()


@router.get("/national")
def get_national_summary(
    year: int = Query(None),
    destination_type: str = Query(None),  # cultural, nature, coastal, religious
    db: Session = Depends(get_db),
):
    # If destination_type filter, get governorates that have matching sites
    gov_filter = None
    if destination_type:
        from app.db.models import TourismSite

        matching_sites = (
            db.query(TourismSite.governorate_id)
            .filter(TourismSite.site_type == destination_type)
            .distinct()
            .all()
        )
        gov_filter = [s[0] for s in matching_sites]

    # Total visitors
    vq = db.query(
        func.coalesce(func.sum(VisitorData.total_visitors), 0),
        func.coalesce(func.sum(VisitorData.international_visitors), 0),
        func.coalesce(func.sum(VisitorData.domestic_visitors), 0),
    )
    if year:
        vq = vq.filter(VisitorData.year == year)
    if gov_filter:
        vq = vq.filter(VisitorData.governorate_id.in_(gov_filter))
    visitors = vq.first()

    # Total rooms and beds
    rbq = db.query(
        func.coalesce(func.sum(Hotel.total_rooms), 0),
        func.coalesce(func.sum(Hotel.total_beds), 0),
        func.count(Hotel.id),
    )
    if gov_filter:
        rbq = rbq.filter(Hotel.governorate_id.in_(gov_filter))
    rooms_beds = rbq.first()

    # Average occupancy
    oq = db.query(func.coalesce(func.avg(OccupancyData.avg_occupancy_rate), 0))
    if year:
        oq = oq.filter(OccupancyData.year == year)
    if gov_filter:
        oq = oq.filter(OccupancyData.governorate_id.in_(gov_filter))
    avg_occ = oq.scalar()

    # High priority zones
    pq = db.query(func.count(CapacityIndicator.id)).filter(
        CapacityIndicator.capacity_classification == "under"
    )
    if year:
        pq = pq.filter(CapacityIndicator.year == year)
    if gov_filter:
        pq = pq.filter(CapacityIndicator.governorate_id.in_(gov_filter))
    priority_zones = pq.scalar() or 0

    return {
        "total_visitors": visitors[0] if visitors else 0,
        "international_visitors": visitors[1] if visitors else 0,
        "domestic_visitors": visitors[2] if visitors else 0,
        "total_rooms": rooms_beds[0] if rooms_beds else 0,
        "total_beds": rooms_beds[1] if rooms_beds else 0,
        "total_hotels": rooms_beds[2] if rooms_beds else 0,
        "avg_occupancy_rate": round(avg_occ, 1) if avg_occ else 0,
        "high_priority_zones": priority_zones,
        "destination_type_filter": destination_type,
    }


@router.get("/governorate/{gov_id}")
def get_governorate_summary(
    gov_id: int, year: int = Query(None), db: Session = Depends(get_db)
):
    gov = db.query(Governorate).filter(Governorate.id == gov_id).first()
    if not gov:
        return {"error": "Governorate not found"}

    # Visitor time series
    vq = db.query(VisitorData).filter(VisitorData.governorate_id == gov_id)
    if year:
        vq = vq.filter(VisitorData.year == year)
    visitors = vq.order_by(VisitorData.year, VisitorData.month).all()

    # Occupancy time series
    oq = db.query(OccupancyData).filter(OccupancyData.governorate_id == gov_id)
    if year:
        oq = oq.filter(OccupancyData.year == year)
    occupancy = oq.order_by(OccupancyData.year, OccupancyData.month).all()

    # Hotels
    hotels = db.query(Hotel).filter(Hotel.governorate_id == gov_id).all()
    total_rooms = sum(h.total_rooms or 0 for h in hotels)
    total_beds = sum(h.total_beds or 0 for h in hotels)

    # Latest indicators
    indicators = (
        db.query(CapacityIndicator)
        .filter(CapacityIndicator.governorate_id == gov_id)
        .order_by(CapacityIndicator.year.desc(), CapacityIndicator.month.desc())
        .first()
    )

    return {
        "governorate": {
            "id": gov.id,
            "name_en": gov.name_en,
            "name_ar": gov.name_ar,
            "code": gov.code,
            "area_km2": gov.area_km2,
            "population": gov.population,
        },
        "visitors": [
            {
                "year": v.year,
                "month": v.month,
                "total": v.total_visitors,
                "international": v.international_visitors,
                "domestic": v.domestic_visitors,
            }
            for v in visitors
        ],
        "occupancy": [
            {
                "year": o.year,
                "month": o.month,
                "rate": o.avg_occupancy_rate,
                "rooms": o.total_rooms,
                "beds": o.total_beds,
            }
            for o in occupancy
        ],
        "accommodation": {
            "hotel_count": len(hotels),
            "total_rooms": total_rooms,
            "total_beds": total_beds,
        },
        "indicators": {
            "rooms_per_1000_visitors": indicators.rooms_per_1000_visitors
            if indicators
            else None,
            "beds_per_1000_visitors": indicators.beds_per_1000_visitors
            if indicators
            else None,
            "occupancy_pressure_index": indicators.occupancy_pressure_index
            if indicators
            else None,
            "capacity_classification": indicators.capacity_classification
            if indicators
            else None,
            "priority_score": indicators.priority_score if indicators else None,
        }
        if indicators
        else None,
    }
