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

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

async function fetcher<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, options);
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status} fetching ${url}`);
  }
  
  return response.json();
}

export const api = {
  // Base Layer
  getBaseLayer: () => fetcher<BaseLayerMetadata>('/arlington/base-layer'),
  getBbox: () => fetcher<{ bbox: any; center: any }>('/arlington/bbox'),
  
  // Static Map Data
  getBoundary: () => fetcher<BoundaryData>('/arlington/boundary'),
  getMajorRoads: () => fetcher<RoadData>('/arlington/roads/major'),
  getSecondaryRoads: () => fetcher<RoadData>('/arlington/roads/secondary'),
  getRailways: () => fetcher<RailwayData>('/arlington/railways'),
  getGasStations: () => fetcher<POIData>('/arlington/pois/gas-stations'),
  getGroceryStores: () => fetcher<POIData>('/arlington/pois/grocery-stores'),
  
  // Engine Data (Polling)
  getHeatmap: () => fetcher<HeatmapData>('/arlington/heatmap'),
  getActiveAlerts: () => fetcher<ActiveAlertsData>('/arlington/alerts/active'),
  
  // Drill-down
  getCellDetail: (h3_cell: string) => fetcher<CellDetailData>(`/arlington/alerts/cell/${h3_cell}`),
  
  // Actions
  runFusion: () => fetcher<{ status: string; alerts_generated: number }>('/arlington/fusion/run', { method: 'POST' }),
};
