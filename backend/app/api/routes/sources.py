"""Dataset provenance inventory. Snapshots are not advertised as live feeds."""
import csv
from datetime import datetime, timezone
from fastapi import APIRouter
from app.paths import DATA_DIR
router = APIRouter()
SOURCES = [
 ("tourism", "sample/visitors.csv", "generated_demo", "https://www.mota.gov.jo/AR/List/ar_statisiics"),
 ("occupancy", "sample/occupancy.csv", "generated_demo", "https://www.mota.gov.jo/AR/List/ar_statisiics"),
 ("hotels", "sample/hotels.csv", "demo_inventory", "https://www.mota.gov.jo/AR/List/ar_statisiics"),
 ("sites", "sample/sites.csv", "curated_inventory", None),
 ("weather", "weather/all_governorates_weather.csv", "cached_snapshot", "https://open-meteo.com/en/docs/historical-weather-api"),
 ("economics", "economic/jordan_economic_indicators.csv", "cached_snapshot", "https://api.worldbank.org/v2/"),
 ("transport", "transport/governorate_accessibility.csv", "curated_estimate", None),
 ("calendar", "calendar/islamic_calendar.csv", "computed_calendar", None),
]

@router.get("")
def source_inventory():
    items = []
    for name, relative, kind, url in SOURCES:
        path = DATA_DIR / relative
        item = {"id": name, "file": relative, "kind": kind, "source_url": url,
                "available": path.is_file(), "live": False}
        if path.is_file():
            with path.open() as handle:
                reader = csv.DictReader(handle)
                item["columns"] = reader.fieldnames
                item["rows"] = sum(1 for _ in reader)
            item["local_file_modified_at"] = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
        items.append(item)
    return {"sources": items, "note": "Local file timestamps are not source publication dates. Demo tourism data is not official MoTA observations."}
