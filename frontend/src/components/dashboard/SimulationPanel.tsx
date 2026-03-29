"use client";

import { useState, useEffect } from "react";
import { API_URL, THEME } from "@/lib/constants";

interface SimulationPanelProps {
  governorateId: number | null;
  governorateName: string;
}

export default function SimulationPanel({ governorateId, governorateName }: SimulationPanelProps) {
  const [scenarioType, setScenarioType] = useState<"accommodation" | "demand">("accommodation");
  const [addedBeds, setAddedBeds] = useState(500);
  const [visitorChange, setVisitorChange] = useState(20);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const runSim = async () => {
    if (!governorateId) return;
    setLoading(true);
    try {
      const params = new URLSearchParams({
        governorate_id: String(governorateId),
        scenario_type: scenarioType,
        ...(scenarioType === "accommodation"
          ? { added_beds: String(addedBeds) }
          : { visitor_change_pct: String(visitorChange) }),
      });
      const res = await fetch(`${API_URL}/api/analytics/simulate?${params}`, { method: "POST" });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  if (!governorateId) {
    return (
      <div style={{ padding: 20, color: THEME.textMuted, textAlign: "center" }}>
        Select a governorate on the map to run simulations
      </div>
    );
  }

  return (
    <div style={{ padding: 20 }}>
      <h2 style={{ fontSize: 16, color: THEME.accent, margin: "0 0 16px 0", letterSpacing: "0.05em" }}>
        WHAT-IF SIMULATION
      </h2>
      <p style={{ fontSize: 12, color: THEME.textMuted, margin: "0 0 16px 0" }}>
        {governorateName}
      </p>

      {/* Scenario type selector */}
      <div style={{ marginBottom: 16 }}>
        <label style={{ fontSize: 12, color: THEME.textMuted, display: "block", marginBottom: 6 }}>Scenario Type</label>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={() => setScenarioType("accommodation")}
            style={{
              flex: 1, padding: "8px 12px", borderRadius: 6, border: `1px solid ${scenarioType === "accommodation" ? THEME.accent : THEME.border}`,
              backgroundColor: scenarioType === "accommodation" ? "rgba(201,165,92,0.2)" : THEME.surfaceAlt,
              color: THEME.text, cursor: "pointer", fontSize: 12,
            }}
          >
            Add Beds
          </button>
          <button
            onClick={() => setScenarioType("demand")}
            style={{
              flex: 1, padding: "8px 12px", borderRadius: 6, border: `1px solid ${scenarioType === "demand" ? THEME.accent : THEME.border}`,
              backgroundColor: scenarioType === "demand" ? "rgba(201,165,92,0.2)" : THEME.surfaceAlt,
              color: THEME.text, cursor: "pointer", fontSize: 12,
            }}
          >
            Change Visitors
          </button>
        </div>
      </div>

      {/* Input */}
      {scenarioType === "accommodation" ? (
        <div style={{ marginBottom: 16 }}>
          <label style={{ fontSize: 12, color: THEME.textMuted, display: "block", marginBottom: 4 }}>
            Added Beds: {addedBeds}
          </label>
          <input
            type="range" min={0} max={5000} step={100} value={addedBeds}
            onChange={(e) => setAddedBeds(Number(e.target.value))}
            style={{ width: "100%" }}
          />
        </div>
      ) : (
        <div style={{ marginBottom: 16 }}>
          <label style={{ fontSize: 12, color: THEME.textMuted, display: "block", marginBottom: 4 }}>
            Visitor Change: {visitorChange > 0 ? "+" : ""}{visitorChange}%
          </label>
          <input
            type="range" min={-50} max={100} step={5} value={visitorChange}
            onChange={(e) => setVisitorChange(Number(e.target.value))}
            style={{ width: "100%" }}
          />
        </div>
      )}

      {/* Run button */}
      <button
        onClick={runSim}
        disabled={loading}
        style={{
          width: "100%", padding: "10px 16px", borderRadius: 6,
          backgroundColor: THEME.accent, color: "#000", border: "none",
          cursor: "pointer", fontWeight: 600, fontSize: 13,
        }}
      >
        {loading ? "Running..." : "Run Simulation"}
      </button>

      {/* Results */}
      {result && (
        <div style={{ marginTop: 16 }}>
          <h3 style={{ fontSize: 12, color: THEME.textMuted, textTransform: "uppercase", marginBottom: 8 }}>
            Comparison
          </h3>
          <table style={{ width: "100%", fontSize: 12, color: THEME.text, borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${THEME.border}` }}>
                <th style={{ padding: "6px 8px", textAlign: "left", color: THEME.textMuted }}>Indicator</th>
                <th style={{ padding: "6px 8px", textAlign: "right", color: THEME.textMuted }}>Before</th>
                <th style={{ padding: "6px 8px", textAlign: "right", color: THEME.textMuted }}>After</th>
                <th style={{ padding: "6px 8px", textAlign: "right", color: THEME.textMuted }}>Change</th>
              </tr>
            </thead>
            <tbody>
              {result.difference && Object.entries(result.difference)
                .filter(([k]) => !k.startsWith("classification"))
                .map(([key, val]: [string, any]) => (
                  <tr key={key} style={{ borderBottom: `1px solid ${THEME.border}` }}>
                    <td style={{ padding: "6px 8px", fontSize: 11 }}>{key.replace(/_/g, " ")}</td>
                    <td style={{ padding: "6px 8px", textAlign: "right" }}>{val.baseline?.toFixed?.(2) ?? val.baseline}</td>
                    <td style={{ padding: "6px 8px", textAlign: "right" }}>{val.scenario?.toFixed?.(2) ?? val.scenario}</td>
                    <td style={{
                      padding: "6px 8px", textAlign: "right",
                      color: val.change > 0 ? "#22c55e" : val.change < 0 ? "#ef4444" : THEME.textMuted,
                    }}>
                      {val.change > 0 ? "+" : ""}{val.change?.toFixed?.(2) ?? val.change}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>

          {result.difference?.classification_changed && (
            <div style={{
              marginTop: 10, padding: "8px 12px", borderRadius: 6,
              backgroundColor: "rgba(239,68,68,0.15)", border: "1px solid #ef4444",
              fontSize: 12, color: "#ef4444",
            }}>
              Classification changed: {result.difference.classification_before} → {result.difference.classification_after}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
