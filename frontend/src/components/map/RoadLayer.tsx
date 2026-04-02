import React, { useEffect } from 'react';
import maplibregl from 'maplibre-gl';
import { RoadData } from '../../lib/types';
import { useMapStore } from '../../hooks/useMapStore';

interface RoadLayerProps {
  map: maplibregl.Map;
  majorData?: RoadData;
  secondaryData?: RoadData;
  railwayData?: any; // Reusing this for railways too
}

const ROAD_COLORS: Record<string, string> = {
  motorway: '#ff9800',
  motorway_link: '#ff9800',
  trunk: '#ffc107',
  trunk_link: '#ffc107',
  primary: '#a5d6a7',
  secondary: '#81c784',
  railway: '#ab47bc'
};

export const RoadLayer: React.FC<RoadLayerProps> = ({ map, majorData, secondaryData, railwayData }) => {
  const { majorRoads, secondaryRoads, railways } = useMapStore(state => state.layerVisibility);

  // Helper to build and manage a layer
  const syncLayer = (
    id: string, 
    data: any, 
    visible: boolean, 
    isRailway = false,
    defaultWidth = 2
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
            '#ffffff' // fallback
          ],
          'line-width': ['match', ['get', 'type'],
            'motorway', 3,
            'motorway_link', 3,
            'trunk', 2.5,
            'trunk_link', 2.5,
            'railway', 1.5,
            defaultWidth
          ],
          'line-opacity': isRailway ? 0.6 : 0.9,
          'line-dasharray': isRailway ? [3, 3] : undefined
        }
      });
    }

    if (map.getLayer(layerId)) {
      map.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none');
    }
  };

  useEffect(() => {
    syncLayer('major-roads', majorData, majorRoads, false, 2);
    syncLayer('secondary-roads', secondaryData, secondaryRoads, false, 1.2);
    syncLayer('railways', railwayData, railways, true);
  }, [map, majorData, secondaryData, railwayData, majorRoads, secondaryRoads, railways]);

  return null;
};
