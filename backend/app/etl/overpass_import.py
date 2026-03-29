"""
Query OpenStreetMap Overpass API for ALL tourism-related POIs in Jordan.
Gets: hotels, hostels, guest houses, campsites, restaurants, cafes,
      archaeological sites, museums, viewpoints, attractions, etc.

Source: OpenStreetMap via Overpass API (free, no key needed)
License: ODbL (commercial use OK)
"""

import requests
import json
import csv
import os
import time

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
JORDAN_BBOX = "29.18,34.87,33.37,37.31"  # south,west,north,east


def query_overpass(query, timeout=300):
    """Execute an Overpass QL query."""
    print(f"Querying Overpass API (timeout={timeout}s)...")
    resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def get_all_tourism_pois():
    """Get ALL tourism-tagged features in Jordan."""
    query = f"""
    [out:json][timeout:300];
    (
      node["tourism"]({JORDAN_BBOX});
      way["tourism"]({JORDAN_BBOX});
      relation["tourism"]({JORDAN_BBOX});
    );
    out center;
    """
    return query_overpass(query)


def get_all_accommodation():
    """Get all accommodation (hotels, hostels, guest_houses, campsites, etc.)."""
    query = f"""
    [out:json][timeout:300];
    (
      node["tourism"~"hotel|hostel|guest_house|camp_site|chalet|apartment|motel|resort"]({JORDAN_BBOX});
      way["tourism"~"hotel|hostel|guest_house|camp_site|chalet|apartment|motel|resort"]({JORDAN_BBOX});
    );
    out center;
    """
    return query_overpass(query)


def get_all_food():
    """Get all restaurants, cafes, fast food."""
    query = f"""
    [out:json][timeout:300];
    (
      node["amenity"~"restaurant|cafe|fast_food|bar|pub"]({JORDAN_BBOX});
      way["amenity"~"restaurant|cafe|fast_food|bar|pub"]({JORDAN_BBOX});
    );
    out center;
    """
    return query_overpass(query)


def get_historical_sites():
    """Get all historic and archaeological sites."""
    query = f"""
    [out:json][timeout:300];
    (
      node["historic"]({JORDAN_BBOX});
      way["historic"]({JORDAN_BBOX});
      node["tourism"="attraction"]({JORDAN_BBOX});
      way["tourism"="attraction"]({JORDAN_BBOX});
      node["tourism"="museum"]({JORDAN_BBOX});
      way["tourism"="museum"]({JORDAN_BBOX});
    );
    out center;
    """
    return query_overpass(query)


def get_natural_attractions():
    """Get natural features relevant to tourism."""
    query = f"""
    [out:json][timeout:300];
    (
      node["natural"~"peak|spring|volcano|beach|cave_entrance"]({JORDAN_BBOX});
      way["natural"~"water|beach|wood|cliff"]({JORDAN_BBOX});
      relation["boundary"="national_park"]({JORDAN_BBOX});
    );
    out center;
    """
    return query_overpass(query)


def parse_osm_elements(data):
    """Parse Overpass JSON response into flat records."""
    records = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})

        # Get coordinates
        lat = el.get("lat")
        lng = el.get("lon")
        if not lat and "center" in el:
            lat = el["center"].get("lat")
            lng = el["center"].get("lon")

        record = {
            "osm_id": el.get("id"),
            "osm_type": el.get("type"),
            "name": tags.get("name", ""),
            "name_en": tags.get("name:en", ""),
            "name_ar": tags.get("name:ar", ""),
            "tourism": tags.get("tourism", ""),
            "historic": tags.get("historic", ""),
            "amenity": tags.get("amenity", ""),
            "natural": tags.get("natural", ""),
            "rooms": tags.get("rooms", ""),
            "beds": tags.get("beds", ""),
            "stars": tags.get("stars", ""),
            "addr_city": tags.get("addr:city", ""),
            "addr_street": tags.get("addr:street", ""),
            "phone": tags.get("phone", ""),
            "website": tags.get("website", ""),
            "opening_hours": tags.get("opening_hours", ""),
            "wheelchair": tags.get("wheelchair", ""),
            "latitude": lat,
            "longitude": lng,
        }
        records.append(record)

    return records


def run_full_osm_import(output_dir="/tmp/jordan_osm/overpass"):
    """Run all Overpass queries and export results."""
    os.makedirs(output_dir, exist_ok=True)

    queries = {
        "tourism_all": ("All Tourism POIs", get_all_tourism_pois),
        "accommodation": (
            "Accommodation (hotels, hostels, etc.)",
            get_all_accommodation,
        ),
        "food": ("Restaurants, Cafes, Bars", get_all_food),
        "historic": ("Historical & Archaeological Sites", get_historical_sites),
        "natural": ("Natural Attractions", get_natural_attractions),
    }

    summary = {}

    for key, (label, query_fn) in queries.items():
        print(f"\n--- {label} ---")
        try:
            data = query_fn()
            records = parse_osm_elements(data)
            print(f"  Found {len(records)} features")

            # Export to CSV
            if records:
                filepath = os.path.join(output_dir, f"osm_{key}.csv")
                with open(filepath, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=records[0].keys())
                    writer.writeheader()
                    writer.writerows(records)
                print(f"  Saved to {filepath}")

            summary[key] = len(records)

            # Be nice to the API
            time.sleep(2)

        except Exception as e:
            print(f"  ERROR: {e}")
            summary[key] = 0

    print(f"\n=== OSM Overpass Import Summary ===")
    for key, count in summary.items():
        print(f"  {key}: {count}")
    print(f"\nFiles saved to: {output_dir}")

    return summary


if __name__ == "__main__":
    run_full_osm_import()
