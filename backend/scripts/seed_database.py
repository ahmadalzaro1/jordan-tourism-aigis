"""
Seed the database with Jordan governorates and sample tourism data.
Run: python -m backend.scripts.seed_database
"""

import os
import sys
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import Base
from app.db.models import Governorate, TourismSite, Hotel
from scripts.generate_sample_data import GOVERNORATES, HOTELS
from scripts.jordan_tourism_comprehensive import TOURISM_SITES

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://tourism:tourism@localhost:5433/tourism_gis"
)


def seed():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Seed governorates
    print("Seeding governorates...")
    for gov in GOVERNORATES:
        existing = db.query(Governorate).filter(Governorate.code == gov["code"]).first()
        if not existing:
            g = Governorate(
                name_en=gov["name_en"],
                name_ar=gov["name_ar"],
                code=gov["code"],
                area_km2=gov["area_km2"],
                population=gov["population"],
            )
            db.add(g)
    db.commit()

    # Build governorate lookup
    govs = {g.code: g.id for g in db.query(Governorate).all()}
    print(f"  {len(govs)} governorates in database")

    # Seed tourism sites
    print("Seeding tourism sites...")
    for site in TOURISM_SITES:
        existing = (
            db.query(TourismSite).filter(TourismSite.name_en == site["name_en"]).first()
        )
        if not existing:
            s = TourismSite(
                name_en=site["name_en"],
                name_ar=site["name_ar"],
                site_type=site["site_type"],
                governorate_id=govs.get(site["gov_code"]),
                latitude=site["lat"],
                longitude=site["lng"],
                era=site.get("era"),
                description=site.get("description"),
            )
            db.add(s)
    db.commit()
    print(f"  {len(TOURISM_SITES)} tourism sites seeded")

    # Seed hotels
    print("Seeding hotels...")
    for hotel in HOTELS:
        existing = db.query(Hotel).filter(Hotel.name == hotel["name"]).first()
        if not existing:
            h = Hotel(
                name=hotel["name"],
                hotel_class=hotel["hotel_class"],
                governorate_id=govs.get(hotel["gov_code"]),
                latitude=hotel["lat"],
                longitude=hotel["lng"],
                total_rooms=hotel["rooms"],
                total_beds=hotel["beds"],
            )
            db.add(h)
    db.commit()
    print(f"  {len(HOTELS)} hotels seeded")

    # Seed visitor and occupancy data from CSVs
    sample_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample"
    )

    if os.path.exists(os.path.join(sample_dir, "visitors.csv")):
        print("Seeding visitor data from CSV...")
        from app.etl.pipeline import run_etl

        result = run_etl(os.path.join(sample_dir, "visitors.csv"), "visitors", db)
        print(f"  {result['inserted']} records inserted, {result['skipped']} skipped")

    if os.path.exists(os.path.join(sample_dir, "occupancy.csv")):
        print("Seeding occupancy data from CSV...")
        from app.etl.pipeline import run_etl

        result = run_etl(os.path.join(sample_dir, "occupancy.csv"), "occupancy", db)
        print(f"  {result['inserted']} records inserted, {result['skipped']} skipped")

    if os.path.exists(os.path.join(sample_dir, "site_visits.csv")):
        print("Seeding site visits from CSV...")
        from app.etl.pipeline import run_etl

        result = run_etl(os.path.join(sample_dir, "site_visits.csv"), "site_visits", db)
        print(f"  {result['inserted']} records inserted, {result['skipped']} skipped")

    db.close()
    print("\nDatabase seeded successfully!")


if __name__ == "__main__":
    seed()
