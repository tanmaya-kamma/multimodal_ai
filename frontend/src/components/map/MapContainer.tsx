import React, { useRef, useEffect, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useStaticLayers } from '../../hooks/useStaticLayers';
import { useMapStore } from '../../hooks/useMapStore';
import { BoundaryLayer } from './BoundaryLayer';
import { RoadLayer } from './RoadLayer';
import { HeatmapLayer } from './HeatmapLayer';
import { POIMarkers } from './POIMarkers';
import { MapControls } from './MapControls';
import { MapLegend } from './MapLegend';

// Fixed Arlington bounds
const INITIAL_BOUNDS = [
  [-77.172, 38.827], // SW
  [-77.032, 38.934]  // NE
];

export const MapContainer: React.FC = () => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<maplibregl.Map | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  
  const staticData = useStaticLayers();
  const { layerVisibility } = useMapStore();

  useEffect(() => {
    if (!mapContainer.current || map) return;

    const m = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      bounds: INITIAL_BOUNDS as [maplibregl.LngLatLike, maplibregl.LngLatLike],
      fitBoundsOptions: { padding: 40 },
      maxZoom: 18,
      minZoom: 10
    });

    m.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'bottom-right');

    m.on('load', () => {
      setIsLoaded(true);
    });

    setMap(m);

    return () => m.remove();
  }, []); // Only run once

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      {/* Container for MapLibre Canvas */}
      <div 
        ref={mapContainer} 
        style={{ width: '100%', height: '100%', background: '#0a0a0a' }} 
      />

      {/* Map Overlays */}
      <MapControls />
      {layerVisibility.heatmap && <MapLegend />}

      {/* Declarative rendering of map logic (only when map is fully loaded) */}
      {map && isLoaded && (
        <>
          <BoundaryLayer map={map} data={staticData.boundary} />
          {/* Heatmap rendered first so it sits beneath roads and POIs */}
          <HeatmapLayer map={map} />
          <RoadLayer 
            map={map} 
            majorData={staticData.majorRoads} 
            secondaryData={staticData.secondaryRoads} 
            railwayData={staticData.railways}
          />
          <POIMarkers 
            map={map} 
            gasData={staticData.gasStations} 
            groceryData={staticData.groceryStores}
          />
        </>
      )}
    </div>
  );
};
