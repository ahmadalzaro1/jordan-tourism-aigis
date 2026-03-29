# Complete Data Source Map — Jordan Tourism AI-GIS

**All available datasets and APIs that could feed into the system.**
**Principle: Nothing hard-coded. Everything computed from whatever data exists.**

## Tier 1: Core Tourism Data (Required — MoTA provides)

| Dataset | Source | Format | Status |
|---------|--------|--------|--------|
| Visitor counts by governorate/month | MoTA | CSV | Awaiting real data |
| Hotel occupancy by governorate/month | MoTA | CSV | Awaiting real data |
| Site visit counts by site/month | MoTA | CSV | Awaiting real data |
| Hotel locations (rooms, beds, class) | MoTA | CSV | Awaiting real data |
| Tourism site locations | MoTA | CSV | Awaiting real data |
| Governorate boundaries | MoTA | GeoJSON | Sample created |

## Tier 2: Open Government Data (Available Now)

| Dataset | Source | API | Relevance |
|---------|--------|-----|-----------|
| Population by governorate | Jordan DoS | jorinfo.dos.gov.jo | Tourism dependency ratio |
| Tourism statistics table | Jordan DoS | jorinfo.dos.gov.jo | Historical validation |
| GDP quarterly | CEIC/WorldBank | World Bank API | Economic correlation |
| Tourism receipts (% exports) | World Bank | data.worldbank.org | Revenue analysis |
| Exchange rates (JOD/USD) | Twelve Data / FRED | API available | Affordability for intl tourists |
| Nighttime lights (VIIRS) | NASA Earthdata | API available | Economic activity proxy |

## Tier 3: OpenStreetMap (Available Now — Already Imported)

| Dataset | Count | Relevance |
|---------|-------|-----------|
| Tourism POIs | 1,462 | Hotels, hostels, attractions, viewpoints |
| Restaurants/Cafes | 1,141 | Food service capacity |
| Historic sites | 4,224 | Cultural tourism assets |
| Heritage sites | 23 | UNESCO/designated sites |
| Nature reserves | 177 | Ecotourism assets |
| Shops | 2,847 | Commercial services |

## Tier 4: Weather & Climate (Free API)

| Dataset | Source | API | Relevance |
|---------|--------|-----|-----------|
| Temperature by governorate | Open-Meteo | open-meteo.com (free) | Seasonal demand correlation |
| Rainfall by governorate | Open-Meteo | open-meteo.com (free) | Outdoor tourism impact |
| Sunshine hours | Open-Meteo | open-meteo.com (free) | Beach/nature tourism driver |
| Historical weather (2020+) | Open-Meteo | Historical API | Back-test weather-tourism correlation |

## Tier 5: Calendar & Events (Computable)

| Dataset | Source | Relevance |
|---------|--------|-----------|
| Ramadan dates (2020-2025) | Islamic calendar | Demand suppression during fasting |
| Eid al-Fitr dates | Islamic calendar | Demand spike after Ramadan |
| Eid al-Adha dates | Islamic calendar | Demand spike |
| Jordan public holidays | calendar.jo | Domestic tourism driver |
| School holidays | Ministry of Education | Domestic tourism peaks |
| Events calendar | calendar.jo | Festival/conference impact |

## Tier 6: Aviation Data (Free/Paid APIs)

| Dataset | Source | API | Relevance |
|---------|--------|-----|-----------|
| Queen Alia passenger stats | Airport International Group | Scraping/Press | International arrivals proxy |
| Flight routes to Jordan | OpenFlights | Open data | Connectivity indicator |
| Airline capacity | OAG / Cirium | Paid | Supply-side tourism metric |
| ADS-B flight tracking | ADS-B Exchange | API | Real-time traffic |

## Tier 7: Search & Interest Data (Free API)

| Dataset | Source | API | Relevance |
|---------|--------|-----|-----------|
| Google Trends "travel Jordan" | Google Trends | API (free) | Demand leading indicator |
| Google Trends "Petra" | Google Trends | API | Site-specific interest |
| Wikipedia page views | Wikimedia | API (free) | Attention proxy |
| Booking.com search volume | SimilarWeb | Paid | Booking intent |

## Tier 8: Social Media & Sentiment (Free/Paid)

| Dataset | Source | API | Relevance |
|---------|--------|-----|-----------|
| Instagram location tags | Instagram Graph API | Limited | Social buzz |
| TripAdvisor reviews | Scraping | Manual | Sentiment analysis |
| Twitter/X mentions | Twitter API | Paid | Real-time sentiment |
| Reddit travel posts | Reddit API | Free | Travel discussion trends |

## Tier 9: Economic Indicators (Free APIs)

| Dataset | Source | API | Relevance |
|---------|--------|-----|-----------|
| Jordan GDP | World Bank | Free API | Economic health |
| Inflation rate | World Bank | Free API | Cost of tourism |
| Unemployment rate | World Bank | Free API | Domestic tourism budget |
| Oil prices | EIA / TradingEconomics | Free | Regional economic driver |
| Regional conflict index | ACLED | Free API | Safety perception |

## Tier 10: Infrastructure Data (OpenStreetMap + Gov)

| Dataset | Source | Relevance |
|---------|--------|-----------|
| Road network | OSM/Geofabrik | Accessibility scoring |
| Highway distances | OSM | Time-to-travel calculations |
| Airport locations | OSM + IATA | Air connectivity |
| Border crossings | OSM | Land border tourism |
| Hotel star ratings | MoTA + OSM | Quality tiers |

## Tier 11: WorldMonitor/Crucix Patterns (Study, Don't Copy)

| Pattern | Source Project | Application |
|---------|--------------|-------------|
| RSS feed aggregation | WorldMonitor | Track Jordan tourism news |
| Commodity price tracking | WorldMonitor | Oil prices affect regional tourism |
| Market data integration | WorldMonitor | Currency fluctuations |
| Country risk scoring | WorldMonitor | Safety perception scoring |
| Delta engine (what changed) | Crucix | Dashboard "what changed" panel |
| SSE auto-refresh | Crucix | Live data updates |

## Tier 12: Satellite & Remote Sensing (Free)

| Dataset | Source | Relevance |
|---------|--------|-----------|
| Nighttime lights (VIIRS) | NASA | Economic activity by governorate |
| NDVI vegetation index | NASA | Nature tourism seasonality |
| Sea surface temperature | NASA | Coastal tourism (Aqaba) |
| Air quality (PM2.5) | NASA | Health/tourism quality |

## Implementation Priority

| Priority | Data | Why |
|----------|------|-----|
| NOW | Weather (Open-Meteo) | Free API, immediate correlation with tourism |
| NOW | Ramadan/Eid calendar | Compute from date, no API needed |
| NOW | Google Trends | Free, real-time demand signal |
| NOW | World Bank economic data | Free API, GDP/tourism receipts |
| SOON | Queen Alia airport data | Validate with arrivals |
| SOON | TripAdvisor sentiment | Scrape reviews for sites |
| LATER | Satellite night lights | Economic activity proxy |
| LATER | Social media | Sentiment analysis |
