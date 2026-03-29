"""
Generate sample tourism data for Jordan's 12 governorates.
Creates CSV files that can be loaded via the ETL pipeline or seed script.
"""

import csv
import random
import os
import json
import sys

random.seed(42)

# Import comprehensive tourism sites
sys.path.insert(0, os.path.dirname(__file__))
from jordan_tourism_comprehensive import TOURISM_SITES

GOVERNORATES = [
    {
        "code": "AMM",
        "name_en": "Amman",
        "name_ar": "عمان",
        "area_km2": 7579,
        "population": 4007526,
        "lat": 31.9454,
        "lng": 35.9284,
    },
    {
        "code": "IRB",
        "name_en": "Irbid",
        "name_ar": "إربد",
        "area_km2": 1572,
        "population": 1770000,
        "lat": 32.5556,
        "lng": 35.8500,
    },
    {
        "code": "ZAR",
        "name_en": "Zarqa",
        "name_ar": "الزرقاء",
        "area_km2": 4761,
        "population": 1364878,
        "lat": 32.0728,
        "lng": 36.0880,
    },
    {
        "code": "MAF",
        "name_en": "Mafraq",
        "name_ar": "المفرق",
        "area_km2": 26551,
        "population": 549000,
        "lat": 32.3428,
        "lng": 36.2080,
    },
    {
        "code": "JER",
        "name_en": "Jerash",
        "name_ar": "جرش",
        "area_km2": 410,
        "population": 237000,
        "lat": 32.2806,
        "lng": 35.8994,
    },
    {
        "code": "AJL",
        "name_en": "Ajloun",
        "name_ar": "عجلون",
        "area_km2": 420,
        "population": 176000,
        "lat": 32.3325,
        "lng": 35.7517,
    },
    {
        "code": "BAL",
        "name_en": "Balqa",
        "name_ar": "البلقاء",
        "area_km2": 1120,
        "population": 491700,
        "lat": 32.0383,
        "lng": 35.7272,
    },
    {
        "code": "MAD",
        "name_en": "Madaba",
        "name_ar": "مادبا",
        "area_km2": 940,
        "population": 189000,
        "lat": 31.7167,
        "lng": 35.8000,
    },
    {
        "code": "KAR",
        "name_en": "Karak",
        "name_ar": "الكرك",
        "area_km2": 3495,
        "population": 318000,
        "lat": 31.1853,
        "lng": 35.7047,
    },
    {
        "code": "TAF",
        "name_en": "Tafilah",
        "name_ar": "الطفيلة",
        "area_km2": 2209,
        "population": 96000,
        "lat": 30.8400,
        "lng": 35.6000,
    },
    {
        "code": "MAA",
        "name_en": "Ma'an",
        "name_ar": "معان",
        "area_km2": 32832,
        "population": 144000,
        "lat": 30.1962,
        "lng": 35.7341,
    },
    {
        "code": "AQAB",
        "name_en": "Aqaba",
        "name_ar": "العقبة",
        "area_km2": 6583,
        "population": 188000,
        "lat": 29.5321,
        "lng": 35.0063,
    },
]

# Tourism sites imported from jordan_tourism_comprehensive.py (80 sites across 12 governorates)

