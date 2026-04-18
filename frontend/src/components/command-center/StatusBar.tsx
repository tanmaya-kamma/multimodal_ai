import React, { useState, useEffect } from 'react';
import { GlassCard } from '../ui/GlassCard';
import { SystemStatus } from '../ui/SystemStatus';
import { useFusionTrigger } from '../../hooks/useFusion';
import { useAlerts } from '../../hooks/useAlerts';

export const StatusBar: React.FC = () => {
  const [timeStr, setTimeStr] = useState('');
  const fusionMutation = useFusionTrigger();
  const { isFetching } = useAlerts();

  useEffect(() => {
    const updateTime = () => {
      setTimeStr(new Date().toLocaleTimeString('en-US', { hour12: false }));
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <GlassCard 
      animation="none"
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: 'var(--statusbar-height)',
        zIndex: 200,
        borderRadius: 0,
        borderLeft: 'none',
        borderRight: 'none',
        borderTop: 'none',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
      }}
    >
      {/* Left Group */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '22px',
            height: '22px',
            background: 'linear-gradient(135deg, #67e8f9, #0891b2)',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontWeight: 'bold',
            fontSize: '10px',
            letterSpacing: '-0.5px',
          }}>
            H3
          </div>
          <span style={{ 
            fontWeight: 600, 
            letterSpacing: '0.06em',
            fontSize: '14px'
          }}>
            GRID<span style={{ color: 'var(--accent-cyan)' }}>CORE</span> OMNI
          </span>
        </div>

        <div style={{ width: '1px', height: '18px', background: 'var(--border-default)' }} />

        <SystemStatus />
      </div>

      {/* Right Group */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {isFetching && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ 
              width: '8px', height: '8px', borderRadius: '50%', 
              background: 'var(--accent-cyan)', 
              animation: 'subtlePulse 1.5s infinite', 
              boxShadow: '0 0 8px var(--accent-cyan)' 
            }} />
            <span style={{ 
              fontSize: '11px', color: 'var(--accent-cyan)', fontWeight: 600, 
              textTransform: 'uppercase', letterSpacing: '0.04em' 
            }}>
              Syncing
            </span>
          </div>
        )}
        <button
          onClick={() => fusionMutation.mutate()}
          disabled={fusionMutation.isPending}
          style={{
            background: fusionMutation.isPending ? 'var(--bg-elevated)' : 'rgba(103, 232, 249, 0.1)',
            border: `1px solid ${fusionMutation.isPending ? 'var(--border-subtle)' : 'rgba(103, 232, 249, 0.25)'}`,
            color: fusionMutation.isPending ? 'var(--text-secondary)' : 'var(--accent-cyan)',
            padding: '5px 14px',
            borderRadius: '8px',
            fontSize: '11px',
            fontWeight: 600,
            cursor: fusionMutation.isPending ? 'not-allowed' : 'pointer',
            transition: 'all 0.25s var(--ease-spring)',
            textTransform: 'uppercase',
            letterSpacing: '0.06em'
          }}
        >
          {fusionMutation.isPending ? 'Synthesizing...' : 'Run Fusion'}
        </button>

        <div style={{ width: '1px', height: '18px', background: 'var(--border-default)' }} />

        <div className="mono" style={{ 
          fontSize: '13px', 
          color: 'var(--text-secondary)',
          minWidth: '80px',
          textAlign: 'right'
        }}>
          {timeStr}
        </div>
      </div>
    </GlassCard>
  );
};
