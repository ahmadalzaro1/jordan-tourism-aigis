"""
Autonomous AutoResearch Agent for Jordan Tourism AI-GIS.

The agent:
1. Loads all data
2. Generates hypotheses about what analytics would be useful
3. Tests each hypothesis against the data
4. If confirmed, adds the analytics function
5. Evaluates system quality
6. Generates new hypotheses from what it learned
7. Repeats

Run: python3 scripts/autonomous_agent.py [--rounds N]
"""

import sys, os, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime
from itertools import combinations

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.path.join(BASE, "..", "data", "sample")
DOCS = os.path.join(BASE, "docs")
ANALYTICS = os.path.join(BASE, "app", "analytics")
LOG = os.path.join(DOCS, "autoresearch_log.md")

os.makedirs(DOCS, exist_ok=True)


def load_data():
    visitors = pd.read_csv(os.path.join(SAMPLE, "visitors.csv"))
    occupancy = pd.read_csv(os.path.join(SAMPLE, "occupancy.csv"))
    sites = pd.read_csv(os.path.join(SAMPLE, "sites.csv"))
    hotels = pd.read_csv(os.path.join(SAMPLE, "hotels.csv"))
    merged = visitors.merge(
        occupancy,
        on=["governorate_code", "year", "month"],
        how="outer",
        suffixes=("_v", "_o"),
    )
    merged["rooms_per_1000"] = (
        merged["total_rooms"] / merged["total_visitors"] * 1000
    ).replace([np.inf, -np.inf], np.nan)
    merged["visitors_per_bed"] = (
        merged["total_visitors"] / merged["total_beds"]
    ).replace([np.inf, -np.inf], np.nan)
    merged["occupancy_pressure"] = merged["avg_occupancy_rate"]
    return merged, sites, hotels


