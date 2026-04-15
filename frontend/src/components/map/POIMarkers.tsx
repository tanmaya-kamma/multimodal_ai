import React, { useEffect, useState } from 'react';
import maplibregl from 'maplibre-gl';
import { POIData } from '../../lib/types';
import { useMapStore } from '../../hooks/useMapStore';

/** Zoom threshold: POIs only render at zoom >= 13 to reduce clutter at overview */
const POI_MIN_ZOOM = 13;

interface POIMarkersProps {
  map: maplibregl.Map;
  gasData?: POIData;
  groceryData?: POIData;
  zoom: number;
}

export const POIMarkers: React.FC<POIMarkersProps> = ({ map, gasData, groceryData, zoom }) => {
  const visible = useMapStore(state => state.layerVisibility.pois);
  const [markers, setMarkers] = useState<maplibregl.Marker[]>([]);

  const shouldShow = visible && zoom >= POI_MIN_ZOOM;

  useEffect(() => {
    // Clean up old markers
    markers.forEach(m => m.remove());
    
    if (!shouldShow) {
      setMarkers([]);
      return;
    }

    const newMarkers: maplibregl.Marker[] = [];

    const addMarkers = (data: any | undefined, color: string, label: string) => {
      if (!data) return;
      
      const items = data.stations || data.stores || data.pois;
      if (!items) return;

      items.forEach((poi: any) => {
        // Create custom element
        const el = document.createElement('div');
        el.className = 'poi-marker';
        el.style.width = '22px';
        el.style.height = '22px';
        el.style.display = 'flex';
        el.style.alignItems = 'center';
        el.style.justifyContent = 'center';
        el.style.backgroundColor = color;
        el.style.border = '2px solid rgba(255, 255, 255, 0.3)';
        el.style.borderRadius = '50%';
        el.style.cursor = 'pointer';
        el.style.boxShadow = `0 0 10px ${color}60`;
        el.style.fontSize = '11px';
        el.style.transition = 'transform 0.2s var(--ease-spring)';
        el.innerHTML = label === 'Gas Station' ? '⛽' : '🛒';
        
        el.addEventListener('mouseenter', () => el.style.transform = 'scale(1.3)');
        el.addEventListener('mouseleave', () => el.style.transform = 'scale(1)');

        const popup = new maplibregl.Popup({ offset: 15, closeButton: false })
          .setHTML(`<div style="font-weight:600;font-size:13px;margin-bottom:4px;color:#000;">${poi.name}</div><div style="font-size:11px;color:#555;">${label}</div>`);

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([poi.lon, poi.lat])
          .setPopup(popup)
          .addTo(map);
          
        newMarkers.push(marker);
      });
    };

    addMarkers(gasData, '#F87171', 'Gas Station');
    addMarkers(groceryData, '#34D399', 'Grocery Store');

    setMarkers(newMarkers);

    return () => {
      newMarkers.forEach(m => m.remove());
    };
  }, [map, gasData, groceryData, shouldShow]);

  return null;
};
