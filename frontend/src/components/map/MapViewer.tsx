"use client";

import { useState, useEffect, useCallback } from "react";
import Map, { Source, Layer, Popup, NavigationControl } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import { JORDAN_CENTER, JORDAN_BOUNDS, THEME, API_URL } from "@/lib/constants";
import type { GeoJSONCollection } from "@/lib/types";

interface MapViewerProps {
  selectedGovId: number | null;
  onGovSelect: (id: number | null) => void;
  selectedYear: number;
  showHeatmap?: boolean;
  showPriorityZones?: boolean;
  onToggleHeatmap?: () => void;
  onTogglePriorityZones?: () => void;
}

export default function MapViewer({ selectedGovId, onGovSelect, selectedYear, showHeatmap = true, showPriorityZones = true, onToggleHeatmap, onTogglePriorityZones }: MapViewerProps) {
  const [governorates, setGovernorates] = useState<GeoJSONCollection | null>(null);
  const [hotels, setHotels] = useState<GeoJSONCollection | null>(null);
  const [sites, setSites] = useState<GeoJSONCollection | null>(null);
  const [popupInfo, setPopupInfo] = useState<any>(null);
  const [showHotels, setShowHotels] = useState(true);
  const [showSites, setShowSites] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/api/geo/governorates`).then(r => r.json()).then(setGovernorates).catch(console.error);
    fetch(`${API_URL}/api/geo/hotels`).then(r => r.json()).then(setHotels).catch(console.error);
    fetch(`${API_URL}/api/geo/sites`).then(r => r.json()).then(setSites).catch(console.error);
  }, []);

  const handleGovClick = useCallback((e: any) => {
    if (e.features?.length > 0) {
      const props = e.features[0].properties;
      onGovSelect(props.id);
    }
  }, [onGovSelect]);

  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      <Map
        initialViewState={{
          longitude: JORDAN_CENTER[0],
          latitude: JORDAN_CENTER[1],
          zoom: 7,
        }}
        style={{ width: "100%", height: "100%" }}
        mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
        maxBounds={[[34, 28.5], [38, 34]]}
        interactiveLayerIds={["governorate-fill"]}
        onClick={handleGovClick}
      >
        <NavigationControl position="top-right" style={{ backgroundColor: THEME.surface }} />

        {/* Governorate boundaries */}
        {governorates && (
          <Source id="governorates" type="geojson" data={governorates}>
            <Layer
              id="governorate-fill"
              type="fill"
              paint={{
                "fill-color": [
                  "case",
                  ["==", ["get", "id"], selectedGovId || -1],
                  "rgba(201, 165, 92, 0.4)",
                  "rgba(201, 165, 92, 0.1)",
                ],
                "fill-outline-color": "rgba(201, 165, 92, 0.6)",
              }}
            />
            <Layer
              id="governorate-border"
              type="line"
              paint={{
                "line-color": THEME.accent,
                "line-width": 1.5,
                "line-opacity": 0.8,
              }}
            />
            <Layer
              id="governorate-labels"
              type="symbol",
              layout={{
                "text-field": ["get", "name_en"],
                "text-size": 11,
                "text-anchor": "center",
              }}
              paint={{
                "text-color": THEME.text,
                "text-halo-color": "#000",
                "text-halo-width": 1,
              }}
            />
          </Source>
        )}

        {/* Hotels */}
        {showHotels && hotels && (
          <Source id="hotels" type="geojson" data={hotels}>
            <Layer
              id="hotel-markers"
              type="circle"
              paint={{
                "circle-radius": 6,
                "circle-color": THEME.accent,
                "circle-stroke-width": 1.5,
                "circle-stroke-color": "#fff",
              }}
            />
          </Source>
        )}

        {/* Tourism Sites */}
        {showSites && sites && (
          <Source id="sites" type="geojson" data={sites}>
            <Layer
              id="site-markers"
              type="circle"
              paint={{
                "circle-radius": 7,
                "circle-color": [
                  "match",
                  ["get", "site_type"],
                  "archaeological", "#3b82f6",
                  "natural", "#22c55e",
                  "coastal", "#06b6d4",
                  "religious", "#a855f7",
                  "#6b7280",
                ],
                "circle-stroke-width": 1.5,
                "circle-stroke-color": "#fff",
              }}
            />
          </Source>
        )}

        {/* Popup */}
        {popupInfo && (
          <Popup
            longitude={popupInfo.longitude}
            latitude={popupInfo.latitude}
            onClose={() => setPopupInfo(null)}
            style={{ color: "#000" }}
          >
            <div style={{ fontSize: "13px" }}>
              <strong>{popupInfo.name}</strong>
              {popupInfo.type && <div>Type: {popupInfo.type}</div>}
            </div>
          </Popup>
        )}
      </Map>

      {/* Layer Toggle Controls */}
      <div style={{
        position: "absolute",
        top: 12,
        left: 12,
        backgroundColor: THEME.surface,
        border: `1px solid ${THEME.border}`,
        borderRadius: 8,
        padding: "10px 14px",
        fontSize: 13,
        zIndex: 10,
      }}>
        <div style={{ fontWeight: 600, marginBottom: 8, color: THEME.accent }}>Layers</div>
        <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", marginBottom: 6 }}>
          <input type="checkbox" checked={showHotels} onChange={() => setShowHotels(!showHotels)} />
          <span style={{ color: THEME.accent }}>&#9679;</span> Hotels
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", marginBottom: 6 }}>
          <input type="checkbox" checked={showSites} onChange={() => setShowSites(!showSites)} />
          <span style={{ color: "#3b82f6" }}>&#9679;</span> Tourism Sites
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", marginBottom: 6 }}>
          <input type="checkbox" checked={showHeatmap} onChange={onToggleHeatmap} />
          <span style={{ color: "#f59e0b" }}>&#9632;</span> Demand Heatmap
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
          <input type="checkbox" checked={showPriorityZones} onChange={onTogglePriorityZones} />
          <span style={{ color: "#22c55e" }}>&#9679;</span> Priority Zones
        </label>
      </div>

      {/* Wordmark */}
      <div style={{
        position: "absolute",
        bottom: 12,
        left: 12,
        color: THEME.textMuted,
        fontSize: 11,
        letterSpacing: "0.15em",
        pointerEvents: "none",
      }}>
        JORDAN TOURISM AI-GIS
      </div>
    </div>
  );
}
