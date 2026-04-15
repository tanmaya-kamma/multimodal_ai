import { useMutation } from '@tanstack/react-query';
import { api } from '../api/endpoints';
import type { RouteAnalysisRequest } from '../lib/types';

/**
 * On-demand route analysis mutation.
 * Usage: const { mutate, data } = useRouteAnalysis();
 *        mutate({ source: { name: 'Ballston' }, destinations: [{ name: 'Pentagon City' }] });
 */
export function useRouteAnalysis() {
  return useMutation({
    mutationFn: (req: RouteAnalysisRequest) => api.analyzeRoutes(req),
  });
}
