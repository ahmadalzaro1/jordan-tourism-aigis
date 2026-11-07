"""Initialize tables, seed bundled demo data, and create Superset views.
Existing bundled observations are preserved unless --generate-demo is requested.
"""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.paths import DATA_DIR
from app.db.database import engine
from sqlalchemy import text
from scripts.seed_database import seed
from app.official import official_mode


def main(generate_demo=False):
    if generate_demo and official_mode():
        raise ValueError("Set DATA_MODE=demo explicitly before generating demonstration observations")
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    if generate_demo:
        from scripts.generate_sample_data import generate_visitors_csv, generate_occupancy_csv, generate_hotels_csv, generate_sites_csv, generate_site_visits_csv
        sample_dir = DATA_DIR / "sample"
        sample_dir.mkdir(parents=True, exist_ok=True)
        for generator in [generate_visitors_csv, generate_occupancy_csv, generate_hotels_csv, generate_sites_csv, generate_site_visits_csv]:
            generator(str(sample_dir))
    seed()
    sql = (DATA_DIR / "schema/views.sql").read_text()
    with engine.begin() as connection:
        for statement in sql.split(";"):
            if statement.strip():
                connection.execute(text(statement))
    print("Database initialized in " + ("official mode: reviewed locations, no generated observations." if official_mode() else "demo mode: generated observations and legacy SQL views."))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate-demo", action="store_true", help="Explicitly regenerate demo CSVs before seeding")
    main(parser.parse_args().generate_demo)
