import { apiClient } from './apiClient';
import type {
  BaseLayerMetadata,
  BoundaryData,
  RoadData,
  RailwayData,
  POIData,
  ActiveAlertsData,
  CellDetailData,
  HeatmapData,
  RouteAnalysisRequest,
  RouteAnalysisResponse,
  SimulationRequest,
  SimulationResponse,
} from '../lib/types';

// ═══════════════════════════════════════════════
// TYPED API — Every function maps 1:1 to a FastAPI endpoint
// Ghost endpoints have been removed.
// ═══════════════════════════════════════════════

export const api = {
  // ── Base Layer (Static GeoJSON, cached ∞) ──
  getBaseLayer:      () => apiClient.get<BaseLayerMetadata>('/arlington/base-layer').then(r => r.data),
  getBbox:           () => apiClient.get<{ bbox: any; center: any }>('/arlington/bbox').then(r => r.data),
  getBoundary:       () => apiClient.get<BoundaryData>('/arlington/boundary').then(r => r.data),
  getMajorRoads:     () => apiClient.get<RoadData>('/arlington/roads/major').then(r => r.data),
  getSecondaryRoads: () => apiClient.get<RoadData>('/arlington/roads/secondary').then(r => r.data),
  getRailways:       () => apiClient.get<RailwayData>('/arlington/railways').then(r => r.data),
  getGasStations:    () => apiClient.get<POIData>('/arlington/pois/gas-stations').then(r => r.data),
  getGroceryStores:  () => apiClient.get<POIData>('/arlington/pois/grocery-stores').then(r => r.data),

  // ── Fusion Intelligence (Polled every 30s) ──
  getHeatmap:        () => apiClient.get<HeatmapData>('/arlington/heatmap').then(r => r.data),
  getActiveAlerts:   () => apiClient.get<ActiveAlertsData>('/arlington/alerts/active').then(r => r.data),
  getCellDetail:     (h3Cell: string) => apiClient.get<CellDetailData>(`/arlington/alerts/cell/${h3Cell}`).then(r => r.data),
  
  // ── Fusion Trigger (Manual or scheduled) ──
  runFusion:         () => apiClient.post<{ status: string; alerts_generated: number }>('/arlington/fusion/run').then(r => r.data),

  // ── Route Analysis (On-demand) ──
  analyzeRoutes:     (req: RouteAnalysisRequest) => apiClient.post<RouteAnalysisResponse>('/arlington/routes/analyze', req).then(r => r.data),

  // ── Simulation Trigger (On-demand, chains Fusion) ──
  triggerSimulation: (req: SimulationRequest) => apiClient.post<SimulationResponse>('/arlington/simulation/trigger', req).then(r => r.data),
};