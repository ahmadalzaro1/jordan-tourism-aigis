/** Jordan coordinates and app constants */

export const JORDAN_CENTER: [number, number] = [35.93, 31.95]; // [lng, lat] for MapLibre
export const JORDAN_BOUNDS: [[number, number], [number, number]] = [
  [34.87, 29.18], // southwest [lng, lat]
  [37.31, 33.37], // northeast [lng, lat]
];

export const GOVERNORATE_CODES: Record<string, string> = {
  AMM: "Amman",
  IRB: "Irbid",
  ZAR: "Zarqa",
  MAF: "Mafraq",
  JER: "Jerash",
  AJL: "Ajloun",
  BAL: "Balqa",
  MAD: "Madaba",
  KAR: "Karak",
  TAF: "Tafilah",
  MAA: "Ma'an",
  AQAB: "Aqaba",
};

export const CAPACITY_COLORS: Record<string, string> = {
  under: "#ef4444", // red
  balanced: "#22c55e", // green
  over: "#f59e0b", // amber
};

export const THEME = {
  background: "#000000",
  surface: "#0a0f1a",
  surfaceAlt: "#141b2d",
  accent: "#c9a55c",
  accentAlt: "#b87333",
  text: "#f5f5f5",
  textMuted: "#8a8f9e",
  border: "#1e2638",
};

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
