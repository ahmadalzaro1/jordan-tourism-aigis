"""
Actionable Layer for Jordan Tourism AI-GIS.

Inspired by Palantir's Ontology + Actions pattern:
- Objects: tourism sites, hotels, governorates, incidents, investments
- Actions: things users can DO with objects
- Functions: business logic that computes on objects
- Rules: automated triggers and alerts

This module turns the dashboard from "view data" into "take action".
"""

# ==========================================
# OBJECT TYPES (Palantir Ontology pattern)
# ==========================================

OBJECT_TYPES = {
    "TourismSite": {
        "description": "A tourism site (archaeological, natural, religious, etc.)",
        "properties": [
            "name",
            "type",
            "governorate",
            "coordinates",
            "status",
            "visitor_count",
        ],
        "actions": ["report_issue", "update_info", "view_forecast"],
    },
    "Hotel": {
        "description": "An accommodation establishment",
        "properties": ["name", "class", "rooms", "beds", "occupancy", "governorate"],
        "actions": ["report_issue", "update_capacity", "view_performance"],
    },
    "Governorate": {
        "description": "An administrative region",
        "properties": [
            "name",
            "visitors",
            "occupancy",
            "classification",
            "accessibility",
        ],
        "actions": ["view_deep_dive", "run_simulation", "propose_investment"],
    },
    "Incident": {
        "description": "A reported tourism issue (from citizen reports or MoTA staff)",
        "properties": [
            "title",
            "type",
            "location",
            "severity",
            "status",
            "reported_by",
            "assigned_to",
        ],
        "actions": ["assign", "resolve", "escalate", "add_photo"],
    },
    "Investment": {
        "description": "A proposed tourism infrastructure investment",
        "properties": [
            "governorate",
            "type",
            "cost",
            "priority_score",
            "status",
            "justification",
        ],
        "actions": ["propose", "review", "approve", "reject", "implement"],
    },
    "ConflictEvent": {
        "description": "A regional conflict or crisis affecting tourism",
        "properties": ["name", "severity", "region", "date", "impact_estimate"],
        "actions": ["trigger_alert", "update_severity", "log_impact"],
    },
    "Forecast": {
        "description": "A demand forecast for a governorate",
        "properties": ["governorate", "horizon", "method", "mape", "predictions"],
        "actions": ["run_forecast", "compare_scenarios", "export_report"],
    },
}

# ==========================================
# ACTIONS (things users can DO)
# ==========================================

ACTIONS = {
    # Citizen/MoTA staff can report issues
    "report_issue": {
        "name": "Report Issue",
        "description": "Report a tourism issue with photo and location",
        "parameters": {
            "title": {"type": "string", "required": True},
            "description": {"type": "text", "required": True},
            "type": {
                "type": "select",
                "options": [
                    "infrastructure",
                    "safety",
                    "cleanliness",
                    "overcrowding",
                    "accessibility",
                    "other",
                ],
            },
            "location": {"type": "geojson", "required": True},
            "photo": {"type": "file", "required": False},
            "severity": {
                "type": "select",
                "options": ["low", "medium", "high", "critical"],
            },
        },
        "creates": "Incident",
        "triggers": ["notify_regional_office", "update_heatmap"],
    },
    # MoTA can assign issues to regional offices
    "assign_issue": {
        "name": "Assign Issue",
        "description": "Assign an incident to a regional office for resolution",
        "parameters": {
            "incident_id": {"type": "reference", "object_type": "Incident"},
            "assigned_to": {
                "type": "select",
                "options": [
                    "amman_office",
                    "aqaba_office",
                    "petra_office",
                    "karak_office",
                ],
            },
            "deadline": {"type": "date"},
            "notes": {"type": "text"},
        },
        "updates": "Incident.assigned_to",
        "triggers": ["notify_assignee"],
    },
    # MoTA can resolve issues
    "resolve_issue": {
        "name": "Resolve Issue",
        "description": "Mark an incident as resolved with resolution notes",
        "parameters": {
            "incident_id": {"type": "reference", "object_type": "Incident"},
            "resolution": {"type": "text", "required": True},
            "resolution_photo": {"type": "file"},
            "cost": {"type": "number"},
        },
        "updates": "Incident.status = resolved",
        "triggers": ["update_stats", "notify_reporter"],
    },
    # MoTA can propose investments
    "propose_investment": {
        "name": "Propose Investment",
        "description": "Propose a tourism infrastructure investment based on analytics",
        "parameters": {
            "governorate_id": {"type": "reference", "object_type": "Governorate"},
            "investment_type": {
                "type": "select",
                "options": [
                    "new_hotel_4star",
                    "hotel_expansion",
                    "eco_lodge",
                    "guest_house",
                    "road_improvement",
                    "site_restoration",
                    "campsite_upgrade",
                ],
            },
            "estimated_cost": {"type": "number", "required": True},
            "justification": {"type": "text", "required": True},
            "priority_score": {"type": "number", "computed": True},
        },
        "creates": "Investment",
        "triggers": ["notify_committee"],
    },
    # Committee can approve/reject investments
    "approve_investment": {
        "name": "Approve Investment",
        "description": "Approve a proposed investment for implementation",
        "parameters": {
            "investment_id": {"type": "reference", "object_type": "Investment"},
            "approved_budget": {"type": "number", "required": True},
            "implementation_timeline": {"type": "text"},
            "conditions": {"type": "text"},
        },
        "updates": "Investment.status = approved",
        "triggers": ["create_implementation_task", "update_budget_tracker"],
    },
    # Run forecast for a governorate
    "run_forecast": {
        "name": "Run Forecast",
        "description": "Generate a demand forecast for a governorate",
        "parameters": {
            "governorate_id": {"type": "reference", "object_type": "Governorate"},
            "horizon_months": {"type": "select", "options": [6, 12, 24]},
            "method": {"type": "select", "options": ["prophet", "arima", "auto"]},
        },
        "creates": "Forecast",
        "triggers": ["update_dashboard", "check_alerts"],
    },
    # Run what-if simulation
    "run_simulation": {
        "name": "Run Simulation",
        "description": "Run a what-if scenario for infrastructure planning",
        "parameters": {
            "governorate_id": {"type": "reference", "object_type": "Governorate"},
            "scenario_type": {"type": "select", "options": ["accommodation", "demand"]},
            "added_beds": {"type": "number"},
            "visitor_change_pct": {"type": "number"},
        },
        "creates": "Forecast",
        "triggers": ["update_comparison"],
    },
    # Trigger conflict alert
    "trigger_conflict_alert": {
        "name": "Trigger Conflict Alert",
        "description": "Alert MoTA about a regional conflict affecting tourism",
        "parameters": {
            "conflict_name": {"type": "string", "required": True},
            "severity": {
                "type": "select",
                "options": ["low", "medium", "high", "critical"],
            },
            "affected_markets": {
                "type": "multiselect",
                "options": [
                    "USA",
                    "UK",
                    "Germany",
                    "France",
                    "Palestine",
                    "Saudi Arabia",
                ],
            },
            "estimated_impact": {"type": "text"},
        },
        "creates": "ConflictEvent",
        "triggers": ["notify_mota", "update_dashboard", "adjust_forecast"],
    },
    # Update hotel capacity
    "update_capacity": {
        "name": "Update Capacity",
        "description": "Update hotel rooms/beds (when new hotel opens or expands)",
        "parameters": {
            "hotel_id": {"type": "reference", "object_type": "Hotel"},
            "new_rooms": {"type": "number"},
            "new_beds": {"type": "number"},
            "effective_date": {"type": "date"},
        },
        "updates": "Hotel.rooms, Hotel.beds",
        "triggers": ["recalculate_indicators", "update_forecast"],
    },
    # Monthly data update
    "upload_monthly_data": {
        "name": "Upload Monthly Data",
        "description": "MoTA analyst uploads monthly tourism statistics",
        "parameters": {
            "data_type": {
                "type": "select",
                "options": ["visitors", "occupancy", "site_visits"],
            },
            "csv_file": {"type": "file", "required": True},
            "month": {"type": "select", "options": list(range(1, 13))},
            "year": {"type": "number", "required": True},
        },
        "triggers": [
            "run_etl",
            "recalculate_indicators",
            "update_dashboard",
            "send_confirmation",
        ],
    },
}

