import { useQueries } from '@tanstack/react-query';
import { api } from '../api/endpoints';

export function useStaticLayers() {
  const queries = useQueries({
    queries: [
      {
        queryKey: ['boundary'],
        queryFn: api.getBoundary,
        staleTime: Infinity,
        refetchOnWindowFocus: false,
      },
      {
        queryKey: ['majorRoads'],
        queryFn: api.getMajorRoads,
        staleTime: Infinity,
        refetchOnWindowFocus: false,
      },
      {
        queryKey: ['secondaryRoads'],
        queryFn: api.getSecondaryRoads,
        staleTime: Infinity,
        refetchOnWindowFocus: false,
      },
      {
        queryKey: ['railways'],
        queryFn: api.getRailways,
        staleTime: Infinity,
        refetchOnWindowFocus: false,
      },
      {
        queryKey: ['gasStations'],
        queryFn: api.getGasStations,
        staleTime: Infinity,
        refetchOnWindowFocus: false,
      },
      {
        queryKey: ['groceryStores'],
        queryFn: api.getGroceryStores,
        staleTime: Infinity,
        refetchOnWindowFocus: false,
      }
    ]
  });

  const isLoading = queries.some(q => q.isLoading);
  const isError = queries.some(q => q.isError);

  return {
    boundary: queries[0].data,
    majorRoads: queries[1].data,
    secondaryRoads: queries[2].data,
    railways: queries[3].data,
    gasStations: queries[4].data,
    groceryStores: queries[5].data,
    isLoading,
    isError
  };
}