# Hotels per governorate (sample)
HOTELS = [
    # Amman (major hub)
    {
        "name": "Grand Hyatt Amman",
        "hotel_class": "5-star",
        "gov_code": "AMM",
        "lat": 31.9500,
        "lng": 35.9100,
        "rooms": 350,
        "beds": 600,
    },
    {
        "name": "Fairmont Amman",
        "hotel_class": "5-star",
        "gov_code": "AMM",
        "lat": 31.9600,
        "lng": 35.9200,
        "rooms": 310,
        "beds": 520,
    },
    {
        "name": "Le Royal Amman",
        "hotel_class": "5-star",
        "gov_code": "AMM",
        "lat": 31.9700,
        "lng": 35.9000,
        "rooms": 280,
        "beds": 450,
    },
    {
        "name": "Amman Rotana",
        "hotel_class": "5-star",
        "gov_code": "AMM",
        "lat": 31.9550,
        "lng": 35.9150,
        "rooms": 430,
        "beds": 700,
    },
    {
        "name": "Corp Amman Hotel",
        "hotel_class": "4-star",
        "gov_code": "AMM",
        "lat": 31.9480,
        "lng": 35.9250,
        "rooms": 200,
        "beds": 340,
    },
    {
        "name": "Movenpick Amman",
        "hotel_class": "5-star",
        "gov_code": "AMM",
        "lat": 31.9620,
        "lng": 35.9050,
        "rooms": 220,
        "beds": 380,
    },
    # Aqaba
    {
        "name": "Kempinski Aqaba",
        "hotel_class": "5-star",
        "gov_code": "AQAB",
        "lat": 29.5250,
        "lng": 35.0100,
        "rooms": 200,
        "beds": 340,
    },
    {
        "name": "Movenpick Resort Aqaba",
        "hotel_class": "5-star",
        "gov_code": "AQAB",
        "lat": 29.5200,
        "lng": 35.0050,
        "rooms": 300,
        "beds": 500,
    },
    {
        "name": "DoubleTree Aqaba",
        "hotel_class": "4-star",
        "gov_code": "AQAB",
        "lat": 29.5300,
        "lng": 35.0150,
        "rooms": 180,
        "beds": 300,
    },
    {
        "name": "Aqaba Gateway Hotel",
        "hotel_class": "3-star",
        "gov_code": "AQAB",
        "lat": 29.5350,
        "lng": 35.0080,
        "rooms": 120,
        "beds": 200,
    },
    # Petra/Wadi Musa
    {
        "name": "Movenpick Resort Petra",
        "hotel_class": "5-star",
        "gov_code": "MAA",
        "lat": 30.3200,
        "lng": 35.4700,
        "rooms": 180,
        "beds": 300,
    },
    {
        "name": "Petra Marriott",
        "hotel_class": "4-star",
        "gov_code": "MAA",
        "lat": 30.3250,
        "lng": 35.4750,
        "rooms": 250,
        "beds": 420,
    },
    {
        "name": "Crown Plaza Petra",
        "hotel_class": "4-star",
        "gov_code": "MAA",
        "lat": 30.3180,
        "lng": 35.4720,
        "rooms": 170,
        "beds": 280,
    },
    {
        "name": "Petra Moon Hotel",
        "hotel_class": "3-star",
        "gov_code": "MAA",
        "lat": 30.3220,
        "lng": 35.4680,
        "rooms": 90,
        "beds": 150,
    },
    # Dead Sea
    {
        "name": "Kempinski Ishtar Dead Sea",
        "hotel_class": "5-star",
        "gov_code": "BAL",
        "lat": 31.5800,
        "lng": 35.5500,
        "rooms": 340,
        "beds": 560,
    },
    {
        "name": "Hilton Dead Sea",
        "hotel_class": "5-star",
        "gov_code": "BAL",
        "lat": 31.5750,
        "lng": 35.5480,
        "rooms": 280,
        "beds": 460,
    },
    {
        "name": "Movenpick Dead Sea",
        "hotel_class": "5-star",
        "gov_code": "BAL",
        "lat": 31.5850,
        "lng": 35.5520,
        "rooms": 310,
        "beds": 510,
    },
    # Wadi Rum
    {
        "name": "Wadi Rum Night Camp",
        "hotel_class": "eco-lodge",
        "gov_code": "AQAB",
        "lat": 29.6100,
        "lng": 35.3900,
        "rooms": 40,
        "beds": 80,
    },
    {
        "name": "Sun City Camp",
        "hotel_class": "eco-lodge",
        "gov_code": "AQAB",
        "lat": 29.6150,
        "lng": 35.3950,
        "rooms": 30,
        "beds": 60,
    },
    # Irbid
    {
        "name": "Warwick Irbed",
        "hotel_class": "4-star",
        "gov_code": "IRB",
        "lat": 32.5500,
        "lng": 35.8500,
        "rooms": 120,
        "beds": 200,
    },
    # Karak
    {
        "name": "Karak Hotel",
        "hotel_class": "3-star",
        "gov_code": "KAR",
        "lat": 31.1800,
        "lng": 35.7000,
        "rooms": 60,
        "beds": 100,
    },
    # Madaba
    {
        "name": "Movenpick Madaba",
        "hotel_class": "4-star",
        "gov_code": "MAD",
        "lat": 31.7150,
        "lng": 35.8050,
        "rooms": 150,
        "beds": 250,
    },
]


