from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from geoalchemy2.functions import ST_AsGeoJSON
from app.db.database import get_db
from app.db.models import Governorate, TourismSite, Hotel

router = APIRouter()


@router.get("/governorates")
def get_governorates(db: Session = Depends(get_db)):
    results = db.query(
        Governorate.id,
        Governorate.name_en,
        Governorate.name_ar,
        Governorate.code,
        Governorate.area_km2,
        Governorate.population,
        func.ST_AsGeoJSON(Governorate.geometry).label("geojson"),
    ).all()
    features = []
    for r in results:
        geojson = eval(r.geojson) if r.geojson else None
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": r.id,
                    "name_en": r.name_en,
                    "name_ar": r.name_ar,
                    "code": r.code,
                    "area_km2": r.area_km2,
                    "population": r.population,
                },
                "geometry": geojson,
            }
        )
    return {"type": "FeatureCollection", "features": features}


@router.get("/hotels")
def get_hotels(governorate_id: int = None, db: Session = Depends(get_db)):
    q = db.query(
        Hotel.id,
        Hotel.name,
        Hotel.hotel_class,
        Hotel.governorate_id,
        Hotel.latitude,
        Hotel.longitude,
        Hotel.total_rooms,
        Hotel.total_beds,
        func.ST_AsGeoJSON(Hotel.geometry).label("geojson"),
    )
    if governorate_id:
        q = q.filter(Hotel.governorate_id == governorate_id)
    results = q.all()
    features = []
    for r in results:
        geojson = eval(r.geojson) if r.geojson else None
        if not geojson and r.latitude and r.longitude:
            geojson = {"type": "Point", "coordinates": [r.longitude, r.latitude]}
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": r.id,
                    "name": r.name,
                    "hotel_class": r.hotel_class,
                    "governorate_id": r.governorate_id,
                    "total_rooms": r.total_rooms,
                    "total_beds": r.total_beds,
                },
                "geometry": geojson,
            }
        )
    return {"type": "FeatureCollection", "features": features}


@router.get("/sites")
def get_sites(governorate_id: int = None, db: Session = Depends(get_db)):
    q = db.query(
        TourismSite.id,
        TourismSite.name_en,
        TourismSite.name_ar,
        TourismSite.site_type,
        TourismSite.governorate_id,
        TourismSite.latitude,
        TourismSite.longitude,
        func.ST_AsGeoJSON(TourismSite.geometry).label("geojson"),
    )
    if governorate_id:
        q = q.filter(TourismSite.governorate_id == governorate_id)
    results = q.all()
    features = []
    for r in results:
        geojson = eval(r.geojson) if r.geojson else None
        if not geojson and r.latitude and r.longitude:
            geojson = {"type": "Point", "coordinates": [r.longitude, r.latitude]}
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": r.id,
                    "name_en": r.name_en,
                    "name_ar": r.name_ar,
                    "site_type": r.site_type,
                    "governorate_id": r.governorate_id,
                },
                "geometry": geojson,
            }
        )
    return {"type": "FeatureCollection", "features": features}
