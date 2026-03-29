"use client";

import { useState } from "react";
import { API_URL, THEME } from "@/lib/constants";

export default function CSVUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [datasetType, setDatasetType] = useState("visitors");
  const [result, setResult] = useState<any>(null);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("dataset_type", datasetType);

    try {
      const res = await fetch(`${API_URL}/api/etl/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setResult(data);
    } catch (e: any) {
      setResult({ status: "failed", error: e.message });
    }
    setUploading(false);
  };

  return (
    <div style={{ padding: 20 }}>
      <h2 style={{ fontSize: 16, color: THEME.accent, margin: "0 0 16px 0", letterSpacing: "0.05em" }}>
        DATA UPLOAD
      </h2>

      {/* Dataset type selector */}
      <div style={{ marginBottom: 16 }}>
        <label style={{ fontSize: 12, color: THEME.textMuted, display: "block", marginBottom: 6 }}>
          Dataset Type
        </label>
        <select
          value={datasetType}
          onChange={(e) => setDatasetType(e.target.value)}
          style={{
            width: "100%", padding: "8px 12px",
            backgroundColor: THEME.surfaceAlt, color: THEME.text,
            border: `1px solid ${THEME.border}`, borderRadius: 6, fontSize: 13,
          }}
        >
          <option value="visitors">Visitor Data</option>
          <option value="occupancy">Occupancy Data</option>
          <option value="site_visits">Site Visit Data</option>
          <option value="hotels">Hotel Data</option>
          <option value="sites">Tourism Sites</option>
        </select>
      </div>

      {/* File picker */}
      <div style={{ marginBottom: 16 }}>
        <label style={{ fontSize: 12, color: THEME.textMuted, display: "block", marginBottom: 6 }}>
          CSV File
        </label>
        <input
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          style={{
            width: "100%", padding: "8px 12px",
            backgroundColor: THEME.surfaceAlt, color: THEME.text,
            border: `1px solid ${THEME.border}`, borderRadius: 6, fontSize: 13,
          }}
        />
      </div>

      {/* Upload button */}
      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        style={{
          width: "100%", padding: "10px 16px", borderRadius: 6,
          backgroundColor: file ? THEME.accent : THEME.border,
          color: file ? "#000" : THEME.textMuted,
          border: "none", cursor: file ? "pointer" : "not-allowed",
          fontWeight: 600, fontSize: 13,
        }}
      >
        {uploading ? "Uploading..." : "Upload & Import"}
      </button>

      {/* Result */}
      {result && (
        <div style={{
          marginTop: 16, padding: "12px 14px", borderRadius: 8,
          backgroundColor: result.status === "success" ? "rgba(34,197,94,0.15)" : "rgba(239,68,68,0.15)",
          border: `1px solid ${result.status === "success" ? "#22c55e" : "#ef4444"}`,
        }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: result.status === "success" ? "#22c55e" : "#ef4444", marginBottom: 6 }}>
            {result.status === "success" ? "✓ Import Successful" : "✗ Import Failed"}
          </div>
          {result.processed !== undefined && (
            <div style={{ fontSize: 12, color: THEME.textMuted }}>
              Processed: {result.processed} | Inserted: {result.inserted} | Skipped: {result.skipped} | Errored: {result.errored}
            </div>
          )}
          {result.errors?.length > 0 && (
            <div style={{ fontSize: 11, color: "#ef4444", marginTop: 6 }}>
              {result.errors.slice(0, 5).map((e: string, i: number) => (
                <div key={i}>• {e}</div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Expected columns hint */}
      <div style={{ marginTop: 20, padding: "10px 12px", borderRadius: 6, backgroundColor: THEME.surfaceAlt, border: `1px solid ${THEME.border}` }}>
        <div style={{ fontSize: 11, color: THEME.textMuted, fontWeight: 600, marginBottom: 4 }}>
          Expected CSV Columns:
        </div>
        <div style={{ fontSize: 10, color: THEME.textMuted, fontFamily: "monospace" }}>
          {datasetType === "visitors" && "governorate_code, year, month, total_visitors, international_visitors, domestic_visitors"}
          {datasetType === "occupancy" && "governorate_code, year, month, avg_occupancy_rate, total_rooms, total_beds, occupied_rooms"}
          {datasetType === "site_visits" && "site_id, year, month, total_visits"}
          {datasetType === "hotels" && "name, hotel_class, governorate_code, latitude, longitude, total_rooms, total_beds"}
          {datasetType === "sites" && "name_en, name_ar, site_type, governorate_code, latitude, longitude, era, description"}
        </div>
      </div>
    </div>
  );
}
