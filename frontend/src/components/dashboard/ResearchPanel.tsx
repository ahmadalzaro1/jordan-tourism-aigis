"use client";

import { useState, useEffect } from "react";
import { API_URL, THEME } from "@/lib/constants";

export default function ResearchPanel() {
  const [clusters, setClusters] = useState<any>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/analytics/clusters`)
      .then(r => r.json())
      .then(setClusters)
      .catch(console.error);
  }, []);

  const analyticsModules = [
    {
      name: "Indicators",
      count: 32,
      functions: [
        "rooms_per_1000", "beds_per_1000", "occupancy_pressure", "growth_pressure",
        "capacity_adequacy", "demand_elasticity", "peak_capacity_ratio",
        "visitor_concentration_hhi", "growth_acceleration", "tourism_dependency",
        "seasonal_cv", "capacity_utilization", "weather_adjusted", "ramadan_adjusted",
        "attention_ratio", "airport_conversion", "gdp_elasticity", "demand_concentration",
        "growth_leads_occupancy", "variance_decomposition", "seasonal_amplitude",
        "complementarity", "recovery_speed", "neighbor_spillover", "peak_concentration",
        "site_diversification", "oversaturation", "intl_leakage", "infrastructure_stress",
      ],
    },
    {
      name: "Scoring",
      count: 14,
      functions: [
        "priority_score", "demand_score", "capacity_gap", "occupancy_pressure_score",
        "growth_score", "accessibility_score", "investment_type", "justification",
        "conflict_resilience", "conflict_lag", "investment_roi", "investment_urgency",
      ],
    },
    {
      name: "Classification",
      count: 3,
      functions: ["classify_capacity", "classify_batch", "classify_seasonal"],
    },
    {
      name: "Forecasting",
      count: 4,
      functions: ["prepare_series", "forecast_prophet", "forecast_arima", "forecast_best"],
    },
    {
      name: "Simulation",
      count: 2,
      functions: ["accommodation_scenario", "demand_scenario"],
    },
    {
      name: "Data-Driven",
      count: 7,
      functions: ["dynamic_thresholds", "detect_seasonality", "data_completeness", "confidence", "rankings", "trends", "anomalies"],
    },
  ];

  const keyFindings = [
    { category: "Supply→Demand", finding: "Hotel rooms predict visitors (r=+0.812)", impact: "high" },
    { category: "Growth→Occupancy", finding: "ALL 12 governorates: growth predicts next month occupancy (r=0.63-0.82)", impact: "high" },
    { category: "Complementarity", finding: "Governorates complement (r=+0.82-0.90) — tourists visit multiple", impact: "high" },
    { category: "Forecast", finding: "Prophet achieves 4.89% MAPE (target: ≤20%)", impact: "high" },
    { category: "Accessibility", finding: "Amman extracts 7x more visitors/access-point than Zarqa", impact: "medium" },
    { category: "Tourism Dependency", finding: "Petra 41%, Aqaba 26% — extreme dependency", impact: "medium" },
    { category: "Recovery", finding: "Summer drops: 10 months. Winter drops: 3 months", impact: "medium" },
    { category: "Conflicts", finding: "43% of tourism is conflict-vulnerable", impact: "medium" },
    { category: "Seasonality", finding: "62-77% amplitude everywhere. Peak always April", impact: "medium" },
    { category: "Neighbor Spillover", finding: "Dead Sea→Amman (r=+0.546), Aqaba→Petra (r=+0.424)", impact: "medium" },
    { category: "Economic", finding: "GDP growth predicts next year tourism (r=+0.841)", impact: "medium" },
    { category: "Diversification", finding: "Aqaba most diverse (HHI=0.306), Petra least (0.867)", impact: "low" },
  ];

  const dataSources = [
    { name: "Tourism (MoTA)", records: "7,680", status: "sample" },
    { name: "OpenStreetMap", records: "15,224", status: "live" },
    { name: "Weather (Open-Meteo)", records: "936", status: "live" },
    { name: "Islamic Calendar", records: "108", status: "computed" },
    { name: "World Bank Economics", records: "7 indicators × 10yr", status: "live" },
    { name: "Wikipedia Views", records: "432", status: "live" },
    { name: "Airport Passengers", records: "72", status: "estimated" },
    { name: "Regional Conflicts", records: "21 events", status: "manual" },
    { name: "Source Markets", records: "12 markets", status: "manual" },
    { name: "Transport Network", records: "12 governorates", status: "computed" },
  ];

  return (
    <div style={{ padding: 20 }}>
      <h2 style={{ fontSize: 16, color: THEME.accent, margin: "0 0 16px 0", letterSpacing: "0.05em" }}>
        RESEARCH
      </h2>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 16 }}>
        {[
          { label: "Functions", value: "70" },
          { label: "Data Files", value: "55" },
          { label: "Findings", value: "100+" },
        ].map((stat) => (
          <div key={stat.label} style={{
            backgroundColor: THEME.surfaceAlt, border: `1px solid ${THEME.border}`,
            borderRadius: 8, padding: "10px 12px", textAlign: "center",
          }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: THEME.accent }}>{stat.value}</div>
            <div style={{ fontSize: 10, color: THEME.textMuted }}>{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Key Findings */}
      <div style={{ marginBottom: 16 }}>
        <h3 style={{ fontSize: 11, color: THEME.textMuted, textTransform: "uppercase", margin: "0 0 8px 0" }}>
          Key Findings
        </h3>
        {keyFindings.map((f, i) => (
          <div key={i} style={{
            backgroundColor: THEME.surfaceAlt, border: `1px solid ${THEME.border}`,
            borderRadius: 6, padding: "8px 10px", marginBottom: 4,
            display: "flex", alignItems: "center", gap: 8,
          }}>
            <span style={{
              width: 6, height: 6, borderRadius: "50%", flexShrink: 0,
              backgroundColor: f.impact === "high" ? "#ef4444" : f.impact === "medium" ? "#f59e0b" : "#22c55e",
            }} />
            <div>
              <span style={{ fontSize: 10, color: THEME.accent, fontWeight: 600 }}>{f.category}</span>
              <div style={{ fontSize: 11, color: THEME.text }}>{f.finding}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Analytics Modules */}
      <div style={{ marginBottom: 16 }}>
        <h3 style={{ fontSize: 11, color: THEME.textMuted, textTransform: "uppercase", margin: "0 0 8px 0" }}>
          Analytics Modules
        </h3>
        {analyticsModules.map((mod) => (
          <div key={mod.name} style={{
            backgroundColor: THEME.surfaceAlt, border: `1px solid ${THEME.border}`,
            borderRadius: 6, padding: "8px 10px", marginBottom: 4,
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: THEME.text }}>{mod.name}</span>
              <span style={{ fontSize: 11, color: THEME.accent }}>{mod.count} functions</span>
            </div>
            <div style={{ fontSize: 9, color: THEME.textMuted, lineHeight: 1.4 }}>
              {mod.functions.join(", ")}
            </div>
          </div>
        ))}
      </div>

      {/* Data Sources */}
      <div style={{ marginBottom: 16 }}>
        <h3 style={{ fontSize: 11, color: THEME.textMuted, textTransform: "uppercase", margin: "0 0 8px 0" }}>
          Data Sources
        </h3>
        {dataSources.map((ds) => (
          <div key={ds.name} style={{
            display: "flex", justifyContent: "space-between", padding: "4px 0",
            borderBottom: `1px solid ${THEME.border}`, fontSize: 11,
          }}>
            <span style={{ color: THEME.text }}>{ds.name}</span>
            <span style={{ color: THEME.textMuted }}>{ds.records}</span>
          </div>
        ))}
      </div>

      {/* Clusters */}
      {clusters?.clusters && (
        <div>
          <h3 style={{ fontSize: 11, color: THEME.textMuted, textTransform: "uppercase", margin: "0 0 8px 0" }}>
            Tourism Clusters
          </h3>
          {clusters.clusters.map((c: any) => (
            <div key={c.key} style={{
              backgroundColor: THEME.surfaceAlt, border: `1px solid ${THEME.border}`,
              borderRadius: 6, padding: "8px 10px", marginBottom: 4,
            }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: THEME.text }}>{c.name_en}</div>
              <div style={{ fontSize: 10, color: THEME.textMuted, marginTop: 2 }}>{c.name_ar}</div>
              <div style={{ fontSize: 10, color: THEME.textMuted, marginTop: 2 }}>{c.description.slice(0, 80)}...</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
