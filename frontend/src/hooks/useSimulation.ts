import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/endpoints';
import { SimulationRequest } from '../lib/types';

/**
 * Trigger the simulation engine and invalidate dependent queries.
 * Usage: const { mutate: runSimulation, isPending, ... } = useSimulation();
 */
export function useSimulation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (req: SimulationRequest) => api.triggerSimulation(req),
    onSuccess: () => {
      // Invalidate all fusion and system-dependent queries so they refetch immediately with new simulation data
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['heatmap'] });
      queryClient.invalidateQueries({ queryKey: ['cellDetail'] });
    },
  });
}
