import React, { useEffect, useState } from 'react';
import maplibregl from 'maplibre-gl';
import { POIData } from '../../lib/types';
import { useMapStore } from '../../hooks/useMapStore';

interface POIMarkersProps {
  map: maplibregl.Map;
  gasData?: POIData;
  groceryData?: POIData;
}

export const POIMarkers: React.FC<POIMarkersProps> = ({ map, gasData, groceryData }) => {
  const visible = useMapStore(state => state.layerVisibility.pois);
  const [markers, setMarkers] = useState<maplibregl.Marker[]>([]);

  useEffect(() => {
    // Clean up old markers
    markers.forEach(m => m.remove());
    
    if (!visible) {
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
        el.style.width = '24px';
        el.style.height = '24px';
        el.style.display = 'flex';
        el.style.alignItems = 'center';
        el.style.justifyContent = 'center';
        el.style.backgroundColor = color;
        el.style.border = '2px solid #fff';
        el.style.borderRadius = '50%';
        el.style.cursor = 'pointer';
        el.style.boxShadow = `0 0 12px ${color}80`; // Glowing effect
        el.style.fontSize = '12px';
        el.innerHTML = label === 'Gas Station' ? '⛽' : '🛒';

        const popup = new maplibregl.Popup({ offset: 15, closeButton: false })
          .setHTML(`<div style="font-weight:600;font-size:13px;margin-bottom:4px;color:#000;">${poi.name}</div><div style="font-size:11px;color:#555;">${label}</div>`);

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([poi.lon, poi.lat])
          .setPopup(popup)
          .addTo(map);
          
        newMarkers.push(marker);
      });
    };

    addMarkers(gasData, '#f44336', 'Gas Station'); // Red glow
    addMarkers(groceryData, '#4caf50', 'Grocery Store'); // Green glow

    setMarkers(newMarkers);

    return () => {
      newMarkers.forEach(m => m.remove());
    };
  }, [map, gasData, groceryData, visible]);

  return null;
};
