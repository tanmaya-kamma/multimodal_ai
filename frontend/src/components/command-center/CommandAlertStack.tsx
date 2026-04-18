import React from 'react';
import { GlassCard } from '../ui/GlassCard';
import { useAlerts } from '../../hooks/useAlerts';
import { useMapStore } from '../../hooks/useMapStore';
import { AlertCard } from '../alerts/AlertCard';
import { isValidH3Cell } from '../../lib/h3-utils';
import { deduplicateAlerts } from '../../lib/deduplication';

export const CommandAlertStack: React.FC = () => {
  const { data, isLoading } = useAlerts();
  const selectCell = useMapStore(s => s.selectCell);
  
  const handleAlertClick = (h3Cell: string) => {
    // H3 Parity Guard
    if (isValidH3Cell(h3Cell)) {
      selectCell(h3Cell);
    } else {
      console.warn(`[CommandAlertStack] Invalid H3 index clicked: ${h3Cell}`);
    }
  };

  const dedupedAlerts = data ? deduplicateAlerts(data.alerts) : [];

  return (
    <GlassCard
      animation="slideInLeft"
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        padding: '0',
        maxHeight: '80vh',
        borderRadius: 'var(--clay-radius)',
      }}
    >
      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--border-default)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexShrink: 0,
      }}>
        <h2 style={{ 
          fontSize: '12px', 
          fontWeight: 600, 
          letterSpacing: '0.08em',
          color: 'var(--text-secondary)',
          textTransform: 'uppercase',
        }}>
          Active Alerts
        </h2>
        {data && (
          <span style={{ 
            fontSize: '12px', 
            color: 'var(--accent-cyan)',
            background: 'rgba(103, 232, 249, 0.1)',
            padding: '3px 10px',
            borderRadius: '12px',
            fontWeight: 600,
            fontFamily: "'JetBrains Mono', monospace",
          }}>
            {dedupedAlerts.length}
            {dedupedAlerts.length < data.alerts.length && (
              <span style={{ 
                color: 'var(--text-secondary)', 
                fontSize: '10px', 
                marginLeft: '4px', 
                fontWeight: 400 
              }}>
                / {data.alerts.length}
              </span>
            )}
          </span>
        )}
      </div>

      {/* List Area — Scrollable */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '12px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
      }}>
        {isLoading ? (
          <div style={{ 
            color: 'var(--text-secondary)', 
            fontSize: '13px', 
            textAlign: 'center', 
            marginTop: '32px' 
          }}>
            <div style={{
              width: '20px',
              height: '20px',
              border: '2px solid var(--border-default)',
              borderTopColor: 'var(--accent-cyan)',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 12px'
            }} />
            Syncing fusion data...
          </div>
        ) : !data || dedupedAlerts.length === 0 ? (
          <div style={{ 
            color: 'var(--text-secondary)', 
            fontSize: '13px', 
            textAlign: 'center', 
            marginTop: '32px',
            opacity: 0.7,
          }}>
            <div style={{ fontSize: '24px', marginBottom: '12px', opacity: 0.3 }}>✓</div>
            No active alerts. System optimal.
          </div>
        ) : (
          dedupedAlerts.map((alert, i) => (
            <div 
              key={`${alert.h3_cell}-${i}`}
              onClick={() => handleAlertClick(alert.h3_cell)}
              style={{
                cursor: 'pointer',
                animation: `fadeIn 0.4s ease-out ${i * 0.08}s forwards`,
                opacity: 0,
                transition: 'all 0.2s var(--ease-spring)',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px) translateX(4px)';
                const glow = alert.alert_tier === 'CRITICAL' ? 'rgba(248, 113, 113, 0.3)' : 
                             alert.alert_tier === 'WARNING' ? 'rgba(251, 146, 60, 0.3)' : 
                             'rgba(52, 211, 153, 0.3)';
                e.currentTarget.style.boxShadow = `0 8px 24px ${glow}`;
                e.currentTarget.style.filter = 'brightness(1.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateX(0)';
                e.currentTarget.style.boxShadow = 'none';
                e.currentTarget.style.filter = 'none';
              }}
            >
              <AlertCard alert={alert} />
            </div>
          ))
        )}
      </div>
    </GlassCard>
  );
};
