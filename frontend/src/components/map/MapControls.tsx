import React from 'react';
import { useMapStore } from '../../hooks/useMapStore';

interface MapControlsSlideOutProps {
  isOpen: boolean;
}

/**
 * MapControlsSlideOut — Slide-out layer toggle panel.
 * Renders inside the right slide-out wrapper in CommandCenterShell.
 * Uses elastic spring animation via CSS class.
 */
export const MapControlsSlideOut: React.FC<MapControlsSlideOutProps> = ({ isOpen }) => {
  const { layerVisibility, toggleLayer } = useMapStore();

  const controls = [
    { id: 'boundary', label: 'County Boundary', color: '#67e8f9' },
    { id: 'majorRoads', label: 'Major Roads', color: '#fb923c' },
    { id: 'secondaryRoads', label: 'Secondary Roads', color: '#6ee7b7' },
    { id: 'railways', label: 'Freight Railways', color: '#c084fc', dashed: true },
    { id: 'pois', label: 'Critical POIs', color: '#34D399', isCircle: true },
    { id: 'heatmap', label: 'H3 Heatmap', color: '#F87171', isHex: true },
  ];

  return (
    <div 
      className={`clay-card slide-panel-right ${isOpen ? 'open' : ''}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        padding: '20px',
        gap: '16px',
      }}
    >
      <h3 style={{
        fontSize: '11px',
        textTransform: 'uppercase',
        letterSpacing: '0.08em',
        color: 'var(--text-secondary)',
        fontWeight: 600,
        paddingBottom: '8px',
        borderBottom: '1px solid var(--border-subtle)',
      }}>
        Map Layers
      </h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {controls.map((ctrl) => {
          const isVisible = layerVisibility[ctrl.id as keyof typeof layerVisibility];
          
          return (
            <label key={ctrl.id} style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              fontSize: '12px',
              cursor: 'pointer',
              padding: '6px 8px',
              borderRadius: '8px',
              opacity: isVisible ? 1 : 0.5,
              background: isVisible ? 'rgba(255, 255, 255, 0.03)' : 'transparent',
              transition: 'all 0.2s ease',
            }}>
              <input 
                type="checkbox"
                checked={isVisible}
                onChange={() => toggleLayer(ctrl.id as any)}
                style={{ 
                  cursor: 'pointer',
                  accentColor: ctrl.color,
                  width: '14px',
                  height: '14px',
                }}
              />
              
              <div style={{
                width: '14px',
                height: ctrl.isCircle ? '14px' : (ctrl.isHex ? '14px' : '4px'),
                borderRadius: ctrl.isCircle ? '50%' : (ctrl.isHex ? '3px' : '2px'),
                backgroundColor: ctrl.color,
                border: ctrl.dashed ? '1px dashed rgba(255,255,255,0.4)' : 'none',
                opacity: ctrl.isHex ? 0.7 : 1,
                flexShrink: 0,
              }} />
              
              <span style={{ color: isVisible ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                {ctrl.label}
              </span>
            </label>
          );
        })}
      </div>
    </div>
  );
};