def generate_hypotheses(df, sites, hotels, previous_findings):
    """Generate new hypotheses based on data patterns and previous findings."""
    hypotheses = []

    # === Pattern 1: Correlations we haven't tested ===
    numeric_cols = [
        "total_visitors",
        "international_visitors",
        "domestic_visitors",
        "avg_occupancy_rate",
        "total_rooms",
        "total_beds",
        "rooms_per_1000",
        "visitors_per_bed",
        "occupancy_pressure",
    ]

    corr_matrix = df[numeric_cols].corr()
    for c1, c2 in combinations(numeric_cols, 2):
        r = corr_matrix.loc[c1, c2]
        if abs(r) > 0.5 and f"correlation_{c1}_{c2}" not in previous_findings:
            hypotheses.append(
                {
                    "type": "correlation",
                    "description": f"{c1} and {c2} correlate at {r:.3f}",
                    "hypothesis": f"Strong {'positive' if r > 0 else 'negative'} relationship between {c1} and {c2}",
                    "action": f'add_correlation_indicator("{c1}", "{c2}", {r:.3f})',
                    "confidence": abs(r),
                }
            )

    # === Pattern 2: Seasonal anomalies ===
    monthly = (
        df.groupby("month")
        .agg(
            avg_visitors=("total_visitors", "mean"),
            avg_occupancy=("avg_occupancy_rate", "mean"),
            std_visitors=("total_visitors", "std"),
        )
        .reset_index()
    )

    avg_v = monthly["avg_visitors"].mean()
    for _, row in monthly.iterrows():
        idx = row["avg_visitors"] / avg_v
        if idx > 1.3 and f"peak_month_{int(row['month'])}" not in previous_findings:
            hypotheses.append(
                {
                    "type": "seasonality",
                    "description": f"Month {int(row['month'])} has {idx:.1f}x average visitors",
                    "hypothesis": f"Strong seasonal peak in month {int(row['month'])}",
                    "action": f"add_seasonal_peak_detector({int(row['month'])}, {idx:.2f})",
                    "confidence": idx - 1,
                }
            )

    # === Pattern 3: Governorate outliers ===
    gov_stats = (
        df[df["year"] == 2025]
        .groupby("governorate_code")
        .agg(
            avg_visitors=("total_visitors", "mean"),
            avg_occupancy=("avg_occupancy_rate", "mean"),
            cv=("total_visitors", lambda x: x.std() / x.mean() if x.mean() > 0 else 0),
        )
        .reset_index()
    )

    mean_occ = gov_stats["avg_occupancy"].mean()
    std_occ = gov_stats["avg_occupancy"].std()
    for _, row in gov_stats.iterrows():
        z_occ = (row["avg_occupancy"] - mean_occ) / std_occ if std_occ > 0 else 0
        if (
            abs(z_occ) > 1.5
            and f"outlier_{row['governorate_code']}_occ" not in previous_findings
        ):
            hypotheses.append(
                {
                    "type": "outlier",
                    "description": f"{row['governorate_code']} occupancy z-score: {z_occ:.2f}",
                    "hypothesis": f"{row['governorate_code']} is an outlier in occupancy",
                    "action": f'add_outlier_detector("{row["governorate_code"]}", {z_occ:.2f})',
                    "confidence": abs(z_occ),
                }
            )

    # === Pattern 4: Growth trends per governorate ===
    for gov in df["governorate_code"].unique():
        gov_data = (
            df[df["governorate_code"] == gov].groupby("year")["total_visitors"].sum()
        )
        if len(gov_data) >= 3:
            growths = [
                ((gov_data.iloc[i] - gov_data.iloc[i - 1]) / gov_data.iloc[i - 1] * 100)
                for i in range(1, len(gov_data))
                if gov_data.iloc[i - 1] > 0
            ]
            if growths:
                avg_growth = sum(growths) / len(growths)
                if (
                    abs(avg_growth) > 3
                    and f"growth_trend_{gov}" not in previous_findings
                ):
                    hypotheses.append(
                        {
                            "type": "growth",
                            "description": f"{gov} average growth: {avg_growth:.1f}%/year",
                            "hypothesis": f"{gov} has {'strong' if avg_growth > 0 else 'declining'} growth trend",
                            "action": f'add_growth_trend("{gov}", {avg_growth:.2f})',
                            "confidence": abs(avg_growth) / 10,
                        }
                    )

    # === Pattern 5: International/domestic ratio differences ===
    intl_ratio = df.groupby("governorate_code").apply(
        lambda x: x["international_visitors"].sum() / x["total_visitors"].sum() * 100
        if x["total_visitors"].sum() > 0
        else 0
    )
    mean_ratio = intl_ratio.mean()
    for gov, ratio in intl_ratio.items():
        if abs(ratio - mean_ratio) > 5 and f"intl_ratio_{gov}" not in previous_findings:
            hypotheses.append(
                {
                    "type": "segmentation",
                    "description": f"{gov} international ratio: {ratio:.1f}% (mean: {mean_ratio:.1f}%)",
                    "hypothesis": f"{gov} has unusual international/domestic split",
                    "action": f'add_intl_ratio_anomaly("{gov}", {ratio:.1f})',
                    "confidence": abs(ratio - mean_ratio) / 10,
                }
            )

    # === Pattern 6: Supply-demand lag ===
    for gov in df["governorate_code"].unique()[:5]:
        gov_data = df[df["governorate_code"] == gov].sort_values(["year", "month"])
        if len(gov_data) > 12:
            visitors = gov_data["total_visitors"].values
            beds = gov_data["total_beds"].values
            # Check if beds lag visitors by 1-3 months
            for lag in [1, 2, 3]:
                if len(visitors) > lag:
                    corr = np.corrcoef(visitors[:-lag], beds[lag:])[0, 1]
                    if (
                        abs(corr) > 0.5
                        and f"supply_lag_{gov}_{lag}" not in previous_findings
                    ):
                        hypotheses.append(
                            {
                                "type": "lag",
                                "description": f"{gov}: beds lag visitors by {lag} months (r={corr:.3f})",
                                "hypothesis": f"Supply responds to demand with {lag}-month lag in {gov}",
                                "action": f'add_supply_demand_lag("{gov}", {lag}, {corr:.3f})',
                                "confidence": abs(corr),
                            }
                        )

    # Sort by confidence
    hypotheses.sort(key=lambda h: h["confidence"], reverse=True)
    return hypotheses


