import React from 'react';
import { useMapStore } from '../../hooks/useMapStore';

export const MapControls: React.FC = () => {
  const { layerVisibility, toggleLayer } = useMapStore();

  const controls = [
    { id: 'boundary', label: 'County Boundary', color: '#4fc3f7' },
    { id: 'majorRoads', label: 'Major Roads', color: '#ff9800' },
    { id: 'secondaryRoads', label: 'Secondary Roads', color: '#a5d6a7' },
    { id: 'railways', label: 'Freight Railways', color: '#ab47bc', dashed: true },
    { id: 'pois', label: 'Critical POIs', color: '#4caf50', isCircle: true },
    { id: 'heatmap', label: 'H3 Heatmap', color: '#f44336', isHex: true },
  ];

  return (
    <div style={{
      position: 'absolute',
      top: '16px',
      right: '16px',
      zIndex: 100,
      background: 'rgba(20, 20, 20, 0.85)',
      backdropFilter: 'blur(8px)',
      border: '1px solid var(--border-default)',
      borderRadius: '8px',
      padding: '12px 16px',
      minWidth: '200px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
      color: 'var(--text-primary)'
    }}>
      <h3 style={{
        fontSize: '11px',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        color: 'var(--text-secondary)',
        marginBottom: '10px',
        fontWeight: 600,
        borderBottom: '1px solid var(--border-subtle)',
        paddingBottom: '6px'
      }}>
        Map Layers
      </h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {controls.map((ctrl) => {
          const isVisible = layerVisibility[ctrl.id as keyof typeof layerVisibility];
          
          return (
            <label key={ctrl.id} style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              fontSize: '12px',
              cursor: 'pointer',
              opacity: isVisible ? 1 : 0.6,
              transition: 'opacity 0.2s'
            }}>
              <input 
                type="checkbox"
                checked={isVisible}
                onChange={() => toggleLayer(ctrl.id as any)}
                style={{ cursor: 'pointer' }}
              />
              
              <div style={{
                width: '14px',
                height: ctrl.isCircle ? '14px' : (ctrl.isHex ? '14px' : '4px'),
                borderRadius: ctrl.isCircle ? '50%' : (ctrl.isHex ? '2px' : '2px'),
                backgroundColor: ctrl.color,
                border: ctrl.dashed ? '1px dashed #fff' : 'none',
                opacity: ctrl.isHex ? 0.7 : 1
              }} />
              
              {ctrl.label}
            </label>
          );
        })}
      </div>
    </div>
  );
};
