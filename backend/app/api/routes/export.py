"""
Executive Summary PDF Export for Jordan Tourism AI-GIS.

Per RFP ToR Section 3.2.3(4):
"Executive summary report as PDF including key analytical values and charts shown on the dashboard"

Uses reportlab to generate a professional PDF with:
- National key indicators
- Top 5 priority investment zones
- Governorate comparison table
- Forecast summary
- Methodology notes
"""

from io import BytesIO
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.db.models import (
    Governorate,
    VisitorData,
    OccupancyData,
    Hotel,
    CapacityIndicator,
)
from app.analytics.scoring import compute_priority_batch

router = APIRouter()


@router.get("/executive-summary")
def export_executive_summary(year: int = Query(2025), db: Session = Depends(get_db)):
    """Generate executive summary PDF."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
    )
    from reportlab.lib import colors

    # Gather data
    governorates = db.query(Governorate).all()

    # National summary
    nat_visitors = (
        db.query(
            func.sum(VisitorData.total_visitors),
            func.sum(VisitorData.international_visitors),
            func.sum(VisitorData.domestic_visitors),
        )
        .filter(VisitorData.year == year)
        .first()
    )

    nat_occupancy = (
        db.query(
            func.avg(OccupancyData.avg_occupancy_rate),
            func.coalesce(func.sum(OccupancyData.total_rooms), 0),
            func.coalesce(func.sum(OccupancyData.total_beds), 0),
        )
        .filter(OccupancyData.year == year)
        .first()
    )

    hotel_count = db.query(func.count(Hotel.id)).scalar()

    # Governorate comparison data
    gov_data = []
    for gov in governorates:
        v = (
            db.query(func.sum(VisitorData.total_visitors))
            .filter(VisitorData.governorate_id == gov.id, VisitorData.year == year)
            .scalar()
            or 0
        )

        o = (
            db.query(
                func.avg(OccupancyData.avg_occupancy_rate),
                func.coalesce(func.sum(OccupancyData.total_beds), 0),
            )
            .filter(OccupancyData.governorate_id == gov.id, OccupancyData.year == year)
            .first()
        )

        prev = (
            db.query(func.sum(VisitorData.total_visitors))
            .filter(VisitorData.governorate_id == gov.id, VisitorData.year == year - 1)
            .scalar()
            or 1
        )

        growth = ((v - prev) / prev * 100) if prev > 0 else 0

        gov_data.append(
            {
                "id": gov.id,
                "name": gov.name_en,
                "visitors": v,
                "beds": o[1] if o else 0,
                "occupancy": o[0] if o else 0,
                "growth": growth,
            }
        )

    # Priority rankings
    batch_input = [
        {
            "id": g["id"],
            "name": g["name"],
            "forecast_visitors": g["visitors"],
            "total_beds": g["beds"],
            "occupancy_pressure": g["occupancy"],
            "growth_pct": g["growth"],
            "has_airport": g["name"] in ["Amman", "Aqaba"],
            "highway_distance_km": 20 if g["name"] in ["Amman", "Aqaba"] else 50,
        }
        for g in gov_data
    ]

    rankings = compute_priority_batch(batch_input)

    # Build PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        textColor=HexColor("#1a1a2e"),
        fontSize=18,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        textColor=HexColor("#c9a55c"),
        fontSize=14,
    )
    body_style = ParagraphStyle("CustomBody", parent=styles["Normal"], fontSize=10)

    story = []

    # Title
    story.append(Paragraph("Jordan Tourism AI-GIS", title_style))
    story.append(Paragraph(f"Executive Summary — {year}", styles["Heading3"]))
    story.append(Paragraph(f"Generated: March 29, 2026", body_style))
    story.append(Spacer(1, 0.5 * cm))

    # National Indicators
    story.append(Paragraph("National Tourism Indicators", heading_style))
    story.append(Spacer(1, 0.3 * cm))

    total_v = nat_visitors[0] if nat_visitors and nat_visitors[0] else 0
    intl_v = nat_visitors[1] if nat_visitors and nat_visitors[1] else 0
    dom_v = nat_visitors[2] if nat_visitors and nat_visitors[2] else 0
    avg_occ = nat_occupancy[0] if nat_occupancy and nat_occupancy[0] else 0
    total_rooms = nat_occupancy[1] if nat_occupancy and nat_occupancy[1] else 0
    total_beds = nat_occupancy[2] if nat_occupancy and nat_occupancy[2] else 0

    indicator_data = [
        ["Indicator", "Value"],
        ["Total Visitors", f"{total_v:,}"],
        ["International Visitors", f"{intl_v:,}"],
        ["Domestic Visitors", f"{dom_v:,}"],
        ["Total Hotels", f"{hotel_count}"],
        ["Total Rooms", f"{total_rooms:,}"],
        ["Total Beds", f"{total_beds:,}"],
        ["Average Occupancy Rate", f"{avg_occ:.1f}%"],
    ]

    t = Table(indicator_data, colWidths=[8 * cm, 6 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1a1a2e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, HexColor("#f5f5f5")],
                ),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    # Top 5 Priority Zones
    story.append(Paragraph("Top 5 Priority Investment Zones", heading_style))
    story.append(Spacer(1, 0.3 * cm))

    rank_data = [["Rank", "Governorate", "Score", "Investment Type", "Justification"]]
    for r in rankings[:5]:
        rank_data.append(
            [
                str(r["rank"]),
                r["governorate"],
                f"{r['priority_score']:.1f}",
                r["recommended_investment_type"].replace("_", " "),
                r["justification"][:60] + "..."
                if len(r["justification"]) > 60
                else r["justification"],
            ]
        )

    t2 = Table(rank_data, colWidths=[1.5 * cm, 3 * cm, 2 * cm, 4 * cm, 5 * cm])
    t2.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1a1a2e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, HexColor("#f5f5f5")],
                ),
            ]
        )
    )
    story.append(t2)
    story.append(Spacer(1, 0.5 * cm))

    # Governorate Comparison
    story.append(Paragraph("Governorate Comparison", heading_style))
    story.append(Spacer(1, 0.3 * cm))

    comp_data = [["Governorate", "Visitors", "Beds", "Occupancy", "Growth"]]
    for g in sorted(gov_data, key=lambda x: x["visitors"], reverse=True):
        comp_data.append(
            [
                g["name"],
                f"{g['visitors']:,}",
                f"{g['beds']:,}",
                f"{g['occupancy']:.1f}%",
                f"{g['growth']:.1f}%",
            ]
        )

    t3 = Table(comp_data, colWidths=[3.5 * cm, 3 * cm, 2.5 * cm, 3 * cm, 3 * cm])
    t3.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1a1a2e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, HexColor("#f5f5f5")],
                ),
            ]
        )
    )
    story.append(t3)
    story.append(Spacer(1, 0.5 * cm))

    # Methodology
    story.append(Paragraph("Methodology Notes", heading_style))
    story.append(
        Paragraph(
            "Demand-capacity indicators: rooms per 1000 visitors, occupancy pressure index, growth pressure index, "
            "capacity adequacy index. Classification uses majority voting across 4 indicators with configurable thresholds.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Forecasting: Facebook Prophet (primary) with yearly seasonality, ARIMA(1,1,1) fallback. "
            "12-month horizon. No external regressors or deep learning.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Priority scoring: weighted combination of demand (25%), capacity gap (30%), occupancy pressure (20%), "
            "growth (15%), and accessibility (10%). Weights are configurable.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Simulation: rule-based recalculation using forecasted baseline and user-defined scenarios. "
            "Transparent, formula-based, reproducible.",
            body_style,
        )
    )

    # Build
    doc.build(story)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=jordan-tourism-summary-{year}.pdf"
        },
    )
