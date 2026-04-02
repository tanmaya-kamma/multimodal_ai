import React from 'react';

export const MapLegend: React.FC = () => {
  return (
    <div style={{
      position: 'absolute',
      bottom: '24px',
      left: '24px',
      zIndex: 100,
      background: 'rgba(20, 20, 20, 0.85)',
      backdropFilter: 'blur(8px)',
      border: '1px solid var(--border-default)',
      borderRadius: '8px',
      padding: '12px',
      color: 'var(--text-primary)',
      boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
    }}>
      <h3 style={{
        fontSize: '10px',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        color: 'var(--text-secondary)',
        marginBottom: '8px',
        fontWeight: 600,
      }}>
        Disruption Severity
      </h3>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ width: '12px', height: '12px', background: '#f44336', opacity: 0.8, border: '1px solid #fff' }} />
          <span style={{ fontSize: '11px', fontWeight: 600, color: '#f44336' }}>CRITICAL</span>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ width: '12px', height: '12px', background: '#ff9800', opacity: 0.55, border: '1px solid #fff' }} />
          <span style={{ fontSize: '11px', fontWeight: 600, color: '#ff9800' }}>WARNING</span>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ width: '12px', height: '12px', background: '#ffeb3b', opacity: 0.3, border: '1px solid #fff' }} />
          <span style={{ fontSize: '11px', fontWeight: 600, color: '#ffeb3b' }}>WATCH</span>
        </div>
      </div>
    </div>
  );
};
