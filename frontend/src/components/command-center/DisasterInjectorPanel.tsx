import React, { useState, useEffect } from 'react';
import { useMapStore } from '../../hooks/useMapStore';
import { useSimulation } from '../../hooks/useSimulation';
import { SimulationType } from '../../lib/types';

/**
 * DisasterInjectorPanel — Slide-out from RightToolbar.
 * Renders inside the slide-out wrapper in CommandCenterShell.
 */
export const DisasterInjectorPanel: React.FC = () => {
  const { toggleSimPanel } = useMapStore();
  const { mutate, isPending, isSuccess, data } = useSimulation();
  
  const [scenario] = useState<SimulationType>('flash_flood');
  const [intensity, setIntensity] = useState(0.85);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    if (isSuccess && data) {
      setToastMessage(`${data.records_injected} records injected. ${data.alerts_generated} alerts generated across ${data.affected_cells.length} cells.`);
      setTimeout(() => setToastMessage(null), 5000);
    }
  }, [isSuccess, data]);

  const handleInject = () => {
    mutate({ scenario, intensity });
  };

  return (
    <div className="clay-card slide-panel-right open" style={{
      display: 'flex',
      flexDirection: 'column',
      padding: '20px',
      gap: '16px',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ 
          fontSize: '11px', fontWeight: 600, letterSpacing: '0.08em', 
          color: 'var(--status-critical)', textTransform: 'uppercase',
        }}>
          Disaster Injector
        </h2>
        <button 
          onClick={toggleSimPanel}
          style={{ 
            background: 'rgba(255, 255, 255, 0.05)', 
            border: 'none', 
            color: 'var(--text-secondary)', 
            cursor: 'pointer',
            width: '24px', height: '24px', borderRadius: '6px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '12px',
          }}
        >
          ✕
        </button>
      </div>

      {/* Scenario Selection */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <label style={{ fontSize: '10px', color: 'var(--text-secondary)', fontWeight: 600, letterSpacing: '0.06em' }}>SCENARIO</label>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' }}>
          <div style={{
            border: '1px solid rgba(248, 113, 113, 0.3)',
            background: 'rgba(248, 113, 113, 0.08)',
            color: 'var(--text-primary)',
            padding: '10px 0', borderRadius: '8px',
            textAlign: 'center', cursor: 'pointer',
            fontSize: '10px', fontWeight: 600, letterSpacing: '0.02em',
          }}>
            FLASH FLOOD
          </div>
          <div title="Coming Soon" style={{
            border: '1px solid var(--border-subtle)',
            background: 'rgba(0,0,0,0.3)',
            color: 'var(--text-secondary)',
            padding: '10px 0', borderRadius: '8px',
            textAlign: 'center', cursor: 'not-allowed',
            fontSize: '10px', opacity: 0.4,
          }}>
            GRIDLOCK
          </div>
          <div title="Coming Soon" style={{
            border: '1px solid var(--border-subtle)',
            background: 'rgba(0,0,0,0.3)',
            color: 'var(--text-secondary)',
            padding: '10px 0', borderRadius: '8px',
            textAlign: 'center', cursor: 'not-allowed',
            fontSize: '10px', opacity: 0.4,
          }}>
            SHORTAGE
          </div>
        </div>
      </div>

      {/* Epicenter */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <label style={{ fontSize: '10px', color: 'var(--text-secondary)', fontWeight: 600, letterSpacing: '0.06em' }}>EPICENTER</label>
        <input 
          type="text" value="Auto (South Arlington)" readOnly
          style={{ 
            padding: '8px 12px', 
            background: 'rgba(0,0,0,0.3)', 
            border: '1px solid var(--border-subtle)', 
            color: 'var(--text-secondary)', 
            borderRadius: '8px', fontSize: '12px',
            cursor: 'not-allowed'
          }}
        />
      </div>

      {/* Intensity Slider */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <label style={{ fontSize: '10px', color: 'var(--text-secondary)', fontWeight: 600, letterSpacing: '0.06em' }}>INTENSITY</label>
          <span className="mono" style={{ fontSize: '11px', color: 'var(--status-critical)' }}>{(intensity * 100).toFixed(0)}%</span>
        </div>
        <input 
          type="range" min="0.5" max="1.0" step="0.05"
          value={intensity} onChange={(e) => setIntensity(parseFloat(e.target.value))}
          disabled={isPending}
          style={{ width: '100%', accentColor: 'var(--status-critical)', cursor: 'pointer' }}
        />
      </div>

      {/* Inject Button */}
      <button 
        onClick={handleInject} disabled={isPending}
        style={{
          padding: '11px',
          background: 'rgba(248, 113, 113, 0.08)',
          border: '1px solid rgba(248, 113, 113, 0.25)',
          color: 'var(--status-critical)',
          borderRadius: '10px', fontWeight: 600, fontSize: '11px',
          cursor: isPending ? 'not-allowed' : 'pointer',
          opacity: isPending ? 0.5 : 1,
          transition: 'all 0.25s var(--ease-spring)',
          letterSpacing: '0.04em',
        }}
      >
        {isPending ? 'INJECTING...' : 'INJECT DISASTER SCENARIO'}
      </button>

      {/* Toast */}
      {toastMessage && (
        <div style={{
          padding: '10px 12px',
          background: 'rgba(103, 232, 249, 0.08)',
          border: '1px solid rgba(103, 232, 249, 0.2)',
          borderRadius: '8px',
          color: 'var(--accent-cyan)',
          fontSize: '11px', textAlign: 'center',
          animation: 'fadeIn 0.3s',
        }}>
          {toastMessage}
        </div>
      )}
    </div>
  );
};
