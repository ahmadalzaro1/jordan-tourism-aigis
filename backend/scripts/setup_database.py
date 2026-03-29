"""
Complete setup: generate sample data, seed database, create views.
Run: python -m backend.scripts.setup_database
"""

import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Step 1: Generate sample data
    print("=" * 50)
    print("Step 1: Generating sample data...")
    print("=" * 50)
    from scripts.generate_sample_data import (
        generate_visitors_csv,
        generate_occupancy_csv,
        generate_hotels_csv,
        generate_sites_csv,
        generate_site_visits_csv,
    )

    sample_dir = os.path.join(base_dir, "data", "sample")
    os.makedirs(sample_dir, exist_ok=True)

    generate_visitors_csv(sample_dir)
    generate_occupancy_csv(sample_dir)
    generate_hotels_csv(sample_dir)
    generate_sites_csv(sample_dir)
    generate_site_visits_csv(sample_dir)
    print("Sample data generated.\n")

    # Step 2: Seed database
    print("=" * 50)
    print("Step 2: Seeding database...")
    print("=" * 50)
    from scripts.seed_database import seed

    seed()
    print("Database seeded.\n")

    # Step 3: Create SQL views
    print("=" * 50)
    print("Step 3: Creating SQL views...")
    print("=" * 50)

    from sqlalchemy import create_engine, text

    db_url = os.environ.get(
        "DATABASE_URL", "postgresql://tourism:tourism@localhost:5433/tourism_gis"
    )
    engine = create_engine(db_url)

    views_sql_path = os.path.join(base_dir, "data", "schema", "views.sql")
    with open(views_sql_path, "r") as f:
        views_sql = f.read()

    with engine.connect() as conn:
        for statement in views_sql.split(";"):
            statement = statement.strip()
            if statement and not statement.startswith("--"):
                try:
                    conn.execute(text(statement))
                    conn.commit()
                except Exception as e:
                    print(f"  Warning: {e}")

    print("SQL views created.\n")

    print("=" * 50)
    print("Setup complete!")
    print("=" * 50)
    print("\nServices:")
    print("  - Database:  localhost:5433 (PostgreSQL/PostGIS)")
    print("  - Backend:   http://localhost:8000 (FastAPI)")
    print("  - Frontend:  http://localhost:3000 (Next.js)")
    print("  - Superset:  http://localhost:8088 (Apache Superset)")
    print("\nSuperset login: admin / admin")


if __name__ == "__main__":
    main()
