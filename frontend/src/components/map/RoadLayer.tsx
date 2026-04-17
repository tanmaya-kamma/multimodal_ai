import React, { useEffect } from 'react';
import maplibregl from 'maplibre-gl';
import { RoadData } from '../../lib/types';
import { useMapStore } from '../../hooks/useMapStore';

interface RoadLayerProps {
  map: maplibregl.Map;
  majorData?: RoadData;
  secondaryData?: RoadData;
  railwayData?: any; // Reusing this for railways too
  zoom: number;
}

const ROAD_COLORS: Record<string, string> = {
  motorway: '#fb923c',
  motorway_link: '#fb923c',
  trunk: '#FBBF24',
  trunk_link: '#FBBF24',
  primary: '#34D399',
  secondary: '#6ee7b7',
  railway: '#c084fc'
};

/** Zoom threshold: secondary roads and railways only render at zoom >= 13 */
const DETAIL_MIN_ZOOM = 13;

export const RoadLayer: React.FC<RoadLayerProps> = ({ map, majorData, secondaryData, railwayData, zoom }) => {
  const { majorRoads, secondaryRoads, railways } = useMapStore(state => state.layerVisibility);

  // Helper to build and manage a layer
  const syncLayer = (
    id: string, 
    data: any, 
    visible: boolean, 
    isRailway = false,
    defaultWidth = 2,
    minZoom?: number
  ) => {
    if (!data || (!data.roads && !data.railways)) return;
    
    const sourceId = `${id}-source`;
    const layerId = `${id}-layer`;

    if (!map.getSource(sourceId)) {
      const items = data.roads || data.railways;
      const geojson: GeoJSON.FeatureCollection = {
        type: 'FeatureCollection',
        features: items.map((item: any) => ({
          type: 'Feature',
          geometry: {
            type: 'LineString',
            coordinates: item.coordinates.map((c: any) => [c.lon, c.lat])
          },
          properties: {
            name: item.name,
            type: isRailway ? 'railway' : item.highway_type,
            ref: item.ref
          }
        }))
      };

      map.addSource(sourceId, { type: 'geojson', data: geojson });

      map.addLayer({
        id: layerId,
        type: 'line',
        source: sourceId,
        ...(minZoom ? { minzoom: minZoom } : {}),
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': ['match', ['get', 'type'],
            'motorway', ROAD_COLORS.motorway,
            'motorway_link', ROAD_COLORS.motorway_link,
            'trunk', ROAD_COLORS.trunk,
            'trunk_link', ROAD_COLORS.trunk_link,
            'primary', ROAD_COLORS.primary,
            'secondary', ROAD_COLORS.secondary,
            'railway', ROAD_COLORS.railway,
            '#71717a' // fallback
          ],
          'line-width': ['match', ['get', 'type'],
            'motorway', 3,
            'motorway_link', 3,
            'trunk', 2.5,
            'trunk_link', 2.5,
            'railway', 1.5,
            defaultWidth
          ],
          'line-opacity': isRailway ? 0.5 : 0.85,
          'line-dasharray': isRailway ? [3, 3] : ([1, 0])
        }
      });
    }

    if (map.getLayer(layerId)) {
      map.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none');
    }
  };

  useEffect(() => {
    // Major roads: always visible (no minzoom constraint)
    syncLayer('major-roads', majorData, majorRoads, false, 2);
    // Secondary roads + railways: minzoom 13 to reduce overview clutter
    syncLayer('secondary-roads', secondaryData, secondaryRoads, false, 1.2, DETAIL_MIN_ZOOM);
    syncLayer('railways', railwayData, railways, true, 1.5, DETAIL_MIN_ZOOM);
  }, [map, majorData, secondaryData, railwayData, majorRoads, secondaryRoads, railways]);

  return null;
};
