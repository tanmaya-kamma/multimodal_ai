import React from 'react';
import { useSystemHealth } from '../../hooks/useAlerts';

export const SystemStatus: React.FC = () => {
  const { data, isLoading, isError } = useSystemHealth();

  let statusColor = 'var(--status-optimal)'; // Green
  let statusText = 'System Real-time';

  if (isLoading) {
    statusColor = 'var(--status-watch)';
    statusText = 'Connecting...';
  } else if (isError) {
    statusColor = 'var(--status-critical)';
    statusText = 'Connection Error';
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <div style={{
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        backgroundColor: statusColor,
        boxShadow: `0 0 8px ${statusColor}`,
        animation: !isError ? 'pulse 2s infinite' : 'none'
      }} />
      <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
        {statusText}
      </span>
      {data && (
        <span style={{ fontSize: '10px', color: '#555', marginLeft: 'auto' }}>
          v0.1.0 // {data.cached_layers?.length || 0}/6 layers
        </span>
      )}
    </div>
  );
};
