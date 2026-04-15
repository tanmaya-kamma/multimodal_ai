import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/endpoints';

/**
 * Trigger the fusion engine and invalidate dependent queries.
 * Usage: const { mutate: runFusion } = useFusionTrigger();
 */
export function useFusionTrigger() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.runFusion,
    onSuccess: () => {
      // Invalidate all fusion-dependent queries so they refetch
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['heatmap'] });
    },
  });
}
