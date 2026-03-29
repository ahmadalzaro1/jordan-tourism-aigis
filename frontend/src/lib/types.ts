export interface Governorate {
  id: number;
  name_en: string;
  name_ar: string;
  code: string;
  area_km2: number;
  population: number;
}

export interface NationalSummary {
  total_visitors: number;
  international_visitors: number;
  domestic_visitors: number;
  total_rooms: number;
  total_beds: number;
  total_hotels: number;
  avg_occupancy_rate: number;
  high_priority_zones: number;
}

export interface GovernorateSummary {
  governorate: Governorate;
  visitors: Array<{ year: number; month: number; total: number; international: number; domestic: number }>;
  occupancy: Array<{ year: number; month: number; rate: number; rooms: number; beds: number }>;
  accommodation: { hotel_count: number; total_rooms: number; total_beds: number };
  indicators: {
    rooms_per_1000_visitors: number | null;
    beds_per_1000_visitors: number | null;
    occupancy_pressure_index: number | null;
    capacity_classification: string | null;
    priority_score: number | null;
  } | null;
}

export interface GeoJSONFeature {
  type: "Feature";
  properties: Record<string, any>;
  geometry: {
    type: string;
    coordinates: any;
  };
}

export interface GeoJSONCollection {
  type: "FeatureCollection";
  features: GeoJSONFeature[];
}
