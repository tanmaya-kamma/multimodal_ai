import React from 'react';
import { useMapStore } from '../../hooks/useMapStore';
import { useCellDetail } from '../../hooks/useCellDetail';
import { useAlerts } from '../../hooks/useAlerts';
import { StatusBadge } from '../ui/StatusBadge';
import { SignalTabs } from './SignalTabs';
import { AtRiskSection } from './AtRiskSection';
import { SourceLinks } from './SourceLinks';

export const CellDetailDrawer: React.FC = () => {
  const { selectedCell, isDrawerOpen, setDrawerOpen } = useMapStore();
  const { data: detailData, isLoading: detailLoading } = useCellDetail(selectedCell);
  const { data: alertsData } = useAlerts();

  // Find the fused alert data if it exists for this cell
  const alert = alertsData?.alerts.find(a => a.h3_cell === selectedCell);

  if (!isDrawerOpen) return null;

  return (
    <div style={{
      position: 'absolute',
      top: '16px',
      bottom: '16px',
      right: isDrawerOpen ? '16px' : '-500px', // Slide in animation via right
      width: '420px',
      backgroundColor: 'var(--bg-surface)',
      border: '1px solid var(--border-default)',
      borderRadius: '12px',
      boxShadow: '-8px 0 32px rgba(0,0,0,0.6)',
      zIndex: 200,
      display: 'flex',
      flexDirection: 'column',
      transition: 'right 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
      animation: 'slideInRight 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        padding: '20px 24px',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        background: 'var(--bg-elevated)'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <h2 className="mono" style={{ fontSize: '18px', color: 'var(--text-primary)', margin: 0 }}>
              {selectedCell?.substring(0, 8)}...
            </h2>
            {alert && <StatusBadge tier={alert.alert_tier} />}
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
            H3 Resolution 8 Spatial Index
          </p>
        </div>
        
        <button 
          onClick={() => setDrawerOpen(false)}
          style={{
            background: 'rgba(255,255,255,0.05)',
            border: 'none',
            color: 'var(--text-primary)',
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '18px',
            transition: 'background 0.2s'
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
          onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
        >
          ×
        </button>
      </div>

      {/* Scrollable Content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
        
        {detailLoading ? (
          <div style={{ color: 'var(--text-secondary)', fontSize: '14px', textAlign: 'center', marginTop: '40px' }}>
            Loading intel...
          </div>
        ) : (
          <>
            {/* Context/Explanation if alert exists */}
            {alert && (
              <div style={{ marginBottom: '32px' }}>
                <p style={{ fontSize: '14px', lineHeight: 1.5, color: 'var(--text-primary)' }}>
                  {alert.explanation}
                </p>
              </div>
            )}

            {/* Signal Tabs */}
            <div style={{ marginBottom: '32px' }}>
               <h3 style={{
                  fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em',
                  color: 'var(--text-secondary)', marginBottom: '12px', fontWeight: 600
               }}>Raw Signals</h3>
               {detailData?.signals && <SignalTabs signals={detailData.signals} />}
            </div>

            {/* At Risk Assets */}
            <div style={{ marginBottom: '32px' }}>
               <h3 style={{
                  fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em',
                  color: 'var(--text-secondary)', marginBottom: '12px', fontWeight: 600
               }}>Infrastructure Context</h3>
               {detailData?.at_risk && <AtRiskSection pois={detailData.at_risk.pois} roads={detailData.at_risk.roads} />}
            </div>

            {/* Recommended Actions */}
            {alert && alert.recommended_actions.length > 0 && (
               <div style={{ marginBottom: '32px' }}>
                 <h3 style={{
                    fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em',
                    color: 'var(--accent-cyan)', marginBottom: '12px', fontWeight: 600
                 }}>Recommended Actions</h3>
                 <ul style={{ paddingLeft: '16px', margin: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                   {alert.recommended_actions.map((act, i) => (
                     <li key={i} style={{ fontSize: '13px', lineHeight: 1.4, color: 'var(--text-primary)' }}>{act}</li>
                   ))}
                 </ul>
               </div>
            )}

            {/* Source Evidence */}
            {alert && alert.source_links && <SourceLinks links={alert.source_links} />}
          </>
        )}
      </div>
    </div>
  );
};
