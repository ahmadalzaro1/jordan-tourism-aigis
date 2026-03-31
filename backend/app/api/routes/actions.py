"""
Actions API — Palantir-style actionable layer.

Turns the dashboard from "view data" into "take action".
Every endpoint corresponds to a Palantir Action Type.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.db.models import Incident, Investment, ConflictEvent, Governorate

router = APIRouter()


# ==========================================
# INCIDENT ACTIONS
# ==========================================


@router.post("/incidents/report")
def report_incident(
    title: str = Query(...),
    description: str = Query(""),
    incident_type: str = Query("other"),
    severity: str = Query("medium"),
    governorate_id: int = Query(None),
    latitude: float = Query(None),
    longitude: float = Query(None),
    reported_by: str = Query("citizen"),
    db: Session = Depends(get_db),
):
    """Report a tourism issue with location. Creates an Incident object."""
    incident = Incident(
        title=title,
        description=description,
        incident_type=incident_type,
        severity=severity,
        governorate_id=governorate_id,
        latitude=latitude,
        longitude=longitude,
        reported_by=reported_by,
        status="reported",
        created_at=datetime.utcnow().isoformat(),
    )
    db.add(incident)
    db.commit()
    return {
        "status": "created",
        "incident_id": incident.id,
        "workflow": "reported → acknowledged → assigned → resolved",
    }


@router.post("/incidents/{incident_id}/assign")
def assign_incident(
    incident_id: int,
    assigned_to: str = Query(...),
    deadline: str = Query(None),
    notes: str = Query(""),
    db: Session = Depends(get_db),
):
    """Assign an incident to a regional office."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(404, "Incident not found")
    incident.assigned_to = assigned_to
    incident.status = "assigned"
    incident.updated_at = datetime.utcnow().isoformat()
    db.commit()
    return {"status": "assigned", "assigned_to": assigned_to}


