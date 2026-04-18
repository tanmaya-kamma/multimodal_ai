import React, { useState } from 'react';
import { useRouteAnalysis } from '../../hooks/useRouteAnalysis';
import { RouteAnalysisRequest } from '../../lib/types';
import { useMapStore } from '../../hooks/useMapStore';
import { X, AlertTriangle, ShieldCheck } from 'lucide-react';

/**
 * RouteAnalysisPanel — Slide-out from RightToolbar.
 * Renders inside the slide-out wrapper in CommandCenterShell.
 */
export const RouteAnalysisPanel: React.FC = () => {
  const { mutate, isPending, isError, error, reset } = useRouteAnalysis();
  const { 
    setRouteData, 
    toggleRoutePanel, 
    routeData, 
    selectedRouteIndices, 
    setLegRouteSelection 
  } = useMapStore();
  
  const [source, setSource] = useState('Ballston');
  const [destinations, setDestinations] = useState('Pentagon City');

  const handleAnalyze = () => {
    if (!source || !destinations) return;
    const destTargets = destinations.split(',').map(d => ({ name: d.trim() })).filter(d => d.name.length > 0);
    const req: RouteAnalysisRequest = {
      source: { name: source.trim() },
      destinations: destTargets
    };
    mutate(req, { onSuccess: (res) => setRouteData(res) });
  };

  const handleClear = () => {
    reset();
    setRouteData(null);
  };

  return (
    <div className="clay-card slide-panel-right open" style={{
      display: 'flex',
      flexDirection: 'column',
      padding: 0,
      height: '100%',
      minHeight: 0,
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{ 
        padding: '16px 20px', 
        borderBottom: '1px solid var(--border-default)', 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        flexShrink: 0,
      }}>
        <h3 style={{ fontSize: '11px', fontWeight: 600, letterSpacing: '0.08em', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
          Route Analysis
        </h3>
        <button 
          onClick={toggleRoutePanel} 
          style={{ 
            background: 'rgba(255, 255, 255, 0.05)', 
            border: 'none', 
            color: 'var(--text-secondary)', 
            cursor: 'pointer',
            width: '24px', height: '24px', borderRadius: '6px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '12px',
            transition: 'background 0.2s',
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
        >
          <X size={14} />
        </button>
      </div>

      {/* Form */}
      <div style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '12px', flexShrink: 0 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <label style={{ fontSize: '10px', color: 'var(--text-secondary)', fontWeight: 600, letterSpacing: '0.06em' }}>SOURCE</label>
          <input 
            type="text" value={source} onChange={e => setSource(e.target.value)} disabled={isPending}
            style={{ 
              padding: '8px 12px', 
              background: 'rgba(0,0,0,0.3)', 
              border: '1px solid var(--border-subtle)', 
              color: 'var(--text-primary)', 
              borderRadius: '8px', 
              fontSize: '13px',
              outline: 'none',
              transition: 'border-color 0.2s',
            }}
            onFocus={(e) => e.currentTarget.style.borderColor = 'rgba(103, 232, 249, 0.3)'}
            onBlur={(e) => e.currentTarget.style.borderColor = 'var(--border-subtle)'}
          />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <label style={{ fontSize: '10px', color: 'var(--text-secondary)', fontWeight: 600, letterSpacing: '0.06em' }}>DESTINATIONS (comma separated)</label>
          <input 
            type="text" value={destinations} onChange={e => setDestinations(e.target.value)} disabled={isPending}
            style={{ 
              padding: '8px 12px', 
              background: 'rgba(0,0,0,0.3)', 
              border: '1px solid var(--border-subtle)', 
              color: 'var(--text-primary)', 
              borderRadius: '8px', 
              fontSize: '13px',
              outline: 'none',
              transition: 'border-color 0.2s',
            }}
            onFocus={(e) => e.currentTarget.style.borderColor = 'rgba(103, 232, 249, 0.3)'}
            onBlur={(e) => e.currentTarget.style.borderColor = 'var(--border-subtle)'}
          />
        </div>

        <button 
          onClick={handleAnalyze} 
          disabled={isPending || !source || !destinations}
          style={{
            marginTop: '4px', padding: '10px',
            background: 'rgba(103, 232, 249, 0.08)',
            border: '1px solid rgba(103, 232, 249, 0.25)',
            color: 'var(--accent-cyan)',
            borderRadius: '10px', fontWeight: 600, fontSize: '12px',
            cursor: (isPending || !source || !destinations) ? 'not-allowed' : 'pointer',
            opacity: (isPending || !source || !destinations) ? 0.4 : 1,
            transition: 'all 0.25s var(--ease-spring)',
            letterSpacing: '0.04em',
          }}
        >
          {isPending ? 'ANALYZING...' : 'ANALYZE ROUTES'}
        </button>

        {isError && (
          <div style={{ 
            padding: '8px 12px', 
            background: 'rgba(248, 113, 113, 0.08)', 
            border: '1px solid rgba(248, 113, 113, 0.2)', 
            color: 'var(--status-critical)', 
            borderRadius: '8px', 
            fontSize: '11px' 
          }}>
            {(error as any)?.detail || 'Failed to analyze routes'}
          </div>
        )}
      </div>

      {/* Results */}
      {routeData && (
        <div style={{ 
          flex: 1, overflowY: 'auto', minHeight: 0,
          padding: '16px 20px', 
          borderTop: '1px solid var(--border-subtle)', 
          display: 'flex', flexDirection: 'column', gap: '16px',
        }}>
          {/* Summary */}
          <div style={{ 
            backgroundColor: 'rgba(255,255,255,0.03)', 
            borderRadius: '8px', 
            padding: '12px', 
            border: '1px solid rgba(255,255,255,0.05)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '4px' }}>
              <span style={{ fontSize: '18px', fontWeight: 700, color: routeData.status === 'clear' ? 'var(--status-optimal)' : 'var(--status-watch)' }}>
                {routeData.compromised_legs} / {routeData.total_legs}
              </span>
              <span style={{ fontSize: '10px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Compromised Legs</span>
            </div>
            <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)', marginTop: '4px' }}>
              {routeData.disrupted_cells_on_route} direct alert overlaps detected
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {(routeData.legs || []).map((leg, legIdx) => {
              const selectedType = selectedRouteIndices[legIdx] || 'primary';
              const currentRoute = selectedType === 'alternate' && leg.alternate_route ? leg.alternate_route : leg.primary_route;
              
              // Guard: unreachable routes have no distance/coordinates
              if (currentRoute.status === 'unreachable') {
                return (
                  <div key={legIdx} style={{ 
                    padding: '12px', 
                    background: 'rgba(248, 113, 113, 0.05)', 
                    borderRadius: '10px', 
                    border: '1px solid rgba(248, 113, 113, 0.15)',
                    borderLeft: '3px solid var(--status-critical)',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '12px', fontWeight: 600 }}>{leg.destination?.name}</span>
                      <span style={{ fontSize: '9px', color: 'var(--status-critical)', textTransform: 'uppercase', fontWeight: 700 }}>
                        Unreachable
                      </span>
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--text-secondary)', marginTop: '6px' }}>
                      {currentRoute.error || 'No driving route found between these points.'}
                    </div>
                  </div>
                );
              }

              return (
                <div key={legIdx} style={{ 
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  padding: '12px', 
                  background: 'rgba(255,255,255,0.015)', 
                  borderRadius: '10px', 
                  border: '1px solid rgba(255,255,255,0.05)',
                  borderLeft: `3px solid ${
                    currentRoute.status === 'severely_compromised' ? 'var(--status-critical)' : 
                    currentRoute.status === 'partially_compromised' ? 'var(--status-watch)' : 'var(--status-optimal)'
                  }` 
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '12px', fontWeight: 600 }}>{leg.destination?.name}</span>
                    <span className="mono" style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>
                      {(currentRoute.distance_km ?? 0).toFixed(1)}km
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <div style={{ 
                      fontSize: '8px', 
                      padding: '1px 5px', 
                      borderRadius: '4px',
                      backgroundColor: selectedType === 'alternate' ? 'rgba(0, 255, 200, 0.1)' : 'rgba(255, 255, 255, 0.05)',
                      color: selectedType === 'alternate' ? '#00ffc8' : 'var(--text-secondary)',
                      textTransform: 'uppercase',
                      fontWeight: 700,
                      border: selectedType === 'alternate' ? '1px solid rgba(0, 255, 200, 0.2)' : '1px solid transparent'
                    }}>
                      {selectedType}
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                      {currentRoute.status?.replace('_', ' ')}
                    </div>
                  </div>

                  {/* Alternative UI */}
                  {leg.alternate_route && (
                    <div style={{ 
                      marginTop: '6px',
                      padding: '10px',
                      borderRadius: '8px',
                      background: selectedType === 'alternate' ? 'rgba(0, 255, 250, 0.03)' : 'rgba(255, 170, 0, 0.03)',
                      border: `1px dashed ${selectedType === 'alternate' ? 'rgba(0, 255, 250, 0.2)' : 'rgba(255, 170, 0, 0.2)'}`
                    }}>
                      <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '6px',
                        marginBottom: '6px',
                        color: selectedType === 'alternate' ? '#00e5ff' : '#ffcf87',
                        fontSize: '10px',
                        fontWeight: 600
                      }}>
                        {selectedType === 'alternate' ? <ShieldCheck size={12} /> : <AlertTriangle size={12} />}
                        <span>{selectedType === 'alternate' ? 'Applied Optimized Route' : 'Alternative Suggested'}</span>
                      </div>
                      
                      <div style={{ fontSize: '10px', color: 'var(--text-secondary)', lineHeight: 1.4, marginBottom: '8px' }}>
                        {leg.alternate_route.reason}
                      </div>

                      <button
                        onClick={() => setLegRouteSelection(legIdx, selectedType === 'primary' ? 'alternate' : 'primary')}
                        style={{
                          width: '100%',
                          padding: '6px',
                          fontSize: '10px',
                          background: selectedType === 'alternate' ? 'rgba(255,255,255,0.05)' : 'rgba(0, 229, 255, 0.15)',
                          border: 'none',
                          borderRadius: '6px',
                          color: selectedType === 'alternate' ? 'white' : '#00e5ff',
                          cursor: 'pointer',
                          fontWeight: 600
                        }}
                      >
                        {selectedType === 'alternate' ? 'Revert to Primary' : 'Switch to Safest Route'}
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <button onClick={handleClear} style={{ 
            marginTop: '8px', background: 'transparent', 
            border: '1px solid var(--border-subtle)', 
            color: 'var(--text-secondary)', 
            padding: '8px', borderRadius: '8px', fontSize: '10px', 
            cursor: 'pointer',
            fontWeight: 600,
            transition: 'all 0.2s',
          }}>
            Clear Analysis
          </button>
        </div>
      )}
    </div>
  );
};
