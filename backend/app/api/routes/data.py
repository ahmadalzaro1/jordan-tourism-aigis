from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.db.models import (
    VisitorData,
    OccupancyData,
    SiteVisitData,
    Governorate,
    TourismSite,
    Hotel,
)

router = APIRouter()


@router.get("/visitors")
def get_visitors(
    governorate_id: int = Query(None),
    year: int = Query(None),
    month: int = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(VisitorData)
    if governorate_id:
        q = q.filter(VisitorData.governorate_id == governorate_id)
    if year:
        q = q.filter(VisitorData.year == year)
    if month:
        q = q.filter(VisitorData.month == month)
    results = q.order_by(VisitorData.year, VisitorData.month).all()
    return [
        {
            "id": r.id,
            "governorate_id": r.governorate_id,
            "year": r.year,
            "month": r.month,
            "total_visitors": r.total_visitors,
            "international_visitors": r.international_visitors,
            "domestic_visitors": r.domestic_visitors,
        }
        for r in results
    ]


@router.get("/occupancy")
def get_occupancy(
    governorate_id: int = Query(None),
    year: int = Query(None),
    month: int = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(OccupancyData)
    if governorate_id:
        q = q.filter(OccupancyData.governorate_id == governorate_id)
    if year:
        q = q.filter(OccupancyData.year == year)
    if month:
        q = q.filter(OccupancyData.month == month)
    results = q.order_by(OccupancyData.year, OccupancyData.month).all()
    return [
        {
            "id": r.id,
            "governorate_id": r.governorate_id,
            "year": r.year,
            "month": r.month,
            "avg_occupancy_rate": r.avg_occupancy_rate,
            "total_rooms": r.total_rooms,
            "total_beds": r.total_beds,
            "occupied_rooms": r.occupied_rooms,
        }
        for r in results
    ]


@router.get("/site-visits")
def get_site_visits(
    site_id: int = Query(None),
    year: int = Query(None),
    month: int = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(SiteVisitData)
    if site_id:
        q = q.filter(SiteVisitData.site_id == site_id)
    if year:
        q = q.filter(SiteVisitData.year == year)
    if month:
        q = q.filter(SiteVisitData.month == month)
    results = q.order_by(SiteVisitData.year, SiteVisitData.month).all()
    return [
        {
            "id": r.id,
            "site_id": r.site_id,
            "year": r.year,
            "month": r.month,
            "total_visits": r.total_visits,
        }
        for r in results
    ]


@router.get("/rooms-beds")
def get_rooms_beds(
    governorate_id: int = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(
        Governorate.id,
        Governorate.name_en,
        func.coalesce(func.sum(Hotel.total_rooms), 0).label("total_rooms"),
        func.coalesce(func.sum(Hotel.total_beds), 0).label("total_beds"),
        func.count(Hotel.id).label("hotel_count"),
    ).outerjoin(Hotel, Hotel.governorate_id == Governorate.id)
    if governorate_id:
        q = q.filter(Governorate.id == governorate_id)
    q = q.group_by(Governorate.id, Governorate.name_en)
    results = q.all()
    return [
        {
            "governorate_id": r.id,
            "governorate_name": r.name_en,
            "total_rooms": r.total_rooms,
            "total_beds": r.total_beds,
            "hotel_count": r.hotel_count,
        }
        for r in results
    ]
