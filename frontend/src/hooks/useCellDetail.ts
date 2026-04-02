import { useQuery } from '@tanstack/react-query';
import { api } from '../api/endpoints';

export function useCellDetail(h3Cell: string | null) {
  return useQuery({
    queryKey: ['cellDetail', h3Cell],
    queryFn: () => {
      if (!h3Cell) throw new Error("No cell selected");
      return api.getCellDetail(h3Cell);
    },
    enabled: !!h3Cell,
    staleTime: 60000, // Cache manual click details for 1 minute
  });
}
