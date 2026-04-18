import React, { useEffect } from 'react';
import maplibregl from 'maplibre-gl';
import { useHeatmap } from '../../hooks/useHeatmap';
import { useMapStore } from '../../hooks/useMapStore';

interface HeatmapLayerProps {
  map: maplibregl.Map;
  beforeId?: string;
}

export const HeatmapLayer: React.FC<HeatmapLayerProps> = ({ map, beforeId }) => {
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

      // Fill Layer — Precision Step-Function Logic
      map.addLayer({
        id: fillLayerId,
        type: 'fill',
        source: sourceId,
        paint: {
          'fill-color': [
            'step', ['get', 'combined_severity'],
            'rgba(52, 211, 153, 0.2)', // 0.0 - 0.3: Transparent Light Green
            0.3, '#FBBF24',            // 0.3 - 0.7: Solaris Yellow
            0.7, '#F87171'             // 0.7 - 1.0: Solaris Red
          ],
          'fill-opacity': [
            'case',
            ['>', ['get', 'combined_severity'], 0],
            0.6, // Enforce 0.6 minimum for active cells
            0.05 // Background ghosting for inactive
          ]
        }
      }, beforeId); 

      // Outline Layer
      map.addLayer({
        id: lineLayerId,
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': '#ffffff',
          'line-opacity': [
            'step', ['get', 'combined_severity'],
            0.05, 
            0.7, 0.2
          ],
          'line-width': 1
        }
      }, beforeId || highlightLayerId); 

      // Pulse glow for high-severity cells
      map.addLayer({
        id: 'h3-heatmap-pulse',
        type: 'line',
        source: sourceId,
        filter: ['>=', ['get', 'severity'], 0.7],
        paint: {
          'line-color': '#F87171',
          'line-width': 4,
          'line-blur': 8,
          'line-opacity': 0.5
        }
      });

      // Highlight layer for selection
      map.addLayer({
        id: highlightLayerId,
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': '#67e8f9',
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
      map.setLayoutProperty('h3-heatmap-pulse', 'visibility', visible ? 'visible' : 'none');
      map.setLayoutProperty(highlightLayerId, 'visibility', visible ? 'visible' : 'none');
    }
  }, [map, visible]);

  // Request Animation Frame for pulse
  useEffect(() => {
    let animationId: number;
    const animate = () => {
      if (map && map.getLayer('h3-heatmap-pulse') && visible) {
        const t = performance.now() / 1500;
        const opacity = 0.2 + 0.5 * Math.abs(Math.sin(t * Math.PI));
        map.setPaintProperty('h3-heatmap-pulse', 'line-opacity', opacity);
      }
      animationId = requestAnimationFrame(animate);
    };
    if (visible) {
      animate();
    }
    return () => cancelAnimationFrame(animationId);
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
         map.setFilter(highlightLayerId, ['==', ['get', 'h3_cell'], selectedCell]);
         map.setPaintProperty(highlightLayerId, 'line-opacity', 1);
       }
    } else {
       map.setFilter(highlightLayerId, ['==', ['get', 'h3_cell'], '']);
    }
  }, [map, selectedCell, data]);

  return null;
};
