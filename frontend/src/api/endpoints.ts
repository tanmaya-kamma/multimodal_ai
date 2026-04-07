import {
  BaseLayerMetadata,
  BoundaryData,
  RoadData,
  RailwayData,
  POIData,
  HeatmapData,
  ActiveAlertsData,
  CellDetailData
} from '../lib/types';

// We point this to your local backend where the Fusion Engine runs
const API_BASE = 'http://localhost:8000';

async function fetcher<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, options);
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status} fetching ${url}`);
  }
  
  return response.json();
}

export const api = {
  // --- EXISTING ARLINGTON DATA (Keep these!) ---
  getBaseLayer: () => fetcher<BaseLayerMetadata>('/arlington/base-layer'),
  getBbox: () => fetcher<{ bbox: any; center: any }>('/arlington/bbox'),
  getBoundary: () => fetcher<BoundaryData>('/arlington/boundary'),
  getMajorRoads: () => fetcher<RoadData>('/arlington/roads/major'),
  getSecondaryRoads: () => fetcher<RoadData>('/arlington/roads/secondary'),
  getRailways: () => fetcher<RailwayData>('/arlington/railways'),
  getGasStations: () => fetcher<POIData>('/arlington/pois/gas-stations'),
  getGroceryStores: () => fetcher<POIData>('/arlington/pois/grocery-stores'),
  getHeatmap: () => fetcher<HeatmapData>('/arlington/heatmap'),
  getActiveAlerts: () => fetcher<ActiveAlertsData>('/arlington/alerts/active'),
  getCellDetail: (h3_cell: string) => fetcher<CellDetailData>(`/arlington/alerts/cell/${h3_cell}`),

  // --- YOUR NEW AI PROJECT DATA (Objective 2) ---
  // This maps the 'Arlington Fusion' to your teammate's actual backend logic
  runFusion: () => fetcher<{ status: string; alerts_generated: number }>('/fusion/process', { method: 'POST' }),
  getPOI: () => fetcher<POIData>('/api/poi'), 
};