# ==========================================
# RULES (automated triggers)
# ==========================================

RULES = {
    "capacity_alert": {
        "name": "Capacity Alert",
        "description": "Alert when a governorate exceeds 80% occupancy",
        "condition": "governorate.avg_occupancy > 80",
        "action": "notify_mota",
        "severity": "high",
    },
    "conflict_impact_alert": {
        "name": "Conflict Impact Alert",
        "description": "Alert when a new conflict event is logged",
        "condition": "ConflictEvent.created",
        "action": "update_forecast + notify_mota",
        "severity": "critical",
    },
    "monthly_data_reminder": {
        "name": "Monthly Data Reminder",
        "description": "Remind MoTA to upload monthly data",
        "condition": "day_of_month == 15 AND last_upload > 30_days",
        "action": "send_reminder",
        "severity": "medium",
    },
    "forecast_accuracy_alert": {
        "name": "Forecast Accuracy Alert",
        "description": "Alert when forecast error exceeds threshold",
        "condition": "forecast.mape > 25",
        "action": "notify_analyst",
        "severity": "medium",
    },
    "investment_imbalance": {
        "name": "Investment Imbalance Alert",
        "description": "Alert when investments are concentrated in one governorate",
        "condition": "max(governorate.investment_share) > 50%",
        "action": "notify_committee",
        "severity": "low",
    },
}

# ==========================================
# WORKFLOW STATES
# ==========================================

WORKFLOWS = {
    "incident": {
        "states": [
            "reported",
            "acknowledged",
            "assigned",
            "in_progress",
            "resolved",
            "closed",
        ],
        "transitions": {
            "reported": ["acknowledged"],
            "acknowledged": ["assigned"],
            "assigned": ["in_progress"],
            "in_progress": ["resolved"],
            "resolved": ["closed"],
        },
    },
    "investment": {
        "states": [
            "proposed",
            "under_review",
            "approved",
            "rejected",
            "implementing",
            "completed",
        ],
        "transitions": {
            "proposed": ["under_review"],
            "under_review": ["approved", "rejected"],
            "approved": ["implementing"],
            "implementing": ["completed"],
            "rejected": ["proposed"],  # Can re-propose
        },
    },
    "data_update": {
        "states": [
            "uploaded",
            "validating",
            "validated",
            "importing",
            "imported",
            "error",
        ],
        "transitions": {
            "uploaded": ["validating"],
            "validating": ["validated", "error"],
            "validated": ["importing"],
            "importing": ["imported", "error"],
            "error": ["uploaded"],  # Re-upload
        },
    },
}
