import React from 'react';
import { useAlerts } from '../../hooks/useAlerts';
import { AlertCard } from './AlertCard';

export const AlertFeed: React.FC = () => {
  const { data, isLoading } = useAlerts();

  if (isLoading) {
    return (
      <div style={{ padding: '20px', color: 'var(--text-secondary)', fontSize: '13px' }}>
        Loading active alerts...
      </div>
    );
  }

  if (!data || data.alerts.length === 0) {
    return (
      <div style={{ padding: '20px', color: 'var(--text-secondary)', fontSize: '13px' }}>
        No active alerts. System is stable.
      </div>
    );
  }

  return (
    <div style={{
      flex: 1,
      overflowY: 'auto',
      display: 'flex',
      flexDirection: 'column',
      // Optional: Add a custom scrollbar style here to keep it hidden or minimal
    }}>
      {/* We can use CSS marquee here if we want continuous scrolling, but a plain list is often more accessible. 
          Given the 'Will Phan' directive to make it visually dynamic, we can apply a simple entrance animation. */}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {data.alerts.map((alert, i) => (
          <div 
            key={`${alert.h3_cell}-${i}`} 
            style={{ 
              animation: `fadeIn 0.5s ease-out ${i * 0.1}s forwards`,
              opacity: 0 // Starts hidden for animation
            }}
          >
            <AlertCard alert={alert} />
          </div>
        ))}
      </div>
    </div>
  );
};
