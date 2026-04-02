import { useQuery } from '@tanstack/react-query';
import { api } from '../api/endpoints';
import { heatMapToGeoJson } from '../lib/h3-utils';

export function useHeatmap() {
  return useQuery({
    queryKey: ['heatmap'],
    queryFn: async () => {
      const data = await api.getHeatmap();
      // Transform H3 cells to GeoJSON FeatureCollection on the fly
      const geojson = heatMapToGeoJson(data.cells);
      return { raw: data, geojson };
    },
    refetchInterval: 30000, // Poll every 30s
    staleTime: 10000,
  });
}
