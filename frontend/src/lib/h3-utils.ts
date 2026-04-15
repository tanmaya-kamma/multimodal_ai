import { cellToBoundary, latLngToCell, cellToParent, gridDisk, getResolution, isValidCell } from 'h3-js';

// ═══════════════════════════════════════════════
// H3 SYNCHRONIZATION PROTOCOL
// Backend: h3.latlng_to_cell(lat, lon, 8)   [Python h3 v4]
// Frontend: latLngToCell(lat, lng, 8)        [h3-js v4]
// Both use H3 v4 API — function names are identical.
// ═══════════════════════════════════════════════

/** Locked resolution — MUST match backend H3_RESOLUTION constant */
export const H3_RESOLUTION = 8 as const;

/**
 * Coordinate-to-Index handshake.
 * Converts a lat/lng pair to an H3 cell index at Resolution 8.
 * This is the exact client-side equivalent of the backend's:
 *   h3.latlng_to_cell(lat, lon, H3_RESOLUTION)
 *
 * @param lat - Latitude (WGS84)
 * @param lng - Longitude (WGS84)
 * @returns H3 cell index string (e.g., "882a100d63fffff")
 */
export function coordinateToH3Index(lat: number, lng: number): string {
  return latLngToCell(lat, lng, H3_RESOLUTION);
}

/**
 * Get the parent cell at a coarser resolution.
 * Useful for zoom-level aggregation in the command center.
 */
export function getParentCell(h3Index: string, parentResolution: number): string {
  return cellToParent(h3Index, parentResolution);
}

/**
 * Get the k-ring neighborhood of a cell.
 * k=1 returns the cell + 6 immediate neighbors.
 * Used for spatial proximity queries on the client.
 */
export function getNeighborhood(h3Index: string, k: number = 1): string[] {
  return gridDisk(h3Index, k);
}

/**
 * Validate that an H3 index is legitimate and at the expected resolution.
 * Use this as a guard before sending cell IDs to the backend.
 */
export function isValidH3Cell(h3Index: string): boolean {
  return isValidCell(h3Index) && getResolution(h3Index) === H3_RESOLUTION;
}
import { Coordinates, HeatmapCell } from './types';

// The backend already provides pre-calculated boundaries, but we have this
// in case we need to build our own from an H3 index ID on the client
export function h3ToGeoJsonPolygon(h3Index: string, severityLevel: number, tierLevel: string) {
  // Returns [lat, lng][]
  const boundary = cellToBoundary(h3Index);
  
  // GeoJSON expects [lng, lat] and the first and last point must be same
  const coordinates = boundary.map(coord => [coord[1], coord[0]]);
  coordinates.push(coordinates[0]);

  return {
    type: 'Feature' as const,
    properties: {
      h3_cell: h3Index,
      severity: severityLevel,
      tier: tierLevel
    },
    geometry: {
      type: 'Polygon' as const,
      coordinates: [coordinates]
    }
  };
}

export function heatMapToGeoJson(cells: HeatmapCell[]) {
  const features = cells.map(cell => {
    // If boundary is already provided by backend format [{lat, lon}]
    if (cell.boundary && cell.boundary.length > 0) {
       const coordinates = cell.boundary.map((c: Coordinates) => [c.lon, c.lat]);
       // Ensure closed polygon
       if (coordinates.length > 0 && 
          (coordinates[0][0] !== coordinates[coordinates.length - 1][0] || 
           coordinates[0][1] !== coordinates[coordinates.length - 1][1])) {
         coordinates.push([...coordinates[0]]);
       }
       
       return {
         type: 'Feature' as const,
         properties: {
           h3_cell: cell.h3_cell,
           severity: cell.severity,
           tier: cell.tier
         },
         geometry: {
           type: 'Polygon' as const,
           coordinates: [coordinates]
         }
       };
    }
    
    // Fallback to client-side calc
    return h3ToGeoJsonPolygon(cell.h3_cell, cell.severity, cell.tier);
  });

  return {
    type: 'FeatureCollection' as const,
    features
  };
}
