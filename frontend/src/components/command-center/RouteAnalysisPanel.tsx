import React, { useState } from 'react';
import { GlassCard } from '../ui/GlassCard';
import { useRouteAnalysis } from '../../hooks/useRouteAnalysis';
import { RouteAnalysisRequest } from '../../lib/types';
import { useMapStore } from '../../hooks/useMapStore';

/**
 * RouteAnalysisPanel — Slide-out from RightToolbar.
 * Renders inside the slide-out wrapper in CommandCenterShell.
 */
export const RouteAnalysisPanel: React.FC = () => {
  const { mutate, isPending, isError, error, reset } = useRouteAnalysis();
  const { setRouteData, toggleRoutePanel, routeData } = useMapStore();
  
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
          ✕
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
          flex: 1, overflowY: 'auto',
          padding: '16px 20px', 
          borderTop: '1px solid var(--border-subtle)', 
          display: 'flex', flexDirection: 'column', gap: '12px',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Summary</span>
            <span className="mono" style={{ fontSize: '11px', fontWeight: 600 }}>
              {routeData.compromised_routes} / {routeData.total_routes} Compromised
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {routeData.routes.map((r, i) => (
              <div key={i} style={{ 
                padding: '10px 12px', 
                background: 'rgba(255,255,255,0.02)', 
                borderRadius: '8px', 
                borderLeft: `3px solid ${
                  r.status === 'severely_compromised' ? 'var(--status-critical)' : 
                  r.status === 'partially_compromised' ? 'var(--status-watch)' : 'var(--status-optimal)'
                }` 
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontSize: '12px', fontWeight: 600 }}>{r.destination.name}</span>
                  <span className="mono" style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>{(r.distance_km).toFixed(1)}km</span>
                </div>
                <div style={{ fontSize: '10px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  {r.status === 'severely_compromised' ? 'SEVERELY COMPROMISED' : r.status === 'partially_compromised' ? 'PARTIALLY COMPROMISED' : 'CLEAR'}
                </div>
              </div>
            ))}
          </div>

          <button onClick={handleClear} style={{ 
            marginTop: '4px', background: 'transparent', 
            border: '1px solid var(--border-subtle)', 
            color: 'var(--text-secondary)', 
            padding: '6px', borderRadius: '6px', fontSize: '10px', 
            cursor: 'pointer',
            transition: 'border-color 0.2s',
          }}>
            Clear Routes
          </button>
        </div>
      )}
    </div>
  );
};
