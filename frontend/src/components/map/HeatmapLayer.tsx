import React, { useEffect } from 'react';
import maplibregl from 'maplibre-gl';
import { useHeatmap } from '../../hooks/useHeatmap';
import { useMapStore } from '../../hooks/useMapStore';

interface HeatmapLayerProps {
  map: maplibregl.Map;
}

export const HeatmapLayer: React.FC<HeatmapLayerProps> = ({ map }) => {
  const { data } = useHeatmap();
  const { layerVisibility, selectedCell, selectCell } = useMapStore();
  const visible = layerVisibility.heatmap;
  
  const sourceId = 'h3-heatmap-source';
  const fillLayerId = 'h3-heatmap-fill';
  const lineLayerId = 'h3-heatmap-line';
  const highlightLayerId = 'h3-heatmap-highlight';

  useEffect(() => {
    if (!data || !data.geojson) return;

    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, {
        type: 'geojson',
        data: data.geojson as GeoJSON.FeatureCollection
      });

      // Fill Layer
      map.addLayer({
        id: fillLayerId,
        type: 'fill',
        source: sourceId,
        paint: {
          'fill-color': [
             'let', 'sev', ['get', 'severity'],
             ['case',
               ['>=', ['var', 'sev'], 0.7], '#f44336',
               ['>=', ['var', 'sev'], 0.45], '#ff9800',
               ['>=', ['var', 'sev'], 0.25], '#ffeb3b',
               '#ffeb3b'
             ]
          ],
          'fill-opacity': [
             'let', 'sev', ['get', 'severity'],
             ['case',
               ['>=', ['var', 'sev'], 0.7], 0.8,
               ['>=', ['var', 'sev'], 0.45], 0.55,
               ['>=', ['var', 'sev'], 0.25], 0.3,
               0.15
             ]
          ]
        }
      });

      // Outline Layer
      map.addLayer({
        id: lineLayerId,
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': '#ffffff',
          'line-opacity': 0.2,
          'line-width': 1
        }
      });

      // Highlight layer for selection
      map.addLayer({
        id: highlightLayerId,
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': '#4fc3f7',
          'line-width': 3,
          'line-opacity': ['case', ['boolean', ['feature-state', 'selected'], false], 1, 0]
        }
      });

      // Click Handler
      map.on('click', fillLayerId, (e) => {
        if (e.features && e.features.length > 0) {
          const h3Cell = e.features[0].properties.h3_cell;
          selectCell(h3Cell);
        }
      });

      // Cursor styles
      map.on('mouseenter', fillLayerId, () => map.getCanvas().style.cursor = 'pointer');
      map.on('mouseleave', fillLayerId, () => map.getCanvas().style.cursor = '');
    } else {
      // Update data if source exists
      (map.getSource(sourceId) as maplibregl.GeoJSONSource).setData(data.geojson as GeoJSON.FeatureCollection);
    }
  }, [map, data]);

  // Handle visibility
  useEffect(() => {
    if (map.getLayer(fillLayerId)) {
      map.setLayoutProperty(fillLayerId, 'visibility', visible ? 'visible' : 'none');
      map.setLayoutProperty(lineLayerId, 'visibility', visible ? 'visible' : 'none');
      map.setLayoutProperty(highlightLayerId, 'visibility', visible ? 'visible' : 'none');
    }
  }, [map, visible]);

  // Handle selection state
  useEffect(() => {
    if (!data || !data.geojson || !map.getSource(sourceId)) return;
    
    // Clear all selected states
    data.geojson.features.forEach((_: any, i: number) => {
       map.setFeatureState(
         { source: sourceId, id: i },
         { selected: false }
       );
    });

    // Set new selected state
    if (selectedCell) {
       const index = data.geojson.features.findIndex((f: any) => f.properties.h3_cell === selectedCell);
       if (index !== -1) {
         // This requires feature IDs to be set or we just use the index if we pass it, 
         // alternatively we can just filter in a separate highlight source.
         // A more reliable way for MapLibre without explicit numeric IDs:
         map.setFilter(highlightLayerId, ['==', ['get', 'h3_cell'], selectedCell]);
         map.setPaintProperty(highlightLayerId, 'line-opacity', 1);
       }
    } else {
       map.setFilter(highlightLayerId, ['==', ['get', 'h3_cell'], '']);
    }
  }, [map, selectedCell, data]);

  return null;
};
