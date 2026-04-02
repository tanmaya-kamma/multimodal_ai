import { cellToBoundary } from 'h3-js';
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
