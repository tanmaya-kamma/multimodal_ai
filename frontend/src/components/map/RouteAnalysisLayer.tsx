import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import { RouteAnalysisResponse, AnalyzedRoute } from '../../lib/types';
import { coordinateToH3Index } from '../../lib/h3-utils';

interface RouteAnalysisLayerProps {
  map: maplibregl.Map;
  routeData: RouteAnalysisResponse | null;
}

export const RouteAnalysisLayer: React.FC<RouteAnalysisLayerProps> = ({ map, routeData }) => {
  const animationFrameRef = useRef<number | undefined>(undefined);
  const startTimeRef = useRef<number>(Date.now());

  useEffect(() => {
    if (!map || !routeData) {
      removeLayers(map);
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      return;
    }

    const { clearGeoJSON, compromisedGeoJSON, markersGeoJSON } = routesToGeoJSON(routeData.routes);

    // 1. Clear Routes Source
    if (!map.getSource('route-clear-source')) {
      map.addSource('route-clear-source', { type: 'geojson', data: clearGeoJSON });
      map.addLayer({
        id: 'route-clear-layer',
        type: 'line',
        source: 'route-clear-source',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': 'var(--neon-green)',
          'line-width': 4,
          'line-opacity': 0.7,
          'line-blur': 2
        }
      });
    } else {
      (map.getSource('route-clear-source') as maplibregl.GeoJSONSource).setData(clearGeoJSON);
    }

    // 2. Compromised Routes Source
    if (!map.getSource('route-compromised-source')) {
      map.addSource('route-compromised-source', { type: 'geojson', data: compromisedGeoJSON });
      map.addLayer({
        id: 'route-compromised-layer',
        type: 'line',
        source: 'route-compromised-source',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': 'var(--neon-red)',
          'line-width': 5,
          'line-blur': 4,
          'line-opacity': 0.5 // Initial, animated below
        }
      });
    } else {
      (map.getSource('route-compromised-source') as maplibregl.GeoJSONSource).setData(compromisedGeoJSON);
    }

    // 3. Markers Source
    if (!map.getSource('route-markers-source')) {
      map.addSource('route-markers-source', { type: 'geojson', data: markersGeoJSON });
      map.addLayer({
        id: 'route-markers-layer',
        type: 'circle',
        source: 'route-markers-source',
        paint: {
          'circle-radius': ['case', ['==', ['get', 'type'], 'source'], 6, 5],
          'circle-color': ['case', 
            ['==', ['get', 'type'], 'source'], 'var(--accent-cyan)',
            ['==', ['get', 'status'], 'severely_compromised'], 'var(--status-critical)',
            ['==', ['get', 'status'], 'partially_compromised'], 'var(--status-warning)',
            'var(--status-none)'
          ],
          'circle-stroke-width': 2,
          'circle-stroke-color': '#000'
        }
      });
    } else {
      (map.getSource('route-markers-source') as maplibregl.GeoJSONSource).setData(markersGeoJSON);
    }

    // Animation loop for neon pulse on compromised lines
    const animate = () => {
      if (!map.getLayer('route-compromised-layer')) return;
      const t = (Date.now() - startTimeRef.current) / 1000;
      // Pulse between 0.3 and 0.9 opacity roughly every 1.5 seconds
      const opacity = 0.6 + 0.3 * Math.sin(t * Math.PI * 1.5);
      map.setPaintProperty('route-compromised-layer', 'line-opacity', opacity);
      animationFrameRef.current = requestAnimationFrame(animate);
    };

    if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    animate();

    const popup = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      offset: 10
    });

    const handleMouseEnter = (e: any) => {
      map.getCanvas().style.cursor = 'pointer';
      const coordinates = e.features[0].geometry.coordinates.slice();
      const props = e.features[0].properties;
      const desc = `<strong>${props.name}</strong><br/>
                    <span style="font-size: 10px; color: var(--text-secondary)">H3: ${props.h3}</span>`;
      
      while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
        coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
      }
      
      popup.setLngLat(coordinates).setHTML(desc).addTo(map);
    };

    const handleMouseLeave = () => {
      map.getCanvas().style.cursor = '';
      popup.remove();
    };

    map.on('mouseenter', 'route-markers-layer', handleMouseEnter);
    map.on('mouseleave', 'route-markers-layer', handleMouseLeave);

    return () => {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      map.off('mouseenter', 'route-markers-layer', handleMouseEnter);
      map.off('mouseleave', 'route-markers-layer', handleMouseLeave);
      popup.remove();
      // Don't remove layers here; only remove when component unmounts or data is null
    };
  }, [map, routeData]);

  // Cleanup on unmount
  useEffect(() => {
    return () => removeLayers(map);
  }, [map]);

  return null;
};

function removeLayers(map: maplibregl.Map) {
  const layers = ['route-clear-layer', 'route-compromised-layer', 'route-markers-layer'];
  layers.forEach(l => { if (map.getLayer(l)) map.removeLayer(l); });
  
  const sources = ['route-clear-source', 'route-compromised-source', 'route-markers-source'];
  sources.forEach(s => { if (map.getSource(s)) map.removeSource(s); });
}

function routesToGeoJSON(routes: AnalyzedRoute[]) {
  const clearFeatures: GeoJSON.Feature[] = [];
  const compromisedFeatures: GeoJSON.Feature[] = [];
  const markersFeatures: GeoJSON.Feature[] = [];
  
  const addMarker = (loc: any, type: string, status?: string) => {
    markersFeatures.push({
      type: 'Feature',
      properties: { 
        name: loc.name, 
        type, 
        status, 
        h3: coordinateToH3Index(loc.lat, loc.lon) 
      },
      geometry: { type: 'Point', coordinates: [loc.lon, loc.lat] }
    });
  };

  for (const route of routes) {
    if (route.status === 'route_not_found') continue;

    // Full route line
    if (route.route_coordinates.length > 0) {
      clearFeatures.push({
        type: 'Feature',
        properties: { status: route.status, type: 'route' },
        geometry: {
          type: 'LineString',
          coordinates: route.route_coordinates.map(c => [c.lon, c.lat])
        }
      });
    }
    
    // Compromised segments overlays
    for (const seg of route.compromised_segments) {
      compromisedFeatures.push({
        type: 'Feature',
        properties: { type: 'compromised', severity: seg.severity },
        geometry: {
          type: 'LineString',
          coordinates: seg.coordinates.map(c => [c.lon, c.lat])
        }
      });
    }

    addMarker(route.source, 'source');
    addMarker(route.destination, 'destination', route.status);
  }
  
  return {
    clearGeoJSON: { type: 'FeatureCollection' as const, features: clearFeatures },
    compromisedGeoJSON: { type: 'FeatureCollection' as const, features: compromisedFeatures },
    markersGeoJSON: { type: 'FeatureCollection' as const, features: markersFeatures }
  };
}
