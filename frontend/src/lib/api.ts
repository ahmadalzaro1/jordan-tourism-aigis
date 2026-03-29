import { API_URL } from "./constants";

export async function fetchJSON<T>(path: string, method: "GET" | "POST" = "GET"): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchNationalSummary(year?: number) {
  const params = year ? `?year=${year}` : "";
  return fetchJSON(`/api/summary/national${params}`);
}

export async function fetchGovernorateSummary(id: number, year?: number) {
  const params = year ? `?year=${year}` : "";
  return fetchJSON(`/api/summary/governorate/${id}${params}`);
}

export async function fetchGovernorates() {
  return fetchJSON("/api/geo/governorates");
}

export async function fetchHotels(governorateId?: number) {
  const params = governorateId ? `?governorate_id=${governorateId}` : "";
  return fetchJSON(`/api/geo/hotels${params}`);
}

export async function fetchSites(governorateId?: number) {
  const params = governorateId ? `?governorate_id=${governorateId}` : "";
  return fetchJSON(`/api/geo/sites${params}`);
}

// Analytics
export async function fetchForecast(governorateId: number, horizon: number = 12) {
  return fetchJSON(`/api/analytics/forecast/${governorateId}?horizon_months=${horizon}`, "POST");
}

export async function fetchIndicators(governorateId: number, year: number = 2025) {
  return fetchJSON(`/api/analytics/indicators/${governorateId}?year=${year}`, "POST");
}

export async function fetchInvestmentRanker() {
  return fetchJSON("/api/analytics/investment-ranker");
}

export async function runSimulation(params: {
  governorateId: number;
  scenarioType: "accommodation" | "demand";
  addedBeds?: number;
  visitorChangePct?: number;
}) {
  const qs = new URLSearchParams({
    governorate_id: String(params.governorateId),
    scenario_type: params.scenarioType,
    ...(params.addedBeds ? { added_beds: String(params.addedBeds) } : {}),
    ...(params.visitorChangePct ? { visitor_change_pct: String(params.visitorChangePct) } : {}),
  });
  return fetchJSON(`/api/analytics/simulate?${qs}`, "POST");
}
