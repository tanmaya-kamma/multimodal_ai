import React from 'react';
import { MapContainer } from '../map/MapContainer';
import { StatusBar } from './StatusBar';
import { CommandAlertStack } from './CommandAlertStack';
import { VLMVisionCard } from './VLMVisionCard';
import { FusionInsightsPanel } from './FusionInsightsPanel';
import { RouteAnalysisPanel } from './RouteAnalysisPanel';
import { DisasterInjectorPanel } from './DisasterInjectorPanel';
import { RightToolbar } from './RightToolbar';
import { MapControlsSlideOut } from '../map/MapControls';
import { useMapStore } from '../../hooks/useMapStore';
import { ErrorBoundary } from '../ErrorBoundary';

/**
 * CommandCenterShell — Solaris Clay / Bento Grid 2.0
 * 
 * Layout:
 * ┌──────────────────────────────────────────────────┐
 * │  StatusBar (top, full-width, 48px)               │
 * ├──────────┬────────────────────────┬──────────────┤
 * │  Alert   │     MAP CANVAS         │  Toolbar     │
 * │  320px   │     (full-bleed)       │  48px        │
 * │          ├──────────┬─────────────┤              │
 * │          │ Fusion   │ VLM PIP     │              │
 * └──────────┴──────────┴─────────────┴──────────────┘
 * 
 * Pointer-Events Guard:
 * - All clay-wrapper divs have pointer-events: none
 * - All clay-card children have pointer-events: auto
 * - Map canvas remains fully interactive through gaps
 */
export const CommandCenterShell: React.FC = () => {
  const showRoutePanel = useMapStore(s => s.showRoutePanel);
  const showSimPanel = useMapStore(s => s.showSimPanel);
  const showLayerPanel = useMapStore(s => s.showLayerPanel);

  return (
    <ErrorBoundary fallbackMessage="The Command Center encountered an error. Click Retry to recover.">
    <div style={{
      position: 'relative',
      width: '100vw',
      height: '100vh',
      overflow: 'hidden',
      backgroundColor: 'var(--bg-primary)'
    }}>
      {/* ─── Layer 0: Full-Bleed Map Canvas ─── */}
      <MapContainer />
      
      {/* ─── Layer 50: Status Bar (Top Header) ─── */}
      <StatusBar />
      
      {/* ─── Layer 100: Left Sidebar — Alert Stack ─── */}
      <div className="clay-wrapper" style={{
        top: 'calc(var(--statusbar-height) + 16px)',
        left: '16px',
        bottom: '16px',
        width: 'var(--sidebar-width)',
        zIndex: 50,
      }}>
        <CommandAlertStack />
      </div>
      
      {/* ─── Layer 100: Bottom — Fusion Insights (conditional) ─── */}
      <div className="clay-wrapper" style={{
        bottom: '16px',
        left: 'calc(var(--sidebar-width) + 32px)',
        right: 'calc(var(--toolbar-width) + 16px)',
        zIndex: 100,
      }}>
        <FusionInsightsPanel />
      </div>

      {/* ─── Layer 100: Bottom-Right — VLM Vision PIP ─── */}
      <div className="clay-wrapper" style={{
        bottom: '16px',
        right: 'calc(var(--toolbar-width) + 16px)',
        zIndex: 100,
      }}>
        <VLMVisionCard />
      </div>
      
      {/* ─── Layer 200: Right Toolbar ─── */}
      <RightToolbar />

      {/* ─── Layer 200: Slide-Out Panels (from right) ─── */}
      <div className="clay-wrapper" style={{
        top: 'calc(var(--statusbar-height) + 16px)',
        right: 'calc(var(--toolbar-width) + 8px)',
        bottom: '16px',
        width: '320px',
        zIndex: 150,
        display: 'flex',
        flexDirection: 'column',
      }}>
        {/* Only one slide-out open at a time. Layer panel has lower priority. */}
        <MapControlsSlideOut isOpen={showLayerPanel && !showRoutePanel && !showSimPanel} />
        {showRoutePanel && !showSimPanel && <RouteAnalysisPanel />}
        {showSimPanel && <DisasterInjectorPanel />}
      </div>
    </div>
    </ErrorBoundary>
  );
};
