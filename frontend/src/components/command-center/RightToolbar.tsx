import React from 'react';
import { useMapStore } from '../../hooks/useMapStore';

/**
 * RightToolbar — Solaris Clay vertical icon button stack.
 * 
 * Pinned to the right edge, provides toggle access to:
 * - Map Layers slide-out
 * - Route Analysis slide-out
 * - Disaster Simulator slide-out
 */
export const RightToolbar: React.FC = () => {
  const { 
    showLayerPanel, toggleLayerPanel,
    showRoutePanel, toggleRoutePanel,
    showSimPanel, toggleSimPanel 
  } = useMapStore();

  const buttons = [
    {
      id: 'layers',
      icon: '🗺️',
      tooltip: 'Map Layers',
      isActive: showLayerPanel,
      isDanger: false,
      onClick: toggleLayerPanel,
    },
    {
      id: 'routes',
      icon: '🛣️',
      tooltip: 'Route Analysis',
      isActive: showRoutePanel,
      isDanger: false,
      onClick: toggleRoutePanel,
    },
    {
      id: 'disaster',
      icon: '🌪️',
      tooltip: 'Disaster Sim',
      isActive: showSimPanel,
      isDanger: true,
      onClick: toggleSimPanel,
    },
  ];

  return (
    <div style={{
      position: 'absolute',
      top: 'calc(var(--statusbar-height) + 16px)',
      right: 0,
      bottom: 0,
      width: 'var(--toolbar-width)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      paddingTop: '8px',
      gap: '8px',
      zIndex: 200,
      pointerEvents: 'none',
    }}>
      {buttons.map((btn) => (
        <button
          key={btn.id}
          className={`toolbar-btn ${btn.isActive ? (btn.isDanger ? 'active-danger' : 'active') : ''}`}
          data-tooltip={btn.tooltip}
          onClick={btn.onClick}
          aria-label={btn.tooltip}
        >
          {btn.icon}
        </button>
      ))}
    </div>
  );
};
