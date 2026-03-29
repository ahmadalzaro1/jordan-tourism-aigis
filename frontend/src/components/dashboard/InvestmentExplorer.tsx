"use client";

import { useEffect, useState } from "react";
import { fetchInvestmentRanker } from "@/lib/api";
import { THEME, CAPACITY_COLORS } from "@/lib/constants";

interface RankerResult {
  year: number;
  rankings: Array<{
    rank: number;
    governorate: string;
    governorate_id: number;
    priority_score: number;
    recommended_investment_type: string;
    justification: string;
    components: Record<string, number>;
  }>;
}

export default function InvestmentExplorer() {
  const [data, setData] = useState<RankerResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInvestmentRanker()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ color: THEME.textMuted, padding: 40, textAlign: "center" }}>Computing priority scores...</div>;
  if (!data) return <div style={{ color: THEME.textMuted, padding: 40, textAlign: "center" }}>No data available</div>;

  return (
    <div style={{ padding: 20 }}>
      <h2 style={{ fontSize: 16, color: THEME.accent, margin: "0 0 4px 0", letterSpacing: "0.05em" }}>
        INVESTMENT EXPLORER
      </h2>
      <p style={{ fontSize: 11, color: THEME.textMuted, margin: "0 0 20px 0" }}>
        Priority-ranked zones for tourism infrastructure investment ({data.year})
      </p>

      {data.rankings.map((gov) => (
        <div
          key={gov.governorate_id}
          style={{
            backgroundColor: THEME.surfaceAlt,
            border: `1px solid ${THEME.border}`,
            borderRadius: 8,
            padding: "14px 16px",
            marginBottom: 10,
          }}
        >
          {/* Header */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <div>
              <span style={{ color: THEME.accent, fontWeight: 700, fontSize: 14, marginRight: 8 }}>
                #{gov.rank}
              </span>
              <span style={{ color: THEME.text, fontWeight: 600, fontSize: 14 }}>
                {gov.governorate}
              </span>
            </div>
            <div style={{
              backgroundColor: gov.priority_score > 60 ? "#ef4444" : gov.priority_score > 40 ? "#f59e0b" : "#22c55e",
              color: "#fff",
              padding: "3px 10px",
              borderRadius: 12,
              fontSize: 12,
              fontWeight: 600,
            }}>
              {gov.priority_score.toFixed(1)}
            </div>
          </div>

          {/* Score components */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 4, marginBottom: 8 }}>
            {Object.entries(gov.components).map(([key, val]) => (
              <div key={key} style={{ fontSize: 10, color: THEME.textMuted }}>
                <div style={{ marginBottom: 2 }}>{key.replace(/_/g, " ")}</div>
                <div style={{
                  height: 4,
                  backgroundColor: THEME.border,
                  borderRadius: 2,
                  overflow: "hidden",
                }}>
                  <div style={{
                    width: `${val}%`,
                    height: "100%",
                    backgroundColor: THEME.accent,
                    borderRadius: 2,
                  }} />
                </div>
              </div>
            ))}
          </div>

          {/* Recommendation */}
          <div style={{ fontSize: 11, color: THEME.textMuted }}>
            <strong style={{ color: THEME.text }}>Investment:</strong>{" "}
            {gov.recommended_investment_type.replace(/_/g, " ")}
          </div>
          <div style={{ fontSize: 11, color: THEME.textMuted, marginTop: 4 }}>
            {gov.justification}
          </div>
        </div>
      ))}
    </div>
  );
}
