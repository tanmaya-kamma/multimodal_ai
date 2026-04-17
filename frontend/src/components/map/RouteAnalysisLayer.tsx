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

    // 1. Clear Routes Source — Solaris Optimal with Glow
    if (!map.getSource('route-clear-source')) {
      map.addSource('route-clear-source', { type: 'geojson', data: clearGeoJSON });
      
      // Outer glow layer
      map.addLayer({
        id: 'route-clear-glow',
        type: 'line',
        source: 'route-clear-source',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': '#34D399',
          'line-width': 8,
          'line-blur': 6,
          'line-opacity': 0.3
        }
      });

      map.addLayer({
        id: 'route-clear-layer',
        type: 'line',
        source: 'route-clear-source',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': '#34D399',
          'line-width': 3,
          'line-opacity': 0.9
        }
      });
    } else {
      (map.getSource('route-clear-source') as maplibregl.GeoJSONSource).setData(clearGeoJSON);
    }

    // 2. Compromised Routes Source — Solaris Critical
    if (!map.getSource('route-compromised-source')) {
      map.addSource('route-compromised-source', { type: 'geojson', data: compromisedGeoJSON });
      map.addLayer({
        id: 'route-compromised-layer',
        type: 'line',
        source: 'route-compromised-source',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': '#F87171',
          'line-width': 5,
          'line-blur': 4,
          'line-opacity': 0.5
        }
      });
    } else {
      (map.getSource('route-compromised-source') as maplibregl.GeoJSONSource).setData(compromisedGeoJSON);
    }

    // 3. Trail Source (Animated Route Path)
    if (!map.getSource('route-trail-source')) {
      map.addSource('route-trail-source', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
      map.addLayer({
        id: 'route-trail-layer',
        type: 'line',
        source: 'route-trail-source',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': '#FFFFFF',
          'line-width': 2,
          'line-opacity': 0.6,
          'line-blur': 0.5
        }
      });
    }

    // 4. Truck Markers Source (Animated Leads)
    if (!map.getSource('route-truck-source')) {
      map.addSource('route-truck-source', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
      map.addLayer({
        id: 'route-truck-layer',
        type: 'circle',
        source: 'route-truck-source',
        paint: {
          'circle-radius': 5,
          'circle-color': '#FFFFFF',
          'circle-stroke-width': 2,
          'circle-stroke-color': '#34D399',
          'circle-pitch-alignment': 'map'
        }
      });
    }

    // 5. Markers Source (Start/End nodes)
    if (!map.getSource('route-markers-source')) {
      map.addSource('route-markers-source', { type: 'geojson', data: markersGeoJSON });
      map.addLayer({
        id: 'route-markers-layer',
        type: 'circle',
        source: 'route-markers-source',
        paint: {
          'circle-radius': ['case', ['==', ['get', 'type'], 'source'], 6, 5],
          'circle-color': ['case', 
            ['==', ['get', 'type'], 'source'], '#67e8f9',
            ['==', ['get', 'status'], 'severely_compromised'], '#F87171',
            ['==', ['get', 'status'], 'partially_compromised'], '#FB923C',
            '#34D399'
          ],
          'circle-stroke-width': 2,
          'circle-stroke-color': '#000'
        }
      });
    } else {
      (map.getSource('route-markers-source') as maplibregl.GeoJSONSource).setData(markersGeoJSON);
    }

    // Unified Animation loop
    const animate = () => {
      const now = Date.now();
      const t = (now - startTimeRef.current) / 1000;
      
      // A) Pulse effect on compromised lines
      if (map.getLayer('route-compromised-layer')) {
        const opacity = 0.6 + 0.3 * Math.sin(t * Math.PI * 1.5);
        map.setPaintProperty('route-compromised-layer', 'line-opacity', opacity);
      }

      // B) Tactical Truck Lerp and Trail effect
      const LOOP_DURATION_MS = 6000; // 6 seconds to traverse route
      const loopT = (now % LOOP_DURATION_MS) / LOOP_DURATION_MS; // 0.0 to 1.0

      const truckFeatures: GeoJSON.Feature[] = [];
      const trailFeatures: GeoJSON.Feature[] = [];

      routeData.routes.forEach(route => {
        if (route.status === 'route_not_found' || route.route_coordinates.length < 2) return;
        
        const coords = route.route_coordinates;
        const totalPoints = coords.length;
        const exactIndex = loopT * (totalPoints - 1);
        const index1 = Math.floor(exactIndex);
        const index2 = Math.min(index1 + 1, totalPoints - 1);
        const fract = exactIndex - index1;

        // Linear Interpolation
        const p1 = coords[index1];
        const p2 = coords[index2];
        const lng = p1.lon + (p2.lon - p1.lon) * fract;
        const lat = p1.lat + (p2.lat - p1.lat) * fract;

        truckFeatures.push({
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [lng, lat] },
          properties: {}
        });

        const trailCoords = coords.slice(0, index1 + 1).map(c => [c.lon, c.lat]);
        trailCoords.push([lng, lat]);
        
        trailFeatures.push({
          type: 'Feature',
          geometry: { type: 'LineString', coordinates: trailCoords },
          properties: {}
        });
      });

      if (map.getSource('route-truck-source')) {
        (map.getSource('route-truck-source') as maplibregl.GeoJSONSource).setData({
          type: 'FeatureCollection', features: truckFeatures
        });
      }
      if (map.getSource('route-trail-source')) {
        (map.getSource('route-trail-source') as maplibregl.GeoJSONSource).setData({
          type: 'FeatureCollection', features: trailFeatures
        });
      }

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
    };
  }, [map, routeData]);

  // Cleanup on unmount
  useEffect(() => {
    return () => removeLayers(map);
  }, [map]);

  return null;
};

function removeLayers(map: maplibregl.Map) {
  if (!map || !map.getStyle()) return;

  const layers = ['route-clear-layer', 'route-clear-glow', 'route-compromised-layer', 'route-markers-layer', 'route-trail-layer', 'route-truck-layer'];
  layers.forEach(l => { 
    try {
      if (map.getLayer(l)) map.removeLayer(l); 
    } catch (e) {
      console.warn(`Failed to remove layer ${l}:`, e);
    }
  });
  
  const sources = ['route-clear-source', 'route-compromised-source', 'route-markers-source', 'route-trail-source', 'route-truck-source'];
  sources.forEach(s => { 
    try {
      if (map.getSource(s)) map.removeSource(s); 
    } catch (e) {
      console.warn(`Failed to remove source ${s}:`, e);
    }
  });
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
    if (route.destinations && route.destinations.length > 0) {
      route.destinations.forEach(dest => addMarker(dest, 'destination', route.status));
    } else {
      addMarker(route.destination, 'destination', route.status);
    }
  }
  
  return {
    clearGeoJSON: { type: 'FeatureCollection' as const, features: clearFeatures },
    compromisedGeoJSON: { type: 'FeatureCollection' as const, features: compromisedFeatures },
    markersGeoJSON: { type: 'FeatureCollection' as const, features: markersFeatures }
  };
}
