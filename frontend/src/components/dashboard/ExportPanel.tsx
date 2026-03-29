"use client";

import { useState } from "react";
import { API_URL, THEME } from "@/lib/constants";

export default function ExportPanel() {
  const [exporting, setExporting] = useState<string | null>(null);

  const exportCSV = async (endpoint: string, filename: string) => {
    setExporting(endpoint);
    try {
      const res = await fetch(`${API_URL}${endpoint}`);
      const data = await res.json();
      
      // Convert to CSV
      if (Array.isArray(data) && data.length > 0) {
        const headers = Object.keys(data[0]);
        const csv = [
          headers.join(","),
          ...data.map(row => headers.map(h => JSON.stringify(row[h] ?? "")).join(","))
        ].join("\n");
        downloadFile(csv, `${filename}.csv`, "text/csv");
      } else if (data.features) {
        // GeoJSON → CSV
        const rows = data.features.map((f: any) => ({
          ...f.properties,
          latitude: f.geometry?.coordinates?.[1],
          longitude: f.geometry?.coordinates?.[0],
        }));
        if (rows.length > 0) {
          const headers = Object.keys(rows[0]);
          const csv = [
            headers.join(","),
            ...rows.map((row: any) => headers.map(h => JSON.stringify(row[h] ?? "")).join(","))
          ].join("\n");
          downloadFile(csv, `${filename}.csv`, "text/csv");
        }
      } else if (data.rankings) {
        // Investment rankings
        const rows = data.rankings.map((r: any) => ({
          rank: r.rank,
          governorate: r.governorate,
          priority_score: r.priority_score,
          investment_type: r.recommended_investment_type,
          justification: r.justification,
          demand_score: r.components?.demand_score,
          capacity_gap_score: r.components?.capacity_gap_score,
          occupancy_pressure_score: r.components?.occupancy_pressure_score,
          growth_score: r.components?.growth_score,
          accessibility_score: r.components?.accessibility_score,
        }));
        const headers = Object.keys(rows[0]);
        const csv = [
          headers.join(","),
          ...rows.map((row: any) => headers.map(h => JSON.stringify(row[h] ?? "")).join(","))
        ].join("\n");
        downloadFile(csv, `${filename}.csv`, "text/csv");
      } else {
        // Generic object export
        const csv = Object.entries(data).map(([k, v]) => `${k},${JSON.stringify(v)}`).join("\n");
        downloadFile(csv, `${filename}.csv`, "text/csv");
      }
    } catch (e) {
      console.error("Export failed:", e);
    }
    setExporting(null);
  };

  const exportMapSnapshot = () => {
    const mapCanvas = document.querySelector(".maplibregl-canvas") as HTMLCanvasElement;
    if (mapCanvas) {
      const link = document.createElement("a");
      link.download = "jordan-tourism-map.png";
      link.href = mapCanvas.toDataURL("image/png");
      link.click();
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2 style={{ fontSize: 16, color: THEME.accent, margin: "0 0 16px 0", letterSpacing: "0.05em" }}>
        EXPORT DATA
      </h2>

      <ExportButton
        label="National Summary (CSV)"
        onClick={() => exportCSV("/api/summary/national", "national_summary")}
        loading={exporting === "/api/summary/national"}
      />
      <ExportButton
        label="Tourism Sites (CSV)"
        onClick={() => exportCSV("/api/geo/sites", "tourism_sites")}
        loading={exporting === "/api/geo/sites"}
      />
      <ExportButton
        label="Hotels (CSV)"
        onClick={() => exportCSV("/api/geo/hotels", "hotels")}
        loading={exporting === "/api/geo/hotels"}
      />
      <ExportButton
        label="Visitor Data (CSV)"
        onClick={() => exportCSV("/api/tourism/visitors", "visitor_data")}
        loading={exporting === "/api/tourism/visitors"}
      />
      <ExportButton
        label="Occupancy Data (CSV)"
        onClick={() => exportCSV("/api/tourism/occupancy", "occupancy_data")}
        loading={exporting === "/api/tourism/occupancy"}
      />
      <ExportButton
        label="Investment Rankings (CSV)"
        onClick={() => exportCSV("/api/analytics/investment-ranker", "investment_rankings")}
        loading={exporting === "/api/analytics/investment-ranker"}
      />
      <ExportButton
        label="Map Snapshot (PNG)"
        onClick={exportMapSnapshot}
        loading={false}
      />
      <ExportButton
        label="Executive Summary (PDF)"
        onClick={() => {
          const year = new Date().getFullYear();
          window.open(`${API_URL}/api/export/executive-summary?year=${year}`, "_blank");
        }}
        loading={false}
      />
    </div>
  );
}

function ExportButton({ label, onClick, loading }: { label: string; onClick: () => void; loading: boolean }) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      style={{
        display: "block", width: "100%", padding: "10px 14px", marginBottom: 8,
        borderRadius: 6, border: `1px solid ${THEME.border}`,
        backgroundColor: THEME.surfaceAlt, color: THEME.text,
        cursor: "pointer", fontSize: 13, textAlign: "left",
      }}
    >
      {loading ? "Exporting..." : `↓ ${label}`}
    </button>
  );
}

function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
