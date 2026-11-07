"use client";

import { useEffect, useState, useRef } from "react";
import { ScatterplotLayer } from "@deck.gl/layers";
import { HeatmapLayer } from "@deck.gl/aggregation-layers";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { API_URL } from "@/lib/constants";
import type { GeoJSONCollection } from "@/lib/types";

interface HeatmapOverlayProps {
  map: import("maplibre-gl").Map; // MapLibre map instance
  showHeatmap: boolean;
  showPriorityZones: boolean;
  selectedYear: number;
}

export default function HeatmapOverlay({ map, showHeatmap, showPriorityZones }: HeatmapOverlayProps) {
  const [hotels, setHotels] = useState<GeoJSONCollection | null>(null);
  const [sites, setSites] = useState<GeoJSONCollection | null>(null);
  const deckOverlay = useRef<MapboxOverlay | null>(null);

  useEffect(() => {
    Promise.all([
      fetch(`${API_URL}/api/geo/hotels`).then(r => r.json()),
      fetch(`${API_URL}/api/geo/sites`).then(r => r.json()),
    ]).then(([h, s]) => {
      setHotels(h);
      setSites(s);
    }).catch(console.error);
  }, []);

  useEffect(() => {
    if (!map) return;

    const layers: import("@deck.gl/core").Layer[] = [];

    // Heatmap: visitor density from hotel locations (proxy)
    if (showHeatmap && hotels?.features) {
      const hotelData = hotels.features
        .filter((f): f is typeof f & { geometry: import("geojson").Point } => f.geometry?.type === "Point")
        .map(f => ({
          coordinates: f.geometry.coordinates as [number, number],
          weight: Number(f.properties?.total_rooms || 50) / 100,
        }));

      layers.push(
        new HeatmapLayer({
          id: "visitor-heatmap",
          data: hotelData,
          getPosition: (d: {coordinates: [number, number]}) => d.coordinates,
          getWeight: (d: {weight: number}) => d.weight,
          radiusPixels: 60,
          intensity: 1.5,
          threshold: 0.05,
          colorRange: [
            [1, 152, 189, 0],
            [73, 227, 206, 100],
            [216, 254, 181, 150],
            [254, 237, 177, 200],
            [254, 173, 84, 230],
            [209, 55, 78, 255],
          ],
        })
      );
    }

    // Priority zones: colored circles for governorates based on classification
    if (showPriorityZones && sites?.features) {
      const siteData = sites.features
        .filter((f): f is typeof f & { geometry: import("geojson").Point } => f.geometry?.type === "Point")
        .map(f => ({
          coordinates: f.geometry.coordinates as [number, number],
          siteType: String(f.properties?.site_type),
          name: f.properties?.name_en,
        }));

      const siteColors: Record<string, number[]> = {
        archaeological: [59, 130, 246, 200],   // blue
        natural: [34, 197, 94, 200],           // green
        coastal: [6, 182, 212, 200],           // cyan
        religious: [168, 85, 247, 200],        // purple
        cultural: [234, 179, 8, 200],          // yellow
        museum: [239, 68, 68, 200],            // red
      };

      layers.push(
        new ScatterplotLayer({
          id: "priority-zones",
          data: siteData,
          getPosition: (d: {coordinates: [number, number]}) => d.coordinates,
          getRadius: 400,
          getFillColor: (d: {siteType: string}) => (siteColors[d.siteType] || [156, 163, 175, 200]) as [number, number, number, number],
          pickable: true,
          radiusMinPixels: 4,
          radiusMaxPixels: 20,
        })
      );
    }

    // Create or update deck.gl overlay
    const overlay = new MapboxOverlay({
      interleaved: true,
      layers,
    });

    if (deckOverlay.current) {
      map.removeControl(deckOverlay.current);
    }
    map.addControl(overlay);
    deckOverlay.current = overlay;

    return () => {
      if (overlay) {
        try { map.removeControl(overlay); } catch {}
      }
    };
  }, [map, showHeatmap, showPriorityZones, hotels, sites]);

  return null;
}
