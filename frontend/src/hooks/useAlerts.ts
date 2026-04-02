import { useQuery } from '@tanstack/react-query';
import { api } from '../api/endpoints';

export function useAlerts() {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: api.getActiveAlerts,
    refetchInterval: 30000, // Poll every 30s
    staleTime: 10000,
  });
}

// Hook specifically for polling system status
export function useSystemHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: api.getBaseLayer,
    refetchInterval: 30000,
  });
}
