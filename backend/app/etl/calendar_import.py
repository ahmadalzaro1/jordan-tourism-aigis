"""
Islamic Calendar Generator for Jordan Tourism AI-GIS.

Computes Ramadan, Eid al-Fitr, and Eid al-Adha dates for 2020-2030.
The Islamic calendar shifts ~11 days per year relative to the Gregorian calendar.

These dates are used to model tourism demand suppression during Ramadan
and demand spikes during Eid holidays.
"""

import pandas as pd
import os

# Ramadan start dates (approximate, based on lunar calendar)
# Source: Islamic calendar calculations
RAMADAN_STARTS = {
    2020: (4, 24),
    2021: (4, 13),
    2022: (4, 2),
    2023: (3, 22),
    2024: (3, 11),
    2025: (2, 28),
    2026: (2, 18),
    2027: (2, 7),
    2028: (1, 27),
    2029: (1, 16),
    2030: (1, 5),
}

RAMADAN_DURATION = 30  # days

# Eid al-Fitr = day after Ramadan ends
# Eid al-Adha = ~70 days after Eid al-Fitr (10th Dhul Hijjah)
EID_ADHA_OFFSET = 70  # days after Eid al-Fitr

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "calendar",
)


def generate_islamic_calendar(years=range(2020, 2031)):
    """Generate Islamic holiday calendar for Jordan."""
    records = []

    for year in years:
        if year not in RAMADAN_STARTS:
            continue

        ramadan_start_month, ramadan_start_day = RAMADAN_STARTS[year]

        # Ramadan spans ~30 days
        from datetime import date, timedelta

        ramadan_start = date(year, ramadan_start_month, ramadan_start_day)
        ramadan_end = ramadan_start + timedelta(days=RAMADAN_DURATION - 1)

        # Eid al-Fitr (1-3 days after Ramadan)
        eid_fitr_start = ramadan_end + timedelta(days=1)
        eid_fitr_end = eid_fitr_start + timedelta(days=2)

        # Eid al-Adha
        eid_adha_start = eid_fitr_start + timedelta(days=EID_ADHA_OFFSET)
        eid_adha_end = eid_adha_start + timedelta(days=3)

        # Mark each month that contains these events
        for month in range(1, 13):
            month_start = date(year, month, 1)
            if month == 12:
                month_end = date(year, 12, 31)
            else:
                month_end = date(year, month + 1, 1) - timedelta(days=1)

            ramadan_days = 0
            eid_fitr_days = 0
            eid_adha_days = 0

            # Count days in this month
            current = month_start
            while current <= month_end:
                if ramadan_start <= current <= ramadan_end:
                    ramadan_days += 1
                if eid_fitr_start <= current <= eid_fitr_end:
                    eid_fitr_days += 1
                if eid_adha_start <= current <= eid_adha_end:
                    eid_adha_days += 1
                current += timedelta(days=1)

            records.append(
                {
                    "year": year,
                    "month": month,
                    "ramadan_days": ramadan_days,
                    "eid_fitr_days": eid_fitr_days,
                    "eid_adha_days": eid_adha_days,
                    "ramadan_start_date": ramadan_start.isoformat(),
                    "ramadan_end_date": ramadan_end.isoformat(),
                    "eid_fitr_date": eid_fitr_start.isoformat(),
                    "eid_adha_date": eid_adha_start.isoformat(),
                    "is_ramadan_month": ramadan_days > 0,
                    "is_eid_month": eid_fitr_days > 0 or eid_adha_days > 0,
                }
            )

    df = pd.DataFrame(records)

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "islamic_calendar.csv")
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} records to {output_path}")

    return df


def get_ramadan_impact_factor(ramadan_days: int) -> float:
    """
    Estimate tourism demand impact of Ramadan.
    Ramadan reduces tourism by ~20-30% due to daytime restrictions.
    The more days in a month, the bigger the impact.
    """
    if ramadan_days == 0:
        return 1.0
    # Linear interpolation: 0 days = 1.0, 30 days = 0.7
    return 1.0 - (ramadan_days / 30) * 0.3


def get_eid_boost_factor(eid_days: int) -> float:
    """
    Estimate tourism demand boost from Eid.
    Eid increases domestic tourism by ~40-60%.
    """
    if eid_days == 0:
        return 1.0
    # Each Eid day boosts by ~15%
    return 1.0 + (eid_days * 0.15)


if __name__ == "__main__":
    print("Generating Islamic calendar for Jordan...")
    df = generate_islamic_calendar()
    print(f"\nRamadan months (2020-2025):")
    ramadan_months = df[df["is_ramadan_month"]]
    for _, row in ramadan_months.iterrows():
        print(
            f"  {int(row['year'])}-{int(row['month']):02d}: {int(row['ramadan_days'])} Ramadan days, starts {row['ramadan_start_date']}"
        )