def generate_visitors_csv(output_dir, years=range(2020, 2026)):
    """Generate monthly visitor data for all governorates."""
    rows = []
    for year in years:
        for month in range(1, 13):
            for gov in GOVERNORATES:
                # Base visitors vary by governorate size and seasonality
                base = gov["population"] * 0.005  # 0.5% of population as base tourism
                # Seasonal factor (peak in Mar-May, Sep-Nov; low in summer and winter)
                seasonal = {
                    1: 0.6,
                    2: 0.7,
                    3: 1.0,
                    4: 1.2,
                    5: 1.1,
                    6: 0.8,
                    7: 0.7,
                    8: 0.75,
                    9: 1.0,
                    10: 1.1,
                    11: 0.9,
                    12: 0.65,
                }
                multiplier = seasonal[month]
                # Tourism hotspots get more visitors
                hotspot = 1.0
                if gov["code"] in ["MAA"]:  # Petra
                    hotspot = 8.0
                elif gov["code"] in ["AQAB"]:  # Aqaba
                    hotspot = 5.0
                elif gov["code"] in ["AMM"]:  # Amman (gateway)
                    hotspot = 3.0
                elif gov["code"] in ["BAL"]:  # Dead Sea
                    hotspot = 4.0
                elif gov["code"] in ["JER"]:  # Jerash
                    hotspot = 3.0
                elif gov["code"] in ["IRB"]:  # Irbid
                    hotspot = 1.5

                total = int(
                    base * multiplier * hotspot * (0.85 + random.random() * 0.3)
                )
                intl = int(total * (0.3 + random.random() * 0.2))
                domestic = total - intl

                rows.append(
                    {
                        "governorate_code": gov["code"],
                        "year": year,
                        "month": month,
                        "total_visitors": total,
                        "international_visitors": intl,
                        "domestic_visitors": domestic,
                    }
                )

    filepath = os.path.join(output_dir, "visitors.csv")
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return filepath, len(rows)


def generate_occupancy_csv(output_dir, years=range(2020, 2026)):
    """Generate monthly occupancy data for all governorates."""
    rows = []
    for year in years:
        for month in range(1, 13):
            for gov in GOVERNORATES:
                # Hotels in this governorate
                gov_hotels = [h for h in HOTELS if h["gov_code"] == gov["code"]]
                total_rooms = sum(h["rooms"] for h in gov_hotels) or 50
                total_beds = sum(h["beds"] for h in gov_hotels) or 80

                # Occupancy rate: seasonal + hotspot
                base_rate = 45  # 45% base
                seasonal = {
                    1: -10,
                    2: -5,
                    3: 10,
                    4: 15,
                    5: 5,
                    6: -5,
                    7: -10,
                    8: -8,
                    9: 10,
                    10: 15,
                    11: 5,
                    12: -8,
                }
                rate = base_rate + seasonal[month] + random.randint(-8, 8)
                if gov["code"] in ["MAA", "AQAB"]:
                    rate += 15
                elif gov["code"] in ["BAL", "AMM"]:
                    rate += 10
                rate = max(10, min(95, rate))

                occupied = int(total_rooms * rate / 100)

                rows.append(
                    {
                        "governorate_code": gov["code"],
                        "year": year,
                        "month": month,
                        "avg_occupancy_rate": round(rate, 1),
                        "total_rooms": total_rooms,
                        "total_beds": total_beds,
                        "occupied_rooms": occupied,
                    }
                )

    filepath = os.path.join(output_dir, "occupancy.csv")
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return filepath, len(rows)


