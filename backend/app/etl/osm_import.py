"""
Import ALL tourism POIs from OpenStreetMap for Jordan.
Uses the HDX humanitarian dataset (GeoJSON) which includes:
- All tourism=* tagged features (hotels, hostels, attractions, campsites, etc.)
- All amenity=* features (restaurants, cafes, etc.)
- All shop=* features
- With fields: name, name:en, name:ar, tourism, amenity, rooms, beds, addr:city

Source: https://data.humdata.org/dataset/hotosm_jor_points_of_interest
Updated: Monthly (March 2026)
License: Open Data Commons Open Database License (ODbL) - COMMERCIAL USE OK
"""

import json
import requests
import os
import csv
from collections import Counter

HDX_GEOJSON_URL = "https://s3.dualstack.us-east-1.amazonaws.com/production-raw-data-api/ISO3/JOR/points_of_interest/points/hotosm_jor_points_of_interest_points_geojson.zip"


def download_osm_data(output_dir):
    """Download OSM POI data from HDX."""
    os.makedirs(output_dir, exist_ok=True)
    zip_path = os.path.join(output_dir, "osm_jordan_pois.zip")

    print(f"Downloading OSM Jordan POI data from HDX...")
    resp = requests.get(HDX_GEOJSON_URL, stream=True)
    resp.raise_for_status()

    with open(zip_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    # Unzip
    import zipfile

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(output_dir)

    # Find the GeoJSON file
    geojson_path = None
    for fname in os.listdir(output_dir):
        if fname.endswith(".geojson"):
            geojson_path = os.path.join(output_dir, fname)
            break

    print(f"Downloaded and extracted to {geojson_path}")
    return geojson_path


def parse_osm_geojson(geojson_path):
    """Parse OSM GeoJSON and categorize features."""
    with open(geojson_path, "r") as f:
        data = json.load(f)

    tourism_features = []
    amenity_features = []
    shop_features = []
    all_features = []

    for feature in data.get("features", []):
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})

        # Get coordinates
        coords = geom.get("coordinates", [None, None])
        lng = coords[0] if len(coords) >= 2 else None
        lat = coords[1] if len(coords) >= 2 else None

        record = {
            "name": props.get("name", ""),
            "name_en": props.get("name:en", props.get("name_en", "")),
            "name_ar": props.get("name:ar", props.get("name_ar", "")),
            "tourism": props.get("tourism", ""),
            "amenity": props.get("amenity", ""),
            "shop": props.get("shop", ""),
            "man_made": props.get("man_made", ""),
            "rooms": props.get("rooms", ""),
            "beds": props.get("beds", ""),
            "addr_city": props.get("addr:city", props.get("addr_city", "")),
            "addr_street": props.get("addr:street", props.get("addr_street", "")),
            "opening_hours": props.get("opening_hours", ""),
            "latitude": lat,
            "longitude": lng,
            "osm_id": props.get("osm_id", ""),
            "osm_type": props.get("osm_type", ""),
        }

        all_features.append(record)

        if props.get("tourism"):
            tourism_features.append(record)
        if props.get("amenity"):
            amenity_features.append(record)
        if props.get("shop"):
            shop_features.append(record)

    return all_features, tourism_features, amenity_features, shop_features


def categorize_tourism(features):
    """Categorize tourism features by type."""
    categories = Counter()
    by_type = {}

    for f in features:
        t = f["tourism"]
        categories[t] += 1
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(f)

    return categories, by_type


def export_to_csv(features, filepath, fieldnames=None):
    """Export features to CSV."""
    if not features:
        return

    if not fieldnames:
        fieldnames = list(features[0].keys())

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(features)

    print(f"  Exported {len(features)} records to {filepath}")


def run_full_import(output_dir="/tmp/jordan_osm"):
    """Full import pipeline."""
    # Step 1: Download
    geojson_path = download_osm_data(output_dir)

    # Step 2: Parse
    all_features, tourism, amenity, shop = parse_osm_geojson(geojson_path)

    print(f"\n=== OSM Jordan POI Summary ===")
    print(f"Total features: {len(all_features)}")
    print(f"Tourism features: {len(tourism)}")
    print(f"Amenity features: {len(amenity)}")
    print(f"Shop features: {len(shop)}")

    # Step 3: Categorize tourism
    categories, by_type = categorize_tourism(tourism)
    print(f"\n=== Tourism Categories ===")
    for cat, count in categories.most_common():
        print(f"  {cat}: {count}")

    # Step 4: Export
    export_dir = os.path.join(output_dir, "exports")
    os.makedirs(export_dir, exist_ok=True)

    # Export all tourism
    export_to_csv(tourism, os.path.join(export_dir, "all_tourism_pois.csv"))

    # Export by type
    for ttype, features in by_type.items():
        safe_name = ttype.replace(" ", "_").replace("/", "_")
        export_to_csv(features, os.path.join(export_dir, f"tourism_{safe_name}.csv"))

    # Export accommodation (hotels, hostels, campsites, etc.)
    accommodation = [
        f
        for f in tourism
        if f["tourism"]
        in [
            "hotel",
            "hostel",
            "camp_site",
            "guest_house",
            "chalet",
            "apartment",
            "resort",
            "motel",
        ]
    ]
    export_to_csv(accommodation, os.path.join(export_dir, "accommodation_all.csv"))

    # Export all amenities (restaurants, cafes, etc.)
    export_to_csv(amenity, os.path.join(export_dir, "all_amenity_pois.csv"))

    # Export shops
    export_to_csv(shop, os.path.join(export_dir, "all_shop_pois.csv"))

    print(f"\n=== Export Summary ===")
    print(f"  Accommodation (hotels+hostels+camps+guest_houses): {len(accommodation)}")
    print(f"  All files saved to: {export_dir}")

    return {
        "total_features": len(all_features),
        "tourism": len(tourism),
        "amenity": len(amenity),
        "shop": len(shop),
        "accommodation": len(accommodation),
        "categories": dict(categories),
        "export_dir": export_dir,
    }


if __name__ == "__main__":
    result = run_full_import()
    print(f"\nDone! {result['total_features']} total POIs imported.")