@router.post("/incidents/{incident_id}/resolve")
def resolve_incident(
    incident_id: int,
    resolution: str = Query(...),
    resolution_cost: float = Query(None),
    db: Session = Depends(get_db),
):
    """Mark an incident as resolved."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(404, "Incident not found")
    incident.resolution = resolution
    incident.resolution_cost = resolution_cost
    incident.status = "resolved"
    incident.updated_at = datetime.utcnow().isoformat()
    db.commit()
    return {"status": "resolved"}


@router.get("/incidents")
def list_incidents(
    status: str = Query(None),
    governorate_id: int = Query(None),
    severity: str = Query(None),
    db: Session = Depends(get_db),
):
    """List incidents with filters."""
    q = db.query(Incident)
    if status:
        q = q.filter(Incident.status == status)
    if governorate_id:
        q = q.filter(Incident.governorate_id == governorate_id)
    if severity:
        q = q.filter(Incident.severity == severity)
    incidents = q.order_by(Incident.created_at.desc()).limit(100).all()
    return [
        {
            "id": i.id,
            "title": i.title,
            "type": i.incident_type,
            "severity": i.severity,
            "status": i.status,
            "governorate_id": i.governorate_id,
            "assigned_to": i.assigned_to,
            "latitude": i.latitude,
            "longitude": i.longitude,
            "created_at": i.created_at,
        }
        for i in incidents
    ]


# ==========================================
# INVESTMENT ACTIONS
# ==========================================


@router.post("/investments/propose")
def propose_investment(
    governorate_id: int = Query(...),
    investment_type: str = Query(...),
    estimated_cost: float = Query(...),
    justification: str = Query(""),
    proposed_by: str = Query("analyst"),
    db: Session = Depends(get_db),
):
    """Propose a tourism infrastructure investment."""
    # Auto-compute priority score from analytics
    from app.analytics.scoring import compute_priority_score

    gov = db.query(Governorate).filter(Governorate.id == governorate_id).first()
    if not gov:
        raise HTTPException(404, "Governorate not found")

    investment = Investment(
        governorate_id=governorate_id,
        investment_type=investment_type,
        estimated_cost=estimated_cost,
        justification=justification,
        proposed_by=proposed_by,
        status="proposed",
        created_at=datetime.utcnow().isoformat(),
    )
    db.add(investment)
    db.commit()
    return {
        "status": "proposed",
        "investment_id": investment.id,
        "workflow": "proposed → under_review → approved/rejected → implementing → completed",
    }


@router.post("/investments/{investment_id}/approve")
def approve_investment(
    investment_id: int,
    approved_budget: float = Query(...),
    implementation_timeline: str = Query(""),
    conditions: str = Query(""),
    reviewed_by: str = Query("committee"),
    db: Session = Depends(get_db),
):
    """Approve a proposed investment."""
    inv = db.query(Investment).filter(Investment.id == investment_id).first()
    if not inv:
        raise HTTPException(404, "Investment not found")
    inv.approved_budget = approved_budget
    inv.implementation_timeline = implementation_timeline
    inv.conditions = conditions
    inv.reviewed_by = reviewed_by
    inv.status = "approved"
    inv.updated_at = datetime.utcnow().isoformat()
    db.commit()
    return {"status": "approved", "budget": approved_budget}


@router.post("/investments/{investment_id}/reject")
def reject_investment(
    investment_id: int,
    reason: str = Query(""),
    db: Session = Depends(get_db),
):
    """Reject a proposed investment."""
    inv = db.query(Investment).filter(Investment.id == investment_id).first()
    if not inv:
        raise HTTPException(404, "Investment not found")
    inv.status = "rejected"
    inv.conditions = reason
    inv.updated_at = datetime.utcnow().isoformat()
    db.commit()
    return {"status": "rejected"}


@router.get("/investments")
def list_investments(
    status: str = Query(None),
    governorate_id: int = Query(None),
    db: Session = Depends(get_db),
):
    """List investments with filters."""
    q = db.query(Investment)
    if status:
        q = q.filter(Investment.status == status)
    if governorate_id:
        q = q.filter(Investment.governorate_id == governorate_id)
    investments = q.order_by(Investment.created_at.desc()).limit(100).all()
    return [
        {
            "id": i.id,
            "governorate_id": i.governorate_id,
            "investment_type": i.investment_type,
            "estimated_cost": i.estimated_cost,
            "approved_budget": i.approved_budget,
            "status": i.status,
            "justification": i.justification,
            "priority_score": i.priority_score,
            "created_at": i.created_at,
        }
        for i in investments
    ]


# ==========================================
# CONFLICT ACTIONS
# ==========================================


@router.post("/conflicts/trigger")
def trigger_conflict_alert(
    conflict_name: str = Query(...),
    severity: str = Query("high"),
    affected_markets: str = Query(""),
    estimated_impact: str = Query(""),
    region: str = Query("Middle East"),
    db: Session = Depends(get_db),
):
    """Trigger a conflict alert affecting tourism."""
    event = ConflictEvent(
        name=conflict_name,
        severity=severity,
        region=region,
        affected_markets=affected_markets,
        estimated_impact=estimated_impact,
        status="active",
        created_at=datetime.utcnow().isoformat(),
    )
    db.add(event)
    db.commit()
    return {
        "status": "alert_created",
        "event_id": event.id,
        "triggers": ["notify_mota", "update_dashboard", "adjust_forecast"],
    }


@router.get("/conflicts")
def list_conflicts(
    status: str = Query("active"),
    db: Session = Depends(get_db),
):
    """List conflict events."""
    events = db.query(ConflictEvent).filter(ConflictEvent.status == status).all()
    return [
        {
            "id": e.id,
            "name": e.name,
            "severity": e.severity,
            "region": e.region,
            "affected_markets": e.affected_markets,
            "status": e.status,
            "created_at": e.created_at,
        }
        for e in events
    ]


# ==========================================
# ONTOLOGY ENDPOINT
# ==========================================


@router.get("/ontology")
def get_ontology():
    """Return the full ontology definition (Palantir-style)."""
    from app.actions.ontology import OBJECT_TYPES, ACTIONS, RULES, WORKFLOWS

    return {
        "object_types": OBJECT_TYPES,
        "actions": ACTIONS,
        "rules": RULES,
        "workflows": WORKFLOWS,
    }