def generate_hotels_csv(output_dir):
    """Generate hotel data CSV."""
    filepath = os.path.join(output_dir, "hotels.csv")
    rows = []
    for h in HOTELS:
        rows.append(
            {
                "name": h["name"],
                "hotel_class": h["hotel_class"],
                "governorate_code": h["gov_code"],
                "latitude": h["lat"],
                "longitude": h["lng"],
                "total_rooms": h["rooms"],
                "total_beds": h["beds"],
            }
        )
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "name",
                "hotel_class",
                "governorate_code",
                "latitude",
                "longitude",
                "total_rooms",
                "total_beds",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    return filepath, len(rows)


def generate_sites_csv(output_dir):
    """Generate tourism sites CSV with comprehensive 80-site database."""
    filepath = os.path.join(output_dir, "sites.csv")
    rows = []
    for s in TOURISM_SITES:
        rows.append(
            {
                "name_en": s["name_en"],
                "name_ar": s["name_ar"],
                "site_type": s["site_type"],
                "governorate_code": s["gov_code"],
                "latitude": s["lat"],
                "longitude": s["lng"],
                "era": s.get("era", ""),
                "description": s.get("description", ""),
            }
        )
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "name_en",
                "name_ar",
                "site_type",
                "governorate_code",
                "latitude",
                "longitude",
                "era",
                "description",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    return filepath, len(rows)


def generate_site_visits_csv(output_dir, years=range(2020, 2026)):
    """Generate monthly site visit data."""
    rows = []
    for year in years:
        for month in range(1, 13):
            for i, site in enumerate(TOURISM_SITES):
                # Petra gets the most visitors
                base = 5000
                if "Petra" in site["name_en"]:
                    base = 120000
                elif "Dead Sea" in site["name_en"]:
                    base = 80000
                elif "Wadi Rum" in site["name_en"]:
                    base = 50000
                elif "Jerash" in site["name_en"]:
                    base = 40000
                elif "Roman Theatre" in site["name_en"] or "Citadel" in site["name_en"]:
                    base = 35000

                seasonal = {
                    1: 0.5,
                    2: 0.6,
                    3: 1.0,
                    4: 1.3,
                    5: 1.1,
                    6: 0.7,
                    7: 0.6,
                    8: 0.65,
                    9: 1.0,
                    10: 1.2,
                    11: 0.85,
                    12: 0.5,
                }
                visits = int(base * seasonal[month] * (0.85 + random.random() * 0.3))

                rows.append(
                    {
                        "site_id": i + 1,
                        "year": year,
                        "month": month,
                        "total_visits": visits,
                    }
                )

    filepath = os.path.join(output_dir, "site_visits.csv")
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return filepath, len(rows)


if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(__file__), "sample")
    os.makedirs(output_dir, exist_ok=True)

    path, count = generate_visitors_csv(output_dir)
    print(f"Generated {count} visitor records -> {path}")

    path, count = generate_occupancy_csv(output_dir)
    print(f"Generated {count} occupancy records -> {path}")

    path, count = generate_hotels_csv(output_dir)
    print(f"Generated {count} hotel records -> {path}")

    path, count = generate_sites_csv(output_dir)
    print(f"Generated {count} site records -> {path}")

    path, count = generate_site_visits_csv(output_dir)
    print(f"Generated {count} site visit records -> {path}")

    print("\nDone! Sample data generated in data/sample/")
