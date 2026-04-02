import React, { useEffect } from 'react';
import maplibregl from 'maplibre-gl';
import { BoundaryData } from '../../lib/types';
import { useMapStore } from '../../hooks/useMapStore';

interface BoundaryLayerProps {
  map: maplibregl.Map;
  data?: BoundaryData;
}

export const BoundaryLayer: React.FC<BoundaryLayerProps> = ({ map, data }) => {
  const visible = useMapStore(state => state.layerVisibility.boundary);

  useEffect(() => {
    if (!data || !data.outer_rings) return;

    const sourceId = 'arlington-boundary-source';
    const layerId = 'arlington-boundary-layer';

    // Convert to GeoJSON
    const geojson: GeoJSON.FeatureCollection = {
      type: 'FeatureCollection',
      features: data.outer_rings.map(ring => ({
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: ring.map(c => [c.lon, c.lat])
        },
        properties: {}
      }))
    };

    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, {
        type: 'geojson',
        data: geojson
      });

      map.addLayer({
        id: layerId,
        type: 'line',
        source: sourceId,
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#4fc3f7',
          'line-width': 2.5,
          'line-dasharray': [3, 3],
          'line-opacity': 0.8
        }
      });
    }

    // Toggle visibility
    if (map.getLayer(layerId)) {
      map.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none');
    }

    return () => {
      // We don't remove the source/layer on unmount normally in this structured app,
      // as it persists, but ideally we should. 
      // For simplicity in hot-reloading we check existence above.
    };
  }, [map, data, visible]);

  return null;
};
