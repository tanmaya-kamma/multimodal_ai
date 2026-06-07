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
  h3_cell: string;
  location: string;
  explanation: string;
  source_links: SourceLink[];
  severity: number;
  confidence: number;
  recommended_actions: string[];
  alert_tier: AlertTier;
  affected_pois: POIAtRisk[];
  affected_roads: RoadAtRisk[];
  timestamp: string;
  // Extended fusion fields (present when consuming FusedIntelligencePacket)
  corroboration_factor?: number;
  source_count?: number;
  signal_count?: number;
  primary_event?: string;
  all_events?: string[];
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
  has_visual_evidence?: boolean;
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

// ═══════════════════════════════════════════════
// FUSED INTELLIGENCE PACKET
// The full output of the attention-weighted fusion engine.
// Maps 1:1 to the Python dict returned by fuse_cell_signals() + run_fusion()
// ═══════════════════════════════════════════════

/** Individual signal with its computed attention weight */
export interface WeightedSignal {
  source: 'weather' | 'traffic' | 'news';
  timestamp: string;
  event_type: string;
  severity: number;       // 0.0–1.0
  confidence: number;     // 0.0–1.0
  attention_weight: number; // source_reliability × temporal_freshness × self_confidence
  details: WeatherDetails | TrafficDetails | NewsDetails;
}

export interface WeatherDetails {
  alert_type: string | null;
  temperature: number | null;
  wind_speed: number | null;
  precipitation: number | null;
}

export interface TrafficDetails {
  camera_id: string;
  congestion_level: string | null;
  anomaly_type: string | null;
  image_path: string | null;  // VLM evidence — relative path to camera capture
}

export interface NewsDetails {
  source_name: string;
  title: string | null;
  extracted_location: string | null;
  urgency: number | null;
  url?: string;
}

/** The full fused intelligence packet for a single H3 cell */
export interface FusedIntelligencePacket {
  h3_cell: string;
  alert_tier: AlertTier;
  location: string;
  explanation: string;
  severity: number;                // fused_severity (0.0–1.0)
  confidence: number;              // fused_confidence (0.0–1.0)
  corroboration_factor: number;    // 1.0–1.5 multiplier
  source_count: number;
  signal_count: number;
  primary_event: string;
  all_events: string[];
  source_links: SourceLink[];
  recommended_actions: string[];
  affected_pois: POIAtRisk[];
  affected_roads: RoadAtRisk[];
  timestamp: string;               // ISO 8601
}

export type AlertTier = 'CRITICAL' | 'WARNING' | 'WATCH' | 'NONE';

export interface SourceLink {
  source_name: string;
  description: string;
  link: string;                    // URL or VLM image path
}

/** SHA-256 content hash for deduplication & integrity verification */
export interface ContentHash {
  algorithm: 'sha256';
  digest: string;                  // hex-encoded
}

/** VLM (Vision-Language Model) evidence envelope */
export interface VLMEvidence {
  camera_id: string;
  image_path: string;              // relative to backend static dir
  analysis_summary: string | null; // VLM-generated description
  detected_anomalies: string[];
  confidence: number;
  content_hash?: ContentHash;
}

// ═══════════════════════════════════════════════
// ROUTE ANALYSIS CONTRACTS
// Maps 1:1 to analyze_routes() return dict
// ═══════════════════════════════════════════════

export interface RouteAnalysisRequest {
  source: { name: string };
  destinations: { name: string }[];
}

export interface RouteAnalysisResponse {
  source: GeocodedLocation;
  total_destinations: number;
  total_legs: number;
  compromised_legs: number;
  disrupted_cells_on_route: number;
  status: 'clear' | 'partially_compromised' | 'severely_compromised' | 'unreachable';
  legs: RouteLeg[];
  metrics: {
    total_distance_km: number;
    total_duration_min: number;
    recommended_distance_km: number;
    recommended_duration_min: number;
  };
  analyzed_at: string;
}

export interface GeocodedLocation {
  name: string;
  lat: number;
  lon: number;
  resolved_address?: string;
}

export interface RouteLeg {
  source: GeocodedLocation;
  destination: GeocodedLocation;
  primary_route: AnalyzedRoute;
  alternate_route: AnalyzedRoute | null;
  alternate_note?: string;
}

export interface AnalyzedRoute {
  status: 'clear' | 'partially_compromised' | 'severely_compromised' | 'route_not_found' | 'unreachable';
  distance_km: number;
  duration_min: number;
  total_cells: number;
  compromised_cells: number;
  total_severity: number;
  route_coordinates: Coordinates[];
  compromised_segments: CompromisedSegment[];
  directions: RouteStep[];
  reason?: string;
  error?: string;
  source?: GeocodedLocation;
  destination?: GeocodedLocation;
  destinations?: GeocodedLocation[];
}

export interface CompromisedSegment {
  coordinates: Coordinates[];
  severity: number;
}

export interface RouteStep {
  instruction: string;
  road_name: string;
  distance_m: number;
  duration_s: number;
}

// ═══════════════════════════════════════════════
// API ENVELOPE
// Standard response wrapper for interceptor layer
// ═══════════════════════════════════════════════

export interface APIErrorEnvelope {
  status: 'error';
  code: number;
  detail: string;
  timestamp: string;
}

// ═══════════════════════════════════════════════
// SIMULATION CONTRACTS
// ═══════════════════════════════════════════════

export type SimulationType = 'flash_flood' | 'traffic_gridlock' | 'supply_shortage';

export interface SimulationRequest {
  scenario: SimulationType;
  epicenter?: { lat: number; lon: number };  // Optional; defaults to scenario-specific zone
  intensity?: number;                        // 0.0–1.0, defaults to 0.85
}

export interface SimulationResponse {
  status: 'success' | 'error';
  scenario: SimulationType;
  records_injected: number;
  alerts_generated: number;
  affected_cells: string[];   // H3 cell IDs (Resolution 8)
  timestamp: string;          // ISO 8601
}