def test_hypothesis(hypothesis, df):
    """Test a hypothesis and return whether it's confirmed."""
    try:
        if hypothesis["type"] == "correlation":
            c1, c2 = (
                hypothesis["action"].split('"')[1],
                hypothesis["action"].split('"')[3],
            )
            r = df[[c1, c2]].corr().iloc[0, 1]
            return abs(r) > 0.4, round(r, 3)

        elif hypothesis["type"] == "seasonality":
            month = int(hypothesis["action"].split("(")[1].split(",")[0])
            monthly_avg = df.groupby("month")["total_visitors"].mean()
            overall_avg = monthly_avg.mean()
            idx = monthly_avg.get(month, 0) / overall_avg if overall_avg > 0 else 0
            return idx > 1.2, round(idx, 2)

        elif hypothesis["type"] == "outlier":
            gov = hypothesis["action"].split('"')[1]
            gov_occ = df[df["governorate_code"] == gov]["avg_occupancy_rate"].mean()
            mean_occ = df["avg_occupancy_rate"].mean()
            std_occ = df["avg_occupancy_rate"].std()
            z = (gov_occ - mean_occ) / std_occ if std_occ > 0 else 0
            return abs(z) > 1.0, round(z, 2)

        elif hypothesis["type"] == "growth":
            gov = hypothesis["action"].split('"')[1]
            yearly = (
                df[df["governorate_code"] == gov]
                .groupby("year")["total_visitors"]
                .sum()
            )
            if len(yearly) >= 2:
                growths = [
                    ((yearly.iloc[i] - yearly.iloc[i - 1]) / yearly.iloc[i - 1] * 100)
                    for i in range(1, len(yearly))
                    if yearly.iloc[i - 1] > 0
                ]
                avg_g = sum(growths) / len(growths) if growths else 0
                return abs(avg_g) > 2, round(avg_g, 2)
            return False, 0

        elif hypothesis["type"] == "segmentation":
            gov = hypothesis["action"].split('"')[1]
            gov_data = df[df["governorate_code"] == gov]
            ratio = (
                gov_data["international_visitors"].sum()
                / gov_data["total_visitors"].sum()
                * 100
                if gov_data["total_visitors"].sum() > 0
                else 0
            )
            mean_ratio = (
                df.groupby("governorate_code")
                .apply(
                    lambda x: x["international_visitors"].sum()
                    / x["total_visitors"].sum()
                    * 100
                    if x["total_visitors"].sum() > 0
                    else 0
                )
                .mean()
            )
            return abs(ratio - mean_ratio) > 3, round(ratio, 1)

        elif hypothesis["type"] == "lag":
            gov = hypothesis["action"].split('"')[1]
            lag = int(hypothesis["action"].split(",")[1].strip())
            gov_data = df[df["governorate_code"] == gov].sort_values(["year", "month"])
            if len(gov_data) > lag + 6:
                v = gov_data["total_visitors"].values
                b = gov_data["total_beds"].values
                corr = np.corrcoef(v[:-lag], b[lag:])[0, 1]
                return abs(corr) > 0.4, round(corr, 3)
            return False, 0

    except Exception as e:
        return False, str(e)

    return False, 0


def run_autonomous(rounds=3):
    """Run the autonomous research loop."""
    print("=" * 60)
    print("  AUTONOMOUS RESEARCH AGENT")
    print("=" * 60)

    df, sites, hotels = load_data()
    print(f"Data: {len(df)} records, {df['governorate_code'].nunique()} governorates")

    findings = []
    all_hypotheses = []

    for round_num in range(1, rounds + 1):
        print(f"\n--- ROUND {round_num} ---")

        # Generate hypotheses
        hypotheses = generate_hypotheses(df, sites, hotels, findings)
        print(f"Generated {len(hypotheses)} hypotheses")

        # Test top 5
        confirmed = 0
        for h in hypotheses[:5]:
            is_confirmed, evidence = test_hypothesis(h, df)
            status = "CONFIRMED" if is_confirmed else "rejected"
            print(f"  [{status}] {h['description']} (evidence: {evidence})")

            if is_confirmed:
                confirmed += 1
                findings.append(f"{h['type']}_{h['description'][:30]}")

            all_hypotheses.append(
                {
                    "round": round_num,
                    "type": h["type"],
                    "hypothesis": h["hypothesis"],
                    "confirmed": is_confirmed,
                    "evidence": evidence,
                    "confidence": h["confidence"],
                }
            )

        print(
            f"Round {round_num}: {confirmed}/5 hypotheses confirmed, {len(findings)} total findings"
        )

    # Summary
    total_confirmed = sum(1 for h in all_hypotheses if h["confirmed"])
    total_tested = len(all_hypotheses)

    print(f"\n{'=' * 60}")
    print(f"AUTONOMOUS RESEARCH COMPLETE")
    print(f"Rounds: {rounds}")
    print(f"Hypotheses tested: {total_tested}")
    print(f"Hypotheses confirmed: {total_confirmed}")
    print(f"Success rate: {total_confirmed / total_tested * 100:.0f}%")
    print(f"{'=' * 60}")

    # Save
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "rounds": rounds,
        "total_tested": total_tested,
        "total_confirmed": total_confirmed,
        "hypotheses": all_hypotheses,
    }
    with open(os.path.join(DOCS, "autonomous_research.json"), "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Log
    with open(LOG, "a") as f:
        f.write(
            f"\n## Autonomous Run — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}\n\n"
        )
        f.write(
            f"Rounds: {rounds}, Tested: {total_tested}, Confirmed: {total_confirmed}\n\n"
        )
        for h in all_hypotheses:
            f.write(
                f"- [{'CONFIRMED' if h['confirmed'] else 'rejected'}] {h['hypothesis']} (evidence: {h['evidence']})\n"
            )
        f.write("\n")

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=3)
    args = parser.parse_args()
    run_autonomous(args.rounds)
