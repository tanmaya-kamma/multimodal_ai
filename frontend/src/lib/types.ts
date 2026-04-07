// API Response Types matching FastAPI schema

export interface BaseLayerMetadata {
  area: string;
  center: { lat: number; lon: number };
  bbox: {
    south: number;
    west: number;
    north: number;
    east: number;
  };
  cached_layers: string[];
}

export interface Coordinates {
  lat: number;
  lon: number;
}

export interface BoundaryData {
  outer_rings: Coordinates[][];
}

export interface RoadFeature {
  name: string;
  highway_type: string;
  ref: string | null;
  coordinates: Coordinates[];
}

export interface RoadData {
  roads: RoadFeature[];
}

export interface RailwayFeature {
  name: string;
  operator: string | null;
  usage: string | null;
  service: string | null;
  coordinates: Coordinates[];
}

export interface RailwayData {
  railways: RailwayFeature[];
}

export interface POIFeature {
  name: string;
  address: string | null;
  lat: number;
  lon: number;
}

export interface POIData {
  pois: POIFeature[];
}

export interface HeatmapCell {
  h3_cell: string;
  tier: 'CRITICAL' | 'WARNING' | 'WATCH' | 'NONE';
  severity: number;
  boundary: Coordinates[];
}

export interface HeatmapData {
  total_cells: number;
  cells: HeatmapCell[];
}

export interface Alert {
  h3_cell?: string;
  location: string;
  explanation: string;
  source_links: { source_name: string; description: string; link: string }[];
  severity: number;
  confidence: number;
  recommended_actions: string[];
  alert_tier: 'CRITICAL' | 'WARNING' | 'WATCH' | 'NONE';
  affected_pois: any[];
  affected_roads: any[];
  timestamp: string;
}

export interface ActiveAlertsData {
  total_alerts: number;
  alerts: Alert[];
}

export interface WeatherSignal {
  alert_type: string | null;
  severity: number;
  confidence: number;
  timestamp: string;
}

export interface TrafficSignal {
  camera_id: string;
  congestion: string | null;
  anomaly: string | null;
  image: string | null;
  severity: number;
  timestamp: string;
}

export interface NewsSignal {
  source: string;
  title: string | null;
  location: string | null;
  event_type: string | null;
  severity: number;
  timestamp: string;
}

export interface POIAtRisk {
  type: string;
  name: string | null;
  address: string | null;
  lat: number;
  lon: number;
}

export interface RoadAtRisk {
  name: string | null;
  type: string | null;
  ref: string | null;
}

export interface CellDetailData {
  h3_cell: string;
  signals: {
    weather: WeatherSignal[];
    traffic: TrafficSignal[];
    news: NewsSignal[];
  };
  at_risk: {
    pois: POIAtRisk[];
    roads: RoadAtRisk[];
  };
}
