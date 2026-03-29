import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import (
    VisitorData,
    OccupancyData,
    SiteVisitData,
    Hotel,
    TourismSite,
    Governorate,
)


def run_etl(filepath: str, dataset_type: str, db: Session) -> dict:
    """Main ETL entry point. Routes to appropriate handler based on dataset_type."""
    handlers = {
        "visitors": _import_visitors,
        "occupancy": _import_occupancy,
        "site_visits": _import_site_visits,
        "hotels": _import_hotels,
        "sites": _import_sites,
    }
    handler = handlers.get(dataset_type)
    if not handler:
        raise ValueError(f"Unknown dataset_type: {dataset_type}")
    return handler(filepath, db)


def _import_visitors(filepath: str, db: Session) -> dict:
    """Import visitor data from CSV.
    Expected columns: governorate_code, year, month, total_visitors, international_visitors, domestic_visitors
    """
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    required = ["governorate_code", "year", "month", "total_visitors"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Build governorate lookup
    govs = {g.code: g.id for g in db.query(Governorate).all()}

    processed = 0
    inserted = 0
    skipped = 0
    errored = 0
    errors = []

    for _, row in df.iterrows():
        processed += 1
        try:
            gov_id = govs.get(str(row["governorate_code"]))
            if not gov_id:
                errors.append(
                    f"Row {processed}: Unknown governorate code '{row['governorate_code']}'"
                )
                errored += 1
                continue

            year = int(row["year"])
            month = int(row["month"])

            # Check for duplicate
            existing = (
                db.query(VisitorData)
                .filter(
                    VisitorData.governorate_id == gov_id,
                    VisitorData.year == year,
                    VisitorData.month == month,
                )
                .first()
            )

            if existing:
                skipped += 1
                continue

            record = VisitorData(
                governorate_id=gov_id,
                year=year,
                month=month,
                total_visitors=int(row.get("total_visitors", 0)),
                international_visitors=int(row.get("international_visitors", 0)),
                domestic_visitors=int(row.get("domestic_visitors", 0)),
            )
            db.add(record)
            inserted += 1
        except Exception as e:
            errors.append(f"Row {processed}: {str(e)}")
            errored += 1

    db.commit()
    return _result(processed, inserted, skipped, errored, errors)


def _import_occupancy(filepath: str, db: Session) -> dict:
    """Import occupancy data from CSV.
    Expected columns: governorate_code, year, month, avg_occupancy_rate, total_rooms, total_beds, occupied_rooms
    """
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    required = ["governorate_code", "year", "month"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    govs = {g.code: g.id for g in db.query(Governorate).all()}

    processed = 0
    inserted = 0
    skipped = 0
    errored = 0
    errors = []

    for _, row in df.iterrows():
        processed += 1
        try:
            gov_id = govs.get(str(row["governorate_code"]))
            if not gov_id:
                errors.append(
                    f"Row {processed}: Unknown governorate code '{row['governorate_code']}'"
                )
                errored += 1
                continue

            year = int(row["year"])
            month = int(row["month"])

            existing = (
                db.query(OccupancyData)
                .filter(
                    OccupancyData.governorate_id == gov_id,
                    OccupancyData.year == year,
                    OccupancyData.month == month,
                )
                .first()
            )

            if existing:
                skipped += 1
                continue

            record = OccupancyData(
                governorate_id=gov_id,
                year=year,
                month=month,
                avg_occupancy_rate=float(row.get("avg_occupancy_rate", 0)),
                total_rooms=int(row.get("total_rooms", 0)),
                total_beds=int(row.get("total_beds", 0)),
                occupied_rooms=int(row.get("occupied_rooms", 0)),
            )
            db.add(record)
            inserted += 1
        except Exception as e:
            errors.append(f"Row {processed}: {str(e)}")
            errored += 1

    db.commit()
    return _result(processed, inserted, skipped, errored, errors)


def _import_site_visits(filepath: str, db: Session) -> dict:
    """Import site visit data from CSV.
    Expected columns: site_id, year, month, total_visits
    """
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    processed = 0
    inserted = 0
    skipped = 0
    errored = 0
    errors = []

    for _, row in df.iterrows():
        processed += 1
        try:
            site_id = int(row["site_id"])
            year = int(row["year"])
            month = int(row["month"])

            existing = (
                db.query(SiteVisitData)
                .filter(
                    SiteVisitData.site_id == site_id,
                    SiteVisitData.year == year,
                    SiteVisitData.month == month,
                )
                .first()
            )

            if existing:
                skipped += 1
                continue

            record = SiteVisitData(
                site_id=site_id,
                year=year,
                month=month,
                total_visits=int(row.get("total_visits", 0)),
            )
            db.add(record)
            inserted += 1
        except Exception as e:
            errors.append(f"Row {processed}: {str(e)}")
            errored += 1

    db.commit()
    return _result(processed, inserted, skipped, errored, errors)


def _import_hotels(filepath: str, db: Session) -> dict:
    """Import hotel data from CSV.
    Expected columns: name, hotel_class, governorate_code, latitude, longitude, total_rooms, total_beds
    """
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    govs = {g.code: g.id for g in db.query(Governorate).all()}

    processed = 0
    inserted = 0
    skipped = 0
    errored = 0
    errors = []

    for _, row in df.iterrows():
        processed += 1
        try:
            gov_id = govs.get(str(row.get("governorate_code", "")))
            lat = (
                float(row.get("latitude", 0)) if pd.notna(row.get("latitude")) else None
            )
            lng = (
                float(row.get("longitude", 0))
                if pd.notna(row.get("longitude"))
                else None
            )

            # Check duplicate by name + governorate
            existing = (
                db.query(Hotel)
                .filter(
                    Hotel.name == str(row["name"]),
                    Hotel.governorate_id == gov_id,
                )
                .first()
            )

            if existing:
                skipped += 1
                continue

            record = Hotel(
                name=str(row["name"]),
                hotel_class=str(row.get("hotel_class", "unclassified")),
                governorate_id=gov_id,
                latitude=lat,
                longitude=lng,
                total_rooms=int(row.get("total_rooms", 0)),
                total_beds=int(row.get("total_beds", 0)),
            )
            db.add(record)
            inserted += 1
        except Exception as e:
            errors.append(f"Row {processed}: {str(e)}")
            errored += 1

    db.commit()
    return _result(processed, inserted, skipped, errored, errors)


def _import_sites(filepath: str, db: Session) -> dict:
    """Import tourism site data from CSV.
    Expected columns: name_en, name_ar, site_type, governorate_code, latitude, longitude
    """
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    govs = {g.code: g.id for g in db.query(Governorate).all()}

    processed = 0
    inserted = 0
    skipped = 0
    errored = 0
    errors = []

    for _, row in df.iterrows():
        processed += 1
        try:
            gov_id = govs.get(str(row.get("governorate_code", "")))
            lat = (
                float(row.get("latitude", 0)) if pd.notna(row.get("latitude")) else None
            )
            lng = (
                float(row.get("longitude", 0))
                if pd.notna(row.get("longitude"))
                else None
            )

            existing = (
                db.query(TourismSite)
                .filter(
                    TourismSite.name_en == str(row["name_en"]),
                )
                .first()
            )

            if existing:
                skipped += 1
                continue

            record = TourismSite(
                name_en=str(row["name_en"]),
                name_ar=str(row.get("name_ar", "")),
                site_type=str(row.get("site_type", "general")),
                governorate_id=gov_id,
                latitude=lat,
                longitude=lng,
            )
            db.add(record)
            inserted += 1
        except Exception as e:
            errors.append(f"Row {processed}: {str(e)}")
            errored += 1

    db.commit()
    return _result(processed, inserted, skipped, errored, errors)


def _result(processed, inserted, skipped, errored, errors):
    status = "success" if errored == 0 else ("partial" if inserted > 0 else "failed")
    return {
        "processed": processed,
        "inserted": inserted,
        "skipped": skipped,
        "errored": errored,
        "status": status,
        "errors": errors[:20],
        "error_details": "; ".join(errors[:5]) if errors else None,
    }
