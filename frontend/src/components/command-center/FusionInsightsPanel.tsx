import React, { useState, useEffect } from 'react';
import { GlassCard } from '../ui/GlassCard';
import { useMapStore } from '../../hooks/useMapStore';
import { useCellDetail } from '../../hooks/useCellDetail';
import { useAlerts } from '../../hooks/useAlerts';
import { StatusBadge } from '../ui/StatusBadge';
import { SeverityBar } from '../ui/SeverityBar';
import { SignalTabs } from '../drawer/SignalTabs';
import { AtRiskSection } from '../drawer/AtRiskSection';
import { SourceLinks } from '../drawer/SourceLinks';
import { isValidH3Cell } from '../../lib/h3-utils';

export const FusionInsightsPanel: React.FC = () => {
  const selectedCell = useMapStore(s => s.selectedCell);
  const selectCell = useMapStore(s => s.selectCell);
  const { data: cellDetail, isLoading: isLoadingDetail } = useCellDetail(selectedCell);
  const { data: alertsData, isSuccess: isAlertsLoaded } = useAlerts();
  
  const [expanded, setExpanded] = useState(false);

  const alertMatch = alertsData?.alerts.find((a) => a.h3_cell === selectedCell);

  // Clear ghost H3 selection if selected hex has no active alerts
  useEffect(() => {
    if (selectedCell && isAlertsLoaded && !alertMatch) {
      selectCell(null);
    }
  }, [selectedCell, isAlertsLoaded, alertMatch, selectCell]);

  // Return early if no cell is selected or no alert data corresponds
  if (!selectedCell) return null;
  if (!isValidH3Cell(selectedCell)) return null;
  if (!alertMatch) return null;
  
  let primaryTab: 'weather' | 'traffic' | 'news' = 'weather';
  let primaryColor = 'var(--priority-news)';
  
  if (alertMatch?.primary_event) {
    const event = alertMatch.primary_event.toLowerCase();
    if (/storm|flood|wind|ice|tornado|hurricane|thunderstorm|precipitation|weather/i.test(event)) {
      primaryTab = 'weather';
      primaryColor = 'var(--priority-weather)';
    } else if (/congestion|accident|camera|road|traffic|closure/i.test(event)) {
      primaryTab = 'traffic';
      primaryColor = 'var(--priority-traffic)';
    } else {
      primaryTab = 'news';
    }
  }
  
  const handleClose = () => {
    setExpanded(false);
    selectCell(null);
  };

  const glowTier = alertMatch?.alert_tier === 'CRITICAL' ? 'critical' as const : 
                   alertMatch?.alert_tier === 'WATCH' ? 'watch' as const : undefined;

  return (
    <GlassCard
      animation="slideInUp"
      glowTier={glowTier}
      style={{
        height: expanded ? '55vh' : '280px',
        transition: 'height 0.4s var(--ease-smooth)',
        display: 'flex',
        flexDirection: 'column',
        padding: 0,
        marginRight: '296px', // Clear VLM PIP card (280px + gap)
      }}
    >
      {/* Header */}
      <div style={{
        padding: '14px 20px',
        borderBottom: '1px solid var(--border-default)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div>
            <h3 style={{ fontSize: '14px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="mono" style={{ fontSize: '12px', opacity: 0.8 }}>
                {selectedCell.substring(0, 8)}...
              </span>
              {alertMatch && <StatusBadge tier={alertMatch.alert_tier} size="md" />}
            </h3>
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '6px' }}>
          <button 
            onClick={() => setExpanded(!expanded)}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              padding: '5px 12px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '11px',
              transition: 'all 0.2s',
            }}
          >
            {expanded ? 'Collapse' : 'Expand'}
          </button>
          <button 
            onClick={handleClose}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: 'none',
              color: 'var(--text-secondary)',
              width: '26px', height: '26px',
              borderRadius: '6px',
              cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '12px',
            }}
          >
            ✕
          </button>
        </div>
      </div>

      {/* Main Content Area (Scrollable) */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        
        {/* Top Summary Block */}
        {alertMatch ? (
          <div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="evidence-chip" style={{ 
                  background: `color-mix(in srgb, ${primaryColor} 15%, transparent)`, 
                  color: primaryColor, 
                  border: `1px solid color-mix(in srgb, ${primaryColor} 30%, transparent)` 
                }}>
                  {alertMatch.primary_event || 'General Alert'}
                </span>
                {(alertMatch.source_count !== undefined || alertMatch.signal_count !== undefined) && (
                  <span className="mono" style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>
                    {alertMatch.source_count || 0} src / {alertMatch.signal_count || 0} sig
                  </span>
                )}
              </div>
              
              {alertMatch.all_events && alertMatch.all_events.length > 1 && (
                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                  {alertMatch.all_events.filter(e => e !== alertMatch.primary_event).map((evt, idx) => (
                    <span key={idx} style={{ 
                      fontSize: '9px', 
                      background: 'rgba(255,255,255,0.04)', 
                      padding: '2px 6px', 
                      borderRadius: '8px',
                      color: 'var(--text-secondary)'
                    }}>
                      {evt}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <p style={{ fontSize: '13px', lineHeight: 1.5, marginBottom: '14px', color: 'var(--text-primary)' }}>
              {alertMatch.explanation}
            </p>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px', fontSize: '11px', color: 'var(--text-secondary)' }}>
                  <span>Severity</span>
                  <span className="mono">{(alertMatch.severity * 100).toFixed(0)}%</span>
                </div>
                <SeverityBar severity={alertMatch.severity} height="4px" />
              </div>
              
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px', fontSize: '11px', color: 'var(--text-secondary)' }}>
                  <span>Confidence</span>
                  <span className="mono">{(alertMatch.confidence * 100).toFixed(0)}%</span>
                </div>
                <div style={{ position: 'relative' }}>
                  <SeverityBar severity={alertMatch.confidence} height="4px" />
                  {(alertMatch.corroboration_factor || 1) > 1 && (
                    <div style={{ 
                      position: 'absolute', top: '-2px', left: '100%', marginLeft: '6px', 
                      color: 'var(--accent-cyan)', fontSize: '9px', fontWeight: 'bold',
                      background: 'rgba(103, 232, 249, 0.1)',
                      padding: '1px 4px', borderRadius: '3px', whiteSpace: 'nowrap'
                    }}>
                      {alertMatch.corroboration_factor}x
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>No active alerts for this sector.</p>
        )}

        {/* Expanded Details */}
        {expanded && (
          <div style={{ 
            display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', 
            borderTop: '1px solid var(--border-subtle)', paddingTop: '20px',
          }}>
            {/* Left Column: Signals & Evidence */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {isLoadingDetail ? (
                <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>Loading signals...</div>
              ) : cellDetail?.signals ? (
                <SignalTabs signals={cellDetail.signals} initialTab={primaryTab} />
              ) : null}

              {alertMatch?.source_links && alertMatch.source_links.length > 0 && (
                <div>
                  <h4 style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                    Source Verification
                  </h4>
                  <SourceLinks links={alertMatch.source_links} />
                </div>
              )}
            </div>

            {/* Right Column: Impact & Actions */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {isLoadingDetail ? (
                 <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>Loading impact...</div>
              ) : (
                <AtRiskSection 
                  pois={cellDetail?.at_risk.pois || []} 
                  roads={cellDetail?.at_risk.roads || []} 
                />
              )}

              {alertMatch?.recommended_actions && alertMatch.recommended_actions.length > 0 && (
                <div style={{ 
                  background: 'rgba(251, 191, 36, 0.06)', 
                  border: '1px solid rgba(251, 191, 36, 0.15)', 
                  borderRadius: '12px', padding: '14px',
                }}>
                  <h4 style={{ fontSize: '10px', color: 'var(--status-watch)', marginBottom: '10px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px', letterSpacing: '0.04em' }}>
                    ⚡ RECOMMENDED ACTIONS
                  </h4>
                  <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {alertMatch.recommended_actions.map((action, i) => (
                      <li key={i} style={{ fontSize: '12px', color: 'var(--text-primary)', lineHeight: 1.4 }}>{action}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </GlassCard>
  );
};
