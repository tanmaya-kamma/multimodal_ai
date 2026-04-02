import React from 'react';
import { SidebarHeader } from './SidebarHeader';
import { NavGroup } from '../navigation/NavGroup';
import { NavItem } from '../navigation/NavItem';
import { AlertFeed } from '../alerts/AlertFeed';
import { SystemStatus } from '../ui/SystemStatus';

// Simple SVG Icons
const MapIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon>
    <line x1="8" y1="2" x2="8" y2="18"></line>
    <line x1="16" y1="6" x2="16" y2="22"></line>
  </svg>
);

const HexagonIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
  </svg>
);

const ActivityIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
  </svg>
);

const AlertTriangleIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
    <line x1="12" y1="9" x2="12" y2="13"></line>
    <line x1="12" y1="17" x2="12.01" y2="17"></line>
  </svg>
);

export const Sidebar: React.FC = () => {
  return (
    <aside style={{
      width: '100%',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: 'var(--bg-surface)',
      borderRight: '1px solid var(--border-subtle)',
    }}>
      <SidebarHeader />
      
      <div style={{
        flex: 1,
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
      }}>
        <div style={{ padding: '24px 16px' }}>
          <NavGroup title="Intelligence">
            <NavItem id="supply-map" label="Supply Map" icon={<MapIcon />} />
            <NavItem id="heatmap" label="H3 Heatmap" icon={<HexagonIcon />} />
            <NavItem id="road-network" label="Road Network" icon={<ActivityIcon />} />
            <NavItem id="alerts" label="Active Alerts" icon={<AlertTriangleIcon />} />
          </NavGroup>
        </div>
        
        <div style={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column',
          borderTop: '1px solid var(--border-subtle)',
          overflow: 'hidden' // Important for Marquee
        }}>
          <h3 style={{
            fontSize: '11px',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: 'var(--text-secondary)',
            margin: '16px 20px 8px',
            fontWeight: 600
          }}>
            Live Feed
          </h3>
          <AlertFeed />
        </div>
      </div>
      
      <div style={{
        padding: '16px 20px',
        borderTop: '1px solid var(--border-subtle)',
        background: 'var(--bg-primary)'
      }}>
        <SystemStatus />
      </div>
    </aside>
  );
};
