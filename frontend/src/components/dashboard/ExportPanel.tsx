"use client";

import { toCSV } from "@/lib/csv";
import type { GeoJSONFeature } from "@/lib/types";
import { useState } from "react";
import { API_URL, THEME } from "@/lib/constants";

export default function ExportPanel({ year }: { year: number }) {
  const [exporting, setExporting] = useState<string | null>(null);

  const exportCSV = async (endpoint: string, filename: string) => {
    setExporting(endpoint);
    try {
      const res = await fetch(`${API_URL}${endpoint}`);
      const data = await res.json();
      
      if (!res.ok) throw new Error(`Export failed: ${res.status}`);
      let rows: Record<string, unknown>[];
      if (Array.isArray(data)) rows = data;
      else if (data.features) {
        rows = data.features.map((f: GeoJSONFeature) => ({
          ...f.properties,
          ...(f.geometry?.type === "Point" ? {latitude: f.geometry.coordinates[1], longitude: f.geometry.coordinates[0]} : {}),
        }));
      } else if (data.rankings) rows = data.rankings;
      else rows = Object.entries(data).map(([field, value]) => ({field, value}));
      downloadFile(toCSV(rows), `${filename}.csv`, "text/csv;charset=utf-8");
    } catch (e) {
      console.error("Export failed:", e);
    }
    setExporting(null);
  };

  const exportMapSnapshot = () => {
    const mapCanvas = document.querySelector(".maplibregl-canvas") as HTMLCanvasElement;
    if (mapCanvas) {
      mapCanvas.toBlob(blob => {
        if (blob) downloadBlob(blob, "jordan-tourism-map.png");
      }, "image/png");
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
  downloadBlob(new Blob([content], { type: mimeType }), filename);
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
