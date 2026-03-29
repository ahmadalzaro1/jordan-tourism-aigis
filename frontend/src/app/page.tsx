"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { API_URL, THEME } from "@/lib/constants";

const MapViewer = dynamic(() => import("@/components/map/MapViewer"), { ssr: false });
const DashboardPanel = dynamic(() => import("@/components/dashboard/DashboardPanel"), { ssr: false });
const SimulationPanel = dynamic(() => import("@/components/dashboard/SimulationPanel"), { ssr: false });
const InvestmentExplorer = dynamic(() => import("@/components/dashboard/InvestmentExplorer"), { ssr: false });
const CSVUpload = dynamic(() => import("@/components/dashboard/CSVUpload"), { ssr: false });
const ExportPanel = dynamic(() => import("@/components/dashboard/ExportPanel"), { ssr: false });
const ResearchPanel = dynamic(() => import("@/components/dashboard/ResearchPanel"), { ssr: false });

type Tab = "dashboard" | "simulation" | "investment" | "research" | "upload" | "export";

export default function Home() {
  const [summary, setSummary] = useState<any>(null);
  const [selectedYear, setSelectedYear] = useState(2025);
  const [selectedGovId, setSelectedGovId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [showPriorityZones, setShowPriorityZones] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/api/summary/national?year=${selectedYear}`)
      .then(r => r.json())
      .then(setSummary)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedYear]);

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "dashboard", label: "Overview" },
    { id: "simulation", label: "Simulation" },
    { id: "investment", label: "Investment" },
    { id: "research", label: "Research" },
    { id: "upload", label: "Upload" },
    { id: "export", label: "Export" },
  ];

  return (
    <div style={{ display: "flex", height: "100vh", width: "100vw", overflow: "hidden" }}>
      {/* Left Panel */}
      <div style={{
        width: 420, height: "100vh", flexShrink: 0,
        backgroundColor: THEME.surface,
        borderRight: `1px solid ${THEME.border}`,
        display: "flex", flexDirection: "column",
      }}>
        {/* Header */}
        <div style={{
          padding: "16px 20px 12px",
          borderBottom: `1px solid ${THEME.border}`,
        }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <h1 style={{
                fontSize: 15, fontWeight: 700, color: THEME.accent,
                margin: 0, letterSpacing: "0.08em",
              }}>
                JORDAN TOURISM
              </h1>
              <p style={{ fontSize: 10, color: THEME.textMuted, margin: "2px 0 0" }}>
                AI-Enabled Geo-Analytics Platform
              </p>
            </div>
            <div style={{
              width: 8, height: 8, borderRadius: "50%",
              backgroundColor: "#22c55e",
              boxShadow: "0 0 6px #22c55e",
            }} />
          </div>
        </div>

        {/* Tabs */}
        <div style={{
          display: "flex", borderBottom: `1px solid ${THEME.border}`,
          overflowX: "auto", flexShrink: 0,
        }}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                flex: 1, padding: "10px 6px", border: "none", cursor: "pointer",
                backgroundColor: activeTab === tab.id ? THEME.surfaceAlt : "transparent",
                color: activeTab === tab.id ? THEME.accent : THEME.textMuted,
                borderBottom: activeTab === tab.id ? `2px solid ${THEME.accent}` : "2px solid transparent",
                fontSize: 11, fontWeight: 600, textTransform: "uppercase",
                letterSpacing: "0.03em", whiteSpace: "nowrap",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflow: "auto" }}>
          {activeTab === "dashboard" && (
            <DashboardPanel
              summary={summary}
              loading={loading}
              selectedYear={selectedYear}
              onYearChange={setSelectedYear}
              selectedGovId={selectedGovId}
              onGovSelect={setSelectedGovId}
            />
          )}
          {activeTab === "simulation" && (
            <SimulationPanel governorateId={selectedGovId} governorateName="" />
          )}
          {activeTab === "investment" && <InvestmentExplorer />}
          {activeTab === "research" && <ResearchPanel />}
          {activeTab === "upload" && <CSVUpload />}
          {activeTab === "export" && <ExportPanel />}
        </div>

        {/* Footer */}
        <div style={{
          padding: "8px 16px",
          borderTop: `1px solid ${THEME.border}`,
          fontSize: 9, color: THEME.textMuted,
          display: "flex", justifyContent: "space-between",
        }}>
          <span>70 analytics functions</span>
          <span>55 data sources</span>
          <span>4.89% MAPE</span>
        </div>
      </div>

      {/* Map */}
      <div style={{ flex: 1, height: "100vh", position: "relative" }}>
        <MapViewer
          selectedGovId={selectedGovId}
          onGovSelect={(id) => {
            setSelectedGovId(id);
            if (id) setActiveTab("simulation");
          }}
          selectedYear={selectedYear}
          showHeatmap={showHeatmap}
          showPriorityZones={showPriorityZones}
          onToggleHeatmap={() => setShowHeatmap(!showHeatmap)}
          onTogglePriorityZones={() => setShowPriorityZones(!showPriorityZones)}
        />
      </div>
    </div>
  );
}